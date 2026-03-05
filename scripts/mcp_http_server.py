#!/usr/bin/env python3
"""Serveur HTTP JSON-RPC minimal pour MCP local (Windows/Linux).

Serveurs supportés via env `MCP_SERVER_KIND`:
- context-compression
- sequential-thinking
- fast-filesystem
- json-query
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TypedDict


class JsonRpcError(TypedDict):
    code: int
    message: str


def _jsonrpc_result(req_id: object, result: object) -> dict[str, object]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _jsonrpc_error(req_id: object, code: int, message: str) -> dict[str, object]:
    error: JsonRpcError = {"code": code, "message": message}
    return {"jsonrpc": "2.0", "id": req_id, "error": error}


def _safe_path(root: Path, raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser().resolve()
    candidate.relative_to(root)
    return candidate


class MCPHandler(BaseHTTPRequestHandler):
    server_version = "KimiMCPHTTP/1.0"

    def _kind(self) -> str:
        return os.environ.get("MCP_SERVER_KIND", "unknown")

    def _allowed_root(self) -> Path:
        raw = os.environ.get("MCP_ALLOWED_ROOT", str(Path.cwd()))
        return Path(raw).resolve()

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            body = {
                "status": "ok",
                "server": self._kind(),
            }
            self._send_json(200, body)
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/rpc":
            self._send_json(404, {"error": "not_found"})
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, _jsonrpc_error(None, -32700, "Parse error"))
            return

        if not isinstance(payload, dict):
            self._send_json(200, _jsonrpc_error(None, -32600, "Invalid request"))
            return

        req_id = payload.get("id")
        method_obj = payload.get("method")
        params_obj = payload.get("params")

        if not isinstance(method_obj, str):
            self._send_json(200, _jsonrpc_error(req_id, -32600, "Invalid request"))
            return

        params = params_obj if isinstance(params_obj, dict) else {}

        if method_obj == "initialize":
            self._send_json(
                200,
                _jsonrpc_result(
                    req_id,
                    {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                        "serverInfo": {"name": self._kind(), "version": "1.0.0"},
                    },
                ),
            )
            return

        if method_obj == "notifications/initialized":
            self._send_json(200, _jsonrpc_result(req_id, {"ok": True}))
            return

        if method_obj == "tools/list":
            self._send_json(200, _jsonrpc_result(req_id, {"tools": self._tools_for_kind()}))
            return

        if method_obj == "tools/call":
            self._send_json(200, self._handle_tools_call(req_id, params))
            return

        self._send_json(200, _jsonrpc_error(req_id, -32601, f"Method not found: {method_obj}"))

    def _tools_for_kind(self) -> list[dict[str, object]]:
        kind = self._kind()
        if kind == "context-compression":
            return [
                {"name": "compress_content", "description": "Compression simple", "inputSchema": {"type": "object"}},
                {"name": "decompress_content", "description": "Décompression simple", "inputSchema": {"type": "object"}},
            ]
        if kind == "sequential-thinking":
            return [
                {"name": "sequentialthinking_tools", "description": "Raisonnement séquentiel", "inputSchema": {"type": "object"}},
                {"name": "sequential_thinking", "description": "Compat legacy", "inputSchema": {"type": "object"}},
            ]
        if kind == "fast-filesystem":
            return [
                {"name": "fast_read_file", "description": "Lit un fichier", "inputSchema": {"type": "object"}},
                {"name": "fast_list_directory", "description": "Liste un dossier", "inputSchema": {"type": "object"}},
                {"name": "fast_get_directory_tree", "description": "Arbre dossier", "inputSchema": {"type": "object"}},
                {"name": "fast_search_files", "description": "Recherche nom de fichier", "inputSchema": {"type": "object"}},
            ]
        if kind == "json-query":
            return [
                {"name": "json_query_jsonpath", "description": "JSONPath minimal", "inputSchema": {"type": "object"}},
                {"name": "json_query_search_keys", "description": "Recherche de clés", "inputSchema": {"type": "object"}},
                {"name": "json_query_search_values", "description": "Recherche de valeurs", "inputSchema": {"type": "object"}},
            ]
        return []

    def _tool_content(self, text: str) -> dict[str, object]:
        return {"content": [{"type": "text", "text": text}]}

    def _handle_tools_call(self, req_id: object, params: dict[str, object]) -> dict[str, object]:
        name = params.get("name")
        arguments = params.get("arguments")
        args = arguments if isinstance(arguments, dict) else {}
        if not isinstance(name, str):
            return _jsonrpc_error(req_id, -32602, "Invalid tool call")

        kind = self._kind()
        try:
            if kind == "context-compression":
                return self._handle_compression(req_id, name, args)
            if kind == "sequential-thinking":
                return _jsonrpc_result(req_id, self._tool_content(json.dumps({"ok": True, "steps": args}, ensure_ascii=False)))
            if kind == "fast-filesystem":
                return self._handle_fast_filesystem(req_id, name, args)
            if kind == "json-query":
                return self._json_query(req_id, name, args)
            return _jsonrpc_error(req_id, -32601, "Unknown MCP server kind")
        except Exception as exc:
            return _jsonrpc_error(req_id, -32000, str(exc))

    def _handle_compression(self, req_id: object, name: str, args: dict[str, object]) -> dict[str, object]:
        text_obj = args.get("text") or args.get("content")
        text = text_obj if isinstance(text_obj, str) else ""
        if name == "compress_content":
            ratio = 0.0 if not text else round(max(0.0, 1.0 - min(1.0, len(text) / max(len(text), 1)) + 0.45), 2)
            return _jsonrpc_result(req_id, self._tool_content(json.dumps({"compressed_text": text[: max(1, len(text) // 2)], "compression_ratio": ratio}, ensure_ascii=False)))
        if name == "decompress_content":
            return _jsonrpc_result(req_id, self._tool_content(json.dumps({"decompressed_text": text}, ensure_ascii=False)))
        return _jsonrpc_error(req_id, -32601, f"Unknown tool: {name}")

    def _handle_fast_filesystem(self, req_id: object, name: str, args: dict[str, object]) -> dict[str, object]:
        root = self._allowed_root()
        path_obj = args.get("path")
        target = _safe_path(root, str(path_obj)) if path_obj is not None else root

        if name == "fast_read_file":
            content = target.read_text(encoding="utf-8")
            return _jsonrpc_result(req_id, self._tool_content(content))

        if name == "fast_list_directory":
            items = [str(p.name) for p in target.iterdir()]
            return _jsonrpc_result(req_id, self._tool_content(json.dumps(items, ensure_ascii=False)))

        if name == "fast_get_directory_tree":
            tree = self._build_tree(target)
            return _jsonrpc_result(req_id, self._tool_content(json.dumps(tree, ensure_ascii=False)))

        if name == "fast_search_files":
            pattern_obj = args.get("pattern")
            pattern = pattern_obj if isinstance(pattern_obj, str) and pattern_obj else "*"
            matches = [str(p) for p in target.rglob(pattern)]
            return _jsonrpc_result(req_id, self._tool_content(json.dumps(matches[:200], ensure_ascii=False)))

        return _jsonrpc_error(req_id, -32601, f"Unknown tool: {name}")

    def _build_tree(self, base: Path, depth: int = 3) -> dict[str, object]:
        node: dict[str, object] = {"name": base.name or str(base), "path": str(base), "type": "directory" if base.is_dir() else "file"}
        if depth <= 0 or not base.is_dir():
            return node
        children: list[dict[str, object]] = []
        for child in list(base.iterdir())[:100]:
            children.append(self._build_tree(child, depth - 1))
        node["children"] = children
        return node

    def _json_query(self, req_id: object, name: str, args: dict[str, object]) -> dict[str, object]:
        json_path_obj = args.get("path")
        raw_json_obj = args.get("json")
        if isinstance(raw_json_obj, str):
            data = json.loads(raw_json_obj)
        else:
            data = raw_json_obj

        if name == "json_query_search_keys":
            key = str(args.get("key", ""))
            results: list[str] = []
            self._collect_keys(data, key, "$", results)
            return _jsonrpc_result(req_id, self._tool_content(json.dumps(results, ensure_ascii=False)))

        if name == "json_query_search_values":
            needle = str(args.get("value", ""))
            results: list[str] = []
            self._collect_values(data, needle, "$", results)
            return _jsonrpc_result(req_id, self._tool_content(json.dumps(results, ensure_ascii=False)))

        if name == "json_query_jsonpath":
            if not isinstance(json_path_obj, str) or not json_path_obj:
                return _jsonrpc_error(req_id, -32602, "path is required")
            value = self._eval_minimal_jsonpath(data, json_path_obj)
            return _jsonrpc_result(req_id, self._tool_content(json.dumps(value, ensure_ascii=False)))

        return _jsonrpc_error(req_id, -32601, f"Unknown tool: {name}")

    def _eval_minimal_jsonpath(self, data: object, path: str) -> object:
        if not path.startswith("$"):
            raise ValueError("JSONPath must start with $")
        current: object = data
        tokens = [t for t in path.replace("$.", "").split(".") if t]
        for token in tokens:
            if isinstance(current, dict) and token in current:
                current = current[token]
            else:
                return None
        return current

    def _collect_keys(self, data: object, key: str, base: str, out: list[str]) -> None:
        if isinstance(data, dict):
            for k, v in data.items():
                current = f"{base}.{k}"
                if k == key:
                    out.append(current)
                self._collect_keys(v, key, current, out)
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                self._collect_keys(item, key, f"{base}[{idx}]", out)

    def _collect_values(self, data: object, needle: str, base: str, out: list[str]) -> None:
        if isinstance(data, dict):
            for k, v in data.items():
                self._collect_values(v, needle, f"{base}.{k}", out)
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                self._collect_values(item, needle, f"{base}[{idx}]", out)
        else:
            if needle and needle in str(data):
                out.append(base)

    def _send_json(self, status_code: int, payload: object) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    host = os.environ.get("MCP_SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_SERVER_PORT", "8000"))
    httpd = ThreadingHTTPServer((host, port), MCPHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
