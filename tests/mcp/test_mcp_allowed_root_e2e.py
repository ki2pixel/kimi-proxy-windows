"""tests.mcp.test_mcp_allowed_root_e2e

Tests E2E (serveurs réels) pour valider l'extension d'accès workspace.

Pré-requis:
    ./scripts/start-mcp-servers.sh start

Objectif:
    - Autoriser les chemins sous /home/kidpixel via MCP_ALLOWED_ROOT
    - Refuser les chemins hors /home/kidpixel (ex: /etc/passwd)
    - Bloquer les tentatives de path traversal et d'évasion via symlink
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest


def _windows_disk_roots_from_env() -> list[str]:
    raw = os.environ.get("MCP_DISK_ROOTS", "")
    if not raw.strip():
        return []
    separator = ";" if ";" in raw else ","
    roots = [item.strip() for item in raw.split(separator) if item.strip()]
    return roots


def _resolve_allowed_root_for_tests() -> Path:
    disk_roots = _windows_disk_roots_from_env() if os.name == "nt" else []
    if disk_roots:
        return Path(disk_roots[0]).expanduser().resolve(strict=False)

    for env_name in ("MCP_ALLOWED_ROOT", "WORKSPACE_PATH"):
        raw = os.environ.get(env_name, "").strip()
        if raw:
            return Path(raw).expanduser().resolve(strict=False)

    return Path.cwd().resolve(strict=False)


def _pick_forbidden_path(allowed_root: Path) -> Path:
    if os.name == "nt":
        allowed_drive = allowed_root.drive.upper() if allowed_root.drive else ""
        for letter in ["Z", "Y", "X", "W", "V", "U", "T", "S", "R"]:
            candidate_drive = f"{letter}:"
            if candidate_drive != allowed_drive:
                return Path(f"{candidate_drive}\\__mcp_forbidden_test__")
        return Path(r"C:\Windows\System32\drivers\etc\hosts")

    candidate = Path("/etc/passwd")
    try:
        candidate.resolve(strict=False).relative_to(allowed_root)
        return Path("/var/log/messages")
    except ValueError:
        return candidate


def _assert_jsonrpc_denied(status: int, data: dict) -> None:
    assert status == 200
    assert "error" in data
    message = str(data["error"].get("message", ""))
    assert "Access denied" in message


def _is_fast_filesystem_available() -> bool:
    try:
        import httpx

        resp = httpx.get("http://127.0.0.1:8004/health", timeout=2.0)
        return resp.status_code == 200
    except Exception:
        return False


def _is_json_query_available() -> bool:
    try:
        import httpx

        resp = httpx.get("http://127.0.0.1:8005/health", timeout=2.0)
        return resp.status_code == 200
    except Exception:
        return False


async def _post_jsonrpc(url: str, payload: dict) -> "tuple[int, dict]":
    import httpx

    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(url, json=payload)
        data = resp.json()
        return resp.status_code, data


@pytest.mark.e2e
@pytest.mark.filesystem
@pytest.mark.asyncio
@pytest.mark.skipif(not _is_fast_filesystem_available(), reason="Fast Filesystem indisponible")
async def test_fast_filesystem_allows_home_kidpixel_root() -> None:
    allowed_root = _resolve_allowed_root_for_tests()

    status, data = await _post_jsonrpc(
        "http://127.0.0.1:8004/rpc",
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "fast_list_directory",
                "arguments": {"path": str(allowed_root)},
            },
            "id": "allowed-1",
        },
    )

    assert status == 200
    assert "result" in data


@pytest.mark.e2e
@pytest.mark.filesystem
@pytest.mark.asyncio
@pytest.mark.skipif(not _is_fast_filesystem_available(), reason="Fast Filesystem indisponible")
async def test_fast_filesystem_blocks_outside_root() -> None:
    forbidden_path = _pick_forbidden_path(_resolve_allowed_root_for_tests())

    status, data = await _post_jsonrpc(
        "http://127.0.0.1:8004/rpc",
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "fast_read_file",
                "arguments": {"path": str(forbidden_path)},
            },
            "id": "forbidden-1",
        },
    )

    _assert_jsonrpc_denied(status, data)


@pytest.mark.e2e
@pytest.mark.filesystem
@pytest.mark.asyncio
@pytest.mark.skipif(not _is_fast_filesystem_available(), reason="Fast Filesystem indisponible")
async def test_fast_filesystem_blocks_traversal_and_symlink_escape() -> None:
    allowed_root = _resolve_allowed_root_for_tests()
    if os.name == "nt" and allowed_root == allowed_root.anchor:
        pytest.skip("Racine disque complète autorisée: cas traversal non pertinent sur ce setup")

    traversal_target = (
        Path(r"C:\Windows\System32\drivers\etc\hosts")
        if os.name == "nt"
        else Path("/etc/passwd")
    )
    traversal_path = str(allowed_root / ".." / ".." / traversal_target.as_posix().lstrip("/"))

    traversal_status, traversal_data = await _post_jsonrpc(
        "http://127.0.0.1:8004/rpc",
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "fast_read_file",
                "arguments": {"path": traversal_path},
            },
            "id": "trav-1",
        },
    )

    _assert_jsonrpc_denied(traversal_status, traversal_data)

    # Symlink escape
    base_dir = allowed_root / "workspace"
    base_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="mcp_allowed_root_", dir=str(base_dir)))
    try:
        symlink_target = Path(r"C:\Windows") if os.name == "nt" else Path("/etc")
        try:
            (temp_dir / "etc_link").symlink_to(symlink_target)
        except (OSError, NotImplementedError):
            pytest.skip("Création de symlink non disponible sur cet environnement")

        symlink_status, symlink_data = await _post_jsonrpc(
            "http://127.0.0.1:8004/rpc",
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "fast_read_file",
                    "arguments": {"path": str(temp_dir / "etc_link" / "passwd")},
                },
                "id": "sym-1",
            },
        )

        _assert_jsonrpc_denied(symlink_status, symlink_data)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.e2e
@pytest.mark.json_query
@pytest.mark.asyncio
@pytest.mark.skipif(not _is_json_query_available(), reason="JSON Query indisponible")
async def test_json_query_allows_file_path_under_home_kidpixel_and_blocks_outside() -> None:
    allowed_path = str(_resolve_allowed_root_for_tests() / "README.md")

    allowed_status, allowed_data = await _post_jsonrpc(
        "http://127.0.0.1:8005/rpc",
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "json_query_jsonpath",
                "arguments": {"file_path": allowed_path, "json": {"a": 1}, "path": "$.a"},
            },
            "id": "jq-allowed",
        },
    )

    assert allowed_status == 200
    assert "result" in allowed_data

    forbidden_status, forbidden_data = await _post_jsonrpc(
        "http://127.0.0.1:8005/rpc",
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "json_query_jsonpath",
                "arguments": {
                    "file_path": str(_pick_forbidden_path(_resolve_allowed_root_for_tests())),
                    "json": {"a": 1},
                    "path": "$.a",
                },
            },
            "id": "jq-forbidden",
        },
    )

    _assert_jsonrpc_denied(forbidden_status, forbidden_data)


@pytest.mark.e2e
@pytest.mark.filesystem
@pytest.mark.asyncio
@pytest.mark.skipif(os.name != "nt", reason="Test Windows uniquement")
@pytest.mark.skipif(not _is_fast_filesystem_available(), reason="Fast Filesystem indisponible")
async def test_fast_filesystem_windows_multi_disk_roots_from_env() -> None:
    roots = _windows_disk_roots_from_env()
    if not roots:
        pytest.skip("MCP_DISK_ROOTS non défini pour test e2e multi-disques")

    for index, root in enumerate(roots):
        status, data = await _post_jsonrpc(
            "http://127.0.0.1:8004/rpc",
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "fast_list_directory",
                    "arguments": {"path": root},
                },
                "id": f"win-allow-{index}",
            },
        )
        assert status == 200
        assert "result" in data

    upper_roots = {root[:1].upper() for root in roots if len(root) >= 2 and root[1:2] == ":"}
    denied_drive = next((f"{letter}:\\" for letter in ["Z", "Y", "X", "W", "V", "U", "T", "S", "R"] if letter not in upper_roots), None)
    if denied_drive is None:
        pytest.skip("Impossible de déterminer un disque non whitelisté pour le test")

    denied_status, denied_data = await _post_jsonrpc(
        "http://127.0.0.1:8004/rpc",
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "fast_list_directory",
                "arguments": {"path": denied_drive},
            },
            "id": "win-denied-drive",
        },
    )

    _assert_jsonrpc_denied(denied_status, denied_data)
