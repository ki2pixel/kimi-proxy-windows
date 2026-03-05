"""
Client MCP spécialisé pour Fast Filesystem.

Supporte opérations fichiers/arbres/recherche via outils MCP fast-filesystem.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List

from kimi_proxy.core.models import MCPPhase4ServerStatus, FileSystemResult
from ..base.rpc import MCPRPCClient

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..base.config import MCPClientConfig


class FileSystemMCPClient:
    """Client spécialisé Fast Filesystem MCP."""

    VALID_TOOLS: List[str] = [
        "fast_read_file",
        "fast_read_multiple_files",
        "fast_write_file",
        "fast_create_directory",
        "fast_list_directory",
        "fast_move_file",
        "fast_copy_file",
        "fast_delete_file",
        "fast_search_files",
        "fast_search_code",
        "edit_file",
        "fast_safe_edit",
        "fast_list_allowed_directories",
        "fast_get_file_info",
        "fast_get_directory_tree",
        "fast_get_disk_usage",
        "fast_find_large_files",
        "fast_extract_lines",
        "fast_batch_file_operations",
        "fast_compress_files",
        "fast_extract_archive",
        "fast_set_allowed_directories",
        "fast_get_text_file",
        "fast_read_binary_file",
        "fast_delete_directory",
    ]

    def __init__(self, config: "MCPClientConfig", rpc_client: MCPRPCClient):
        self.config = config
        self.rpc_client = rpc_client
        self._status: Optional[MCPPhase4ServerStatus] = None

    async def check_status(self) -> MCPPhase4ServerStatus:
        """Vérifie le statut du serveur Fast Filesystem."""
        try:
            start_time = datetime.now()
            result = await self.rpc_client.make_rpc_call(
                server_url=self.config.fast_filesystem_url,
                method="fast_list_allowed_directories",
                params={},
                timeout_ms=self.config.fast_filesystem_timeout_ms,
                api_key=self.config.fast_filesystem_api_key,
            )
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            connected = isinstance(result, dict)

            self._status = MCPPhase4ServerStatus(
                name="fast-filesystem-mcp",
                type="fast_filesystem",
                url=self.config.fast_filesystem_url,
                connected=connected,
                last_check=datetime.now().isoformat(),
                latency_ms=latency_ms,
                tools_count=len(self.VALID_TOOLS),
                capabilities=["file_operations", "search", "directory_tree"],
            )
            return self._status
        except Exception:
            self._status = MCPPhase4ServerStatus(
                name="fast-filesystem-mcp",
                type="fast_filesystem",
                url=self.config.fast_filesystem_url,
                connected=False,
                last_check=datetime.now().isoformat(),
                error_count=1,
                tools_count=len(self.VALID_TOOLS),
                capabilities=[],
            )
            return self._status

    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> FileSystemResult:
        """Appelle un outil Fast Filesystem."""
        if tool_name not in self.VALID_TOOLS:
            return FileSystemResult(
                success=False,
                operation=tool_name,
                error=f"Outil invalide: {tool_name}",
            )

        result = await self.rpc_client.make_rpc_call(
            self.config.fast_filesystem_url,
            method=tool_name,
            params=params,
            timeout_ms=self.config.fast_filesystem_timeout_ms,
            api_key=self.config.fast_filesystem_api_key,
        )

        if not isinstance(result, dict):
            return FileSystemResult(
                success=False,
                path=str(params.get("path", "")),
                operation=tool_name,
                error="Aucune réponse du serveur",
            )

        return FileSystemResult(
            success=bool(result.get("success", True)),
            path=str(params.get("path", result.get("path", ""))),
            operation=tool_name,
            content=result.get("content") if isinstance(result.get("content"), str) else None,
            error=str(result.get("error")) if result.get("error") else None,
            bytes_affected=int(result.get("bytes_affected", result.get("size", 0)) or 0),
        )

    async def read_file(self, path: str, line_count: Optional[int] = None) -> FileSystemResult:
        params: Dict[str, Any] = {"path": path}
        if line_count is not None:
            params["line_count"] = line_count
        return await self.call_tool("fast_read_file", params)

    async def write_file(self, path: str, content: str, append: bool = False) -> FileSystemResult:
        return await self.call_tool(
            "fast_write_file",
            {
                "path": path,
                "content": content,
                "append": append,
            },
        )

    async def search_code(self, path: str, pattern: str, max_results: int = 100) -> FileSystemResult:
        return await self.call_tool(
            "fast_search_code",
            {
                "path": path,
                "pattern": pattern,
                "max_results": max_results,
            },
        )

    async def list_directory(
        self,
        path: str,
        recursive: bool = False,
        show_hidden: Optional[bool] = None,
    ) -> FileSystemResult:
        params: Dict[str, Any] = {
            "path": path,
            "recursive": recursive,
        }
        if show_hidden is not None:
            params["show_hidden"] = show_hidden
        return await self.call_tool("fast_list_directory", params)

    def is_available(self) -> bool:
        return self._status is not None and self._status.connected
