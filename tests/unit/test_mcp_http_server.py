"""Tests unitaires pour scripts/mcp_http_server.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


def _import_mcp_http_server():
    module_path = Path(__file__).resolve().parents[2] / "scripts" / "mcp_http_server.py"
    spec = importlib.util.spec_from_file_location("scripts.mcp_http_server", module_path)
    assert spec is not None
    assert spec.loader is not None

    if spec.name in sys.modules:
        del sys.modules[spec.name]

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
def test_parse_mcp_disk_roots_semicolon(monkeypatch):
    mcp_http = _import_mcp_http_server()
    roots = mcp_http._parse_mcp_disk_roots("C:\\;D:\\;F:\\;G:\\")
    assert len(roots) == 4


@pytest.mark.unit
def test_resolve_allowed_roots_priority_mcp_disk_roots(monkeypatch, tmp_path):
    mcp_http = _import_mcp_http_server()

    r1 = tmp_path / "r1"
    r2 = tmp_path / "r2"
    r1.mkdir()
    r2.mkdir()

    monkeypatch.setenv("MCP_DISK_ROOTS", f"{r1};{r2}")
    monkeypatch.setenv("MCP_ALLOWED_ROOT", str(tmp_path / "fallback"))
    monkeypatch.setenv("WORKSPACE_PATH", str(tmp_path / "legacy"))

    roots = mcp_http._resolve_allowed_roots()
    assert roots == [r1.resolve(strict=False), r2.resolve(strict=False)]


@pytest.mark.unit
def test_resolve_allowed_roots_fallback_to_mcp_allowed_root(monkeypatch, tmp_path):
    mcp_http = _import_mcp_http_server()

    allowed = tmp_path / "allowed"
    allowed.mkdir()

    monkeypatch.setenv("MCP_DISK_ROOTS", "   ")
    monkeypatch.setenv("MCP_ALLOWED_ROOT", str(allowed))
    monkeypatch.delenv("WORKSPACE_PATH", raising=False)

    roots = mcp_http._resolve_allowed_roots()
    assert roots == [allowed.resolve(strict=False)]


@pytest.mark.unit
def test_is_path_allowed_blocks_traversal(monkeypatch, tmp_path):
    mcp_http = _import_mcp_http_server()

    allowed_root = tmp_path / "allowed"
    outside_root = tmp_path / "outside"
    allowed_root.mkdir()
    outside_root.mkdir()

    traversal = str(allowed_root / ".." / "outside" / "secret.txt")
    allowed, _resolved, reason = mcp_http._is_path_allowed(traversal, [allowed_root.resolve(strict=False)])

    assert allowed is False
    assert reason == "outside_allowed_roots"


@pytest.mark.unit
def test_is_path_allowed_blocks_symlink_escape(monkeypatch, tmp_path):
    mcp_http = _import_mcp_http_server()

    allowed_root = tmp_path / "allowed"
    outside_root = tmp_path / "outside"
    allowed_root.mkdir()
    outside_root.mkdir()
    (outside_root / "secret.txt").write_text("secret", encoding="utf-8")

    link = allowed_root / "escape"
    try:
        link.symlink_to(outside_root, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink non supporté dans cet environnement")

    allowed, _resolved, reason = mcp_http._is_path_allowed(str(link / "secret.txt"), [allowed_root.resolve(strict=False)])
    assert allowed is False
    assert reason == "outside_allowed_roots"


@pytest.mark.unit
def test_fast_read_file_requires_path_argument(tmp_path):
    mcp_http = _import_mcp_http_server()

    class _DummyFastFsHandler:
        def __init__(self, roots: list[Path]) -> None:
            self._roots = roots

        def _allowed_roots(self) -> list[Path]:
            return self._roots

        def _tool_content(self, text: str) -> dict[str, object]:
            return {"content": [{"type": "text", "text": text}]}

    dummy = _DummyFastFsHandler([tmp_path.resolve(strict=False)])

    result = mcp_http.MCPHandler._handle_fast_filesystem(dummy, "req-1", "fast_read_file", {})
    assert isinstance(result, dict)
    assert result.get("error", {}).get("code") == -32602
    assert "path is required" in str(result.get("error", {}).get("message", ""))


@pytest.mark.unit
def test_fast_read_file_requires_existing_file_path(tmp_path):
    mcp_http = _import_mcp_http_server()

    class _DummyFastFsHandler:
        def __init__(self, roots: list[Path]) -> None:
            self._roots = roots

        def _allowed_roots(self) -> list[Path]:
            return self._roots

        def _tool_content(self, text: str) -> dict[str, object]:
            return {"content": [{"type": "text", "text": text}]}

    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    dummy = _DummyFastFsHandler([allowed_root.resolve(strict=False)])

    result = mcp_http.MCPHandler._handle_fast_filesystem(
        dummy,
        "req-2",
        "fast_read_file",
        {"path": str(allowed_root)},
    )
    assert isinstance(result, dict)
    assert result.get("error", {}).get("code") == -32602
    assert "existing file" in str(result.get("error", {}).get("message", ""))


@pytest.mark.unit
def test_fast_list_directory_requires_directory_path(tmp_path):
    mcp_http = _import_mcp_http_server()

    class _DummyFastFsHandler:
        def __init__(self, roots: list[Path]) -> None:
            self._roots = roots

        def _allowed_roots(self) -> list[Path]:
            return self._roots

        def _tool_content(self, text: str) -> dict[str, object]:
            return {"content": [{"type": "text", "text": text}]}

        def _build_tree(self, base: Path, depth: int = 3) -> dict[str, object]:
            return {"name": base.name, "path": str(base), "type": "directory"}

    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    file_path = allowed_root / "file.txt"
    file_path.write_text("hello", encoding="utf-8")

    dummy = _DummyFastFsHandler([allowed_root.resolve(strict=False)])
    result = mcp_http.MCPHandler._handle_fast_filesystem(
        dummy,
        "req-3",
        "fast_list_directory",
        {"path": str(file_path)},
    )
    assert isinstance(result, dict)
    assert result.get("error", {}).get("code") == -32602
    assert "existing directory" in str(result.get("error", {}).get("message", ""))


@pytest.mark.unit
def test_fast_search_files_requires_directory_path(tmp_path):
    mcp_http = _import_mcp_http_server()

    class _DummyFastFsHandler:
        def __init__(self, roots: list[Path]) -> None:
            self._roots = roots

        def _allowed_roots(self) -> list[Path]:
            return self._roots

        def _tool_content(self, text: str) -> dict[str, object]:
            return {"content": [{"type": "text", "text": text}]}

        def _build_tree(self, base: Path, depth: int = 3) -> dict[str, object]:
            return {"name": base.name, "path": str(base), "type": "directory"}

    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    file_path = allowed_root / "file.txt"
    file_path.write_text("hello", encoding="utf-8")

    dummy = _DummyFastFsHandler([allowed_root.resolve(strict=False)])
    result = mcp_http.MCPHandler._handle_fast_filesystem(
        dummy,
        "req-4",
        "fast_search_files",
        {"path": str(file_path), "pattern": "*.txt"},
    )
    assert isinstance(result, dict)
    assert result.get("error", {}).get("code") == -32602
    assert "existing directory" in str(result.get("error", {}).get("message", ""))
