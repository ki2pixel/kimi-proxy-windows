Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$VenvPython = Join-Path $ProjectDir "venv\Scripts\python.exe"

function Write-Info([string]$Message) { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Ok([string]$Message) { Write-Host "[OK]   $Message" -ForegroundColor Green }
function Write-Err([string]$Message) { Write-Host "[ERR]  $Message" -ForegroundColor Red }

if (-not (Test-Path $VenvPython)) {
    Write-Err "Missing virtual environment: $VenvPython"
    exit 1
}

$smokeScript = @'
import json
import os
import queue
import subprocess
import sys
import threading
import time
from datetime import datetime

import httpx

PROJECT_DIR = r"C:/Users/kidpixel/Documents/kimi-proxy"
VENV_PY = r"C:/Users/kidpixel/Documents/kimi-proxy/venv/Scripts/python.exe"
BRIDGE = r"C:/Users/kidpixel/Documents/kimi-proxy/scripts/mcp_bridge.py"


def now() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S.%f %z")


def safe_print(text: str) -> None:
    sanitized = text.encode("ascii", errors="backslashreplace").decode("ascii")
    print(sanitized)


def read_line_with_timeout(proc: subprocess.Popen[str], timeout_s: float) -> str | None:
    output_queue: queue.Queue[str | None] = queue.Queue(maxsize=1)

    def _reader() -> None:
        try:
            line = proc.stdout.readline() if proc.stdout else ""
            output_queue.put(line)
        except Exception:
            output_queue.put(None)

    thread = threading.Thread(target=_reader, daemon=True)
    thread.start()
    try:
        return output_queue.get(timeout=timeout_s)
    except queue.Empty:
        return None


def run_stdio_server(name: str, tool_name: str, arguments: dict[str, object], extra_env: dict[str, str]) -> tuple[bool, list[str]]:
    logs: list[str] = [f"server={name} start={now()}"]
    env = os.environ.copy()
    env.update(extra_env)

    proc = subprocess.Popen(
        [VENV_PY, BRIDGE, name],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=PROJECT_DIR,
        env=env,
    )

    stderr_lines: list[str] = []

    def _drain_stderr() -> None:
        try:
            if proc.stderr is None:
                return
            for line in proc.stderr:
                stderr_lines.append(line)
                if len(stderr_lines) > 300:
                    del stderr_lines[:100]
        except Exception:
            return

    stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
    stderr_thread.start()

    def send(req: dict[str, object], timeout_s: float = 5.0) -> tuple[bool, str]:
        try:
            assert proc.stdin is not None
            proc.stdin.write(json.dumps(req, ensure_ascii=False) + "\n")
            proc.stdin.flush()
        except Exception as exc:
            return False, f"write_error={exc}"

        line = read_line_with_timeout(proc, timeout_s)
        if line is None:
            return False, "timeout_waiting_response"
        line = line.strip()
        if not line:
            return False, "empty_response"
        try:
            body = json.loads(line)
        except Exception as exc:
            return False, f"invalid_json={exc} raw={line[:180]}"
        if isinstance(body, dict) and "error" in body:
            return False, f"jsonrpc_error={body['error']}"
        return True, "ok"

    checks = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "cline-smoke", "version": "1.0"},
            },
        },
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        },
    ]

    ok = True
    for req in checks:
        status, details = send(req)
        logs.append(f"{name} {req['method']} => {details}")
        if not status:
            ok = False
            break

    try:
        if proc.stdin:
            proc.stdin.close()
    except Exception:
        pass

    time.sleep(0.3)
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

    stderr_tail = "".join(stderr_lines)[-400:]

    logs.append(f"server={name} exit={proc.returncode}")
    if stderr_tail:
        logs.append(f"server={name} stderr_tail={stderr_tail.replace(chr(10), ' | ')}")
    logs.append(f"server={name} end={now()}")
    return ok, logs


