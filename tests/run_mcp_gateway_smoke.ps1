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

$gatewaySmoke = @'
import json
import sys
import httpx

targets = {
    "sequential-thinking": {
        "tool_name": "sequentialthinking_tools",
        "arguments": {"thought": "smoke"},
    },
    "fast-filesystem": {
        "tool_name": "fast_list_directory",
        "arguments": {"path": "C:/Users/kidpixel/Documents/kimi-proxy"},
    },
    "json-query": {
        "tool_name": "json_query_search_values",
        "arguments": {
            "json": "{\"service\":\"kimi-proxy\",\"status\":\"ok\"}",
            "value": "ok",
        },
    },
}

all_ok = True
def rpc(client: httpx.Client, url: str, req_id: int, method: str, params: dict) -> tuple[bool, str]:
    payload = {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": method,
        "params": params,
    }
    try:
        response = client.post(url, json=payload)
    except Exception as exc:
        return False, f"ERROR {exc}"

    if response.status_code != 200:
        return False, f"HTTP {response.status_code}"

    try:
        body = response.json()
    except Exception as exc:
        return False, f"INVALID_JSON {exc}"

    if isinstance(body, dict) and "error" in body:
        return False, f"JSONRPC_ERROR {body['error']}"
    return True, "OK"


with httpx.Client(timeout=5.0) as client:
    for target, tool_cfg in targets.items():
        url = f"http://127.0.0.1:8000/api/mcp-gateway/{target}/rpc"
        init_ok, init_msg = rpc(client, url, 1, "initialize", {})
        print(f"{target}: initialize {init_msg}")
        if not init_ok:
            all_ok = False

        list_ok, list_msg = rpc(client, url, 2, "tools/list", {})
        print(f"{target}: tools/list {list_msg}")
        if not list_ok:
            all_ok = False

        call_ok, call_msg = rpc(
            client,
            url,
            3,
            "tools/call",
            {"name": tool_cfg["tool_name"], "arguments": tool_cfg["arguments"]},
        )
        print(f"{target}: tools/call {call_msg}")
        if not call_ok:
            all_ok = False

sys.exit(0 if all_ok else 1)
'@

Write-Info "Running MCP gateway smoke checks (Windows)"
Push-Location $ProjectDir
try {
    $tempScript = Join-Path $env:TEMP "kimi_proxy_mcp_gateway_smoke.py"
    Set-Content -Path $tempScript -Value $gatewaySmoke -Encoding UTF8

    & $VenvPython $tempScript
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "MCP gateway smoke checks passed"
        exit 0
    }

    Write-Err "MCP gateway smoke checks failed"
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
