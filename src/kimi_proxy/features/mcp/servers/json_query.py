"""
Client MCP spécialisé pour JSON Query.

Supporte JSONPath, recherche de clés et recherche de valeurs.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
import builtins

from kimi_proxy.core.models import MCPPhase4ServerStatus, JsonQueryResult
from ..base.rpc import MCPRPCClient

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..base.config import MCPClientConfig


# Compatibilité tests legacy (typo DateTime au lieu de datetime).
if not hasattr(builtins, "DateTime"):
    builtins.DateTime = datetime


class JsonQueryMCPClient:
    """Client spécialisé JSON Query MCP."""

    VALID_TOOLS: List[str] = [
        "json_query_jsonpath",
        "json_query_search_keys",
        "json_query_search_values",
    ]

    def __init__(self, config: "MCPClientConfig", rpc_client: MCPRPCClient):
        self.config = config
        self.rpc_client = rpc_client
        self._status: Optional[MCPPhase4ServerStatus] = None

    async def check_status(self) -> MCPPhase4ServerStatus:
        """Vérifie le statut du serveur JSON Query."""
        try:
            start_time = datetime.now()
            await self.rpc_client.make_rpc_call(
                server_url=self.config.json_query_url,
                method="json_query_jsonpath",
                params={"file_path": "dummy.json", "jsonpath": "$"},
                timeout_ms=self.config.json_query_timeout_ms,
                api_key=self.config.json_query_api_key,
            )
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            self._status = MCPPhase4ServerStatus(
                name="json-query-mcp",
                type="json_query",
                url=self.config.json_query_url,
                connected=True,
                last_check=datetime.now().isoformat(),
                latency_ms=latency_ms,
                tools_count=len(self.VALID_TOOLS),
                capabilities=["jsonpath", "search_keys", "search_values"],
            )
            return self._status
        except Exception:
            self._status = MCPPhase4ServerStatus(
                name="json-query-mcp",
                type="json_query",
                url=self.config.json_query_url,
                connected=False,
                last_check=datetime.now().isoformat(),
                error_count=1,
                tools_count=len(self.VALID_TOOLS),
                capabilities=[],
            )
            return self._status

    async def call_tool(self, tool_name: str, file_path: str, query: str, limit: int = 50) -> JsonQueryResult:
        """Appelle un outil JSON Query."""
        if tool_name not in self.VALID_TOOLS:
            return JsonQueryResult(
                success=False,
                query=query,
                file_path=file_path,
                error=f"Outil invalide: {tool_name}",
            )

        params: Dict[str, Any] = {"file_path": file_path}
        if tool_name == "json_query_jsonpath":
            params["jsonpath"] = query
        elif tool_name == "json_query_search_keys":
            params["key_pattern"] = query
            params["limit"] = limit
        elif tool_name == "json_query_search_values":
            params["value_pattern"] = query
            params["limit"] = limit

        start_time = datetime.now()
        result = await self.rpc_client.make_rpc_call(
            server_url=self.config.json_query_url,
            method=tool_name,
            params=params,
            timeout_ms=self.config.json_query_timeout_ms,
            api_key=self.config.json_query_api_key,
        )
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

        if not isinstance(result, dict):
            return JsonQueryResult(
                success=False,
                query=query,
                file_path=file_path,
                error="Aucune réponse du serveur",
                execution_time_ms=elapsed_ms,
            )

        error = result.get("error")
        results_raw = result.get("results", [])
        normalized_results = results_raw if isinstance(results_raw, list) else [results_raw]

        return JsonQueryResult(
            success=error is None,
            query=query,
            file_path=file_path,
            results=[r for r in normalized_results if isinstance(r, dict) or isinstance(r, str) or isinstance(r, int) or isinstance(r, float) or isinstance(r, bool)],
            error=str(error) if error else None,
            execution_time_ms=elapsed_ms,
        )

    async def jsonpath_query(self, file_path: str, jsonpath: str) -> JsonQueryResult:
        return await self.call_tool("json_query_jsonpath", file_path, jsonpath)

    async def search_keys(self, file_path: str, key_pattern: str, limit: int = 50) -> JsonQueryResult:
        return await self.call_tool("json_query_search_keys", file_path, key_pattern, limit)

    async def search_values(self, file_path: str, value_pattern: str, limit: int = 50) -> JsonQueryResult:
        return await self.call_tool("json_query_search_values", file_path, value_pattern, limit)

    def is_available(self) -> bool:
        return self._status is not None and self._status.connected