def run_http_server(name: str, tool_name: str, arguments: dict[str, object]) -> tuple[bool, list[str]]:
    logs: list[str] = [f"server={name} start={now()}"]
    url = f"http://127.0.0.1:8000/api/mcp-gateway/{name}/rpc"

    def rpc(client: httpx.Client, req_id: int, method: str, params: dict[str, object]) -> tuple[bool, str]:
        payload = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
        try:
            response = client.post(url, json=payload)
        except Exception as exc:
            return False, f"http_error={exc}"
        if response.status_code != 200:
            return False, f"status={response.status_code}"
        try:
            body = response.json()
        except Exception as exc:
            return False, f"invalid_json={exc}"
        if isinstance(body, dict) and "error" in body:
            return False, f"jsonrpc_error={body['error']}"
        return True, "ok"

    ok = True
    with httpx.Client(timeout=8.0) as client:
        for req_id, method, params in [
            (
                1,
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "cline-smoke", "version": "1.0"},
                },
            ),
            (2, "tools/list", {}),
            (3, "tools/call", {"name": tool_name, "arguments": arguments}),
        ]:
            status, details = rpc(client, req_id, method, params)
            logs.append(f"{name} {method} => {details}")
            if not status:
                ok = False
                break

    logs.append(f"server={name} end={now()}")
    return ok, logs


stdio_targets = [
    (
        "filesystem-agent",
        "list_allowed_directories",
        {},
        {
            "MCP_FILESYSTEM_ALLOWED_ROOT": PROJECT_DIR,
            "MCP_FILESYSTEM_COMMAND": r"C:/Users/kidpixel/AppData/Roaming/npm/mcp-server-filesystem.cmd",
            "MCP_BRIDGE_MONITORING_ENABLED": "1",
            "MCP_BRIDGE_MONITORING_LOG_PATH": r"C:/Users/kidpixel/AppData/Local/Temp/kimi-proxy/mcp-bridge-filesystem.jsonl",
        },
    ),
    (
        "ripgrep-agent",
        "search",
        {"path": PROJECT_DIR, "pattern": "README", "maxResults": 5},
        {
            "MCP_RIPGREP_COMMAND": r"C:/Users/kidpixel/AppData/Roaming/npm/mcp-ripgrep.cmd",
            "MCP_BRIDGE_STDIO_STREAM_LIMIT": "8388608",
            "MCP_BRIDGE_MONITORING_ENABLED": "1",
            "MCP_BRIDGE_MONITORING_LOG_PATH": r"C:/Users/kidpixel/AppData/Local/Temp/kimi-proxy/mcp-bridge-ripgrep.jsonl",
        },
    ),
    (
        "shrimp-task-manager",
        "list_tasks",
        {},
        {
            "MCP_SHRIMP_TASK_MANAGER_COMMAND": r"C:/Users/kidpixel/Documents/kimi-proxy/scripts/mcp_shrimp_task_manager.cmd",
            "DATA_DIR": r"C:/Users/kidpixel/Documents/kimi-proxy/shrimp_data",
            "MCP_BRIDGE_MONITORING_ENABLED": "1",
            "MCP_BRIDGE_MONITORING_LOG_PATH": r"C:/Users/kidpixel/AppData/Local/Temp/kimi-proxy/mcp-bridge-shrimp.jsonl",
        },
    ),
]

http_targets = [
    ("sequential-thinking", "sequentialthinking_tools", {"thought": "smoke"}),
    ("fast-filesystem", "fast_list_directory", {"path": PROJECT_DIR}),
    (
        "json-query",
        "json_query_search_values",
        {"json": "{\"service\":\"kimi-proxy\",\"status\":\"ok\"}", "value": "ok"},
    ),
]

all_ok = True
print(f"Test-ID: CLINE-SMOKE-01")
print(f"Start: {now()}")

for name, tool_name, args, env in stdio_targets:
    ok, logs = run_stdio_server(name, tool_name, args, env)
    for line in logs:
        safe_print(line)
    all_ok = all_ok and ok

for name, tool_name, args in http_targets:
    ok, logs = run_http_server(name, tool_name, args)
    for line in logs:
        safe_print(line)
    all_ok = all_ok and ok

print(f"End: {now()}")
sys.exit(0 if all_ok else 1)
'@

Write-Info "Running Cline-focused MCP smoke checks (stdio + HTTP)"
Push-Location $ProjectDir
try {
    $tempScript = Join-Path $env:TEMP "kimi_proxy_cline_mcp_smoke.py"
    Set-Content -Path $tempScript -Value $smokeScript -Encoding UTF8

    & $VenvPython $tempScript
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Cline-focused MCP smoke checks passed"
        exit 0
    }

    Write-Err "Cline-focused MCP smoke checks failed"
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
