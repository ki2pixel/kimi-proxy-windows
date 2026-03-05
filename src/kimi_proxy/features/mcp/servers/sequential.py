"""
Client MCP spécialisé pour Sequential Thinking.

Supporte le raisonnement séquentiel multi-étapes et les branches alternatives.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List

from kimi_proxy.core.models import MCPPhase4ServerStatus, SequentialThinkingStep
from ..base.rpc import MCPRPCClient

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..base.config import MCPClientConfig


class SequentialThinkingMCPClient:
    """Client spécialisé Sequential Thinking MCP."""

    VALID_TOOLS: List[str] = ["sequentialthinking"]

    def __init__(self, config: "MCPClientConfig", rpc_client: MCPRPCClient):
        self.config = config
        self.rpc_client = rpc_client
        self._status: Optional[MCPPhase4ServerStatus] = None

    async def check_status(self) -> MCPPhase4ServerStatus:
        """Vérifie le statut du serveur Sequential Thinking."""
        try:
            start_time = datetime.now()
            await self.call_tool("health-check", thought_number=1, total_thoughts=1)
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            self._status = MCPPhase4ServerStatus(
                name="sequential-thinking-mcp",
                type="sequential_thinking",
                url=self.config.sequential_thinking_url,
                connected=True,
                last_check=datetime.now().isoformat(),
                latency_ms=latency_ms,
                tools_count=1,
                capabilities=["sequential_thinking", "problem_solving"],
            )
            return self._status
        except Exception:
            self._status = MCPPhase4ServerStatus(
                name="sequential-thinking-mcp",
                type="sequential_thinking",
                url=self.config.sequential_thinking_url,
                connected=False,
                last_check=datetime.now().isoformat(),
                error_count=1,
                tools_count=1,
                capabilities=[],
            )
            return self._status

    async def call_tool(
        self,
        thought: str,
        thought_number: int = 1,
        total_thoughts: int = 5,
        next_thought_needed: bool = True,
        available_mcp_tools: Optional[List[str]] = None,
    ) -> SequentialThinkingStep:
        """Appelle l'outil sequentialthinking."""
        params: Dict[str, Any] = {
            "thought": thought,
            "thought_number": thought_number,
            "total_thoughts": total_thoughts,
            "next_thought_needed": next_thought_needed,
        }
        if available_mcp_tools is not None:
            params["available_mcp_tools"] = available_mcp_tools

        result = await self.rpc_client.make_rpc_call(
            server_url=self.config.sequential_thinking_url,
            method="sequentialthinking",
            params=params,
            timeout_ms=self.config.sequential_thinking_timeout_ms,
            api_key=self.config.sequential_thinking_api_key,
        )

        if not isinstance(result, dict):
            return SequentialThinkingStep(
                step_number=1,
                thought="Erreur: Aucune réponse du serveur",
                next_thought_needed=False,
                total_thoughts=1,
                branches=[],
            )

        branches = result.get("branches", [])
        return SequentialThinkingStep(
            step_number=int(result.get("thought_number", thought_number)),
            thought=str(result.get("thought", "")),
            next_thought_needed=bool(result.get("next_thought_needed", False)),
            total_thoughts=int(result.get("total_thoughts", total_thoughts)),
            branches=branches if isinstance(branches, list) else [],
        )

    def is_available(self) -> bool:
        return self._status is not None and self._status.connected
