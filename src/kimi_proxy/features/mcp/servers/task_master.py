"""
Client MCP spécialisé pour Task Master (Shrimp Task Manager).

Supporte les workflows de gestion de tâches (PRD, expansion, statuts).
"""
from datetime import datetime
from typing import Optional, Dict, Any, List

from kimi_proxy.core.models import (
    MCPPhase4ServerStatus,
    ShrimpTaskMasterTask,
    ShrimpTaskMasterStats,
)
from ..base.rpc import MCPRPCClient

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..base.config import MCPClientConfig


class TaskMasterMCPClient:
    """Client spécialisé Task Master MCP."""

    VALID_TOOLS: List[str] = [
        "get_tasks",
        "get_task",
        "get_next_task",
        "set_task_status",
        "parse_prd",
        "expand_task",
        "expand_all",
        "analyze_project_complexity",
        "initialize_project",
        "add_task",
        "update_task",
        "remove_task",
        "add_subtask",
        "remove_subtask",
    ]

    def __init__(self, config: "MCPClientConfig", rpc_client: MCPRPCClient):
        self.config = config
        self.rpc_client = rpc_client
        self._status: Optional[MCPPhase4ServerStatus] = None

    async def check_status(self) -> MCPPhase4ServerStatus:
        """Vérifie le statut du serveur Task Master."""
        try:
            start_time = datetime.now()
            await self.rpc_client.make_rpc_call(
                server_url=self.config.task_master_url,
                method="get_tasks",
                params={"limit": 1},
                timeout_ms=self.config.task_master_timeout_ms,
                api_key=self.config.task_master_api_key,
            )
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            self._status = MCPPhase4ServerStatus(
                name="task-master-mcp",
                type="task_master",
                url=self.config.task_master_url,
                connected=True,
                last_check=datetime.now().isoformat(),
                latency_ms=latency_ms,
                tools_count=len(self.VALID_TOOLS),
                capabilities=["task_management", "workflow", "prd_parsing"],
            )
            return self._status
        except Exception:
            self._status = MCPPhase4ServerStatus(
                name="task-master-mcp",
                type="task_master",
                url=self.config.task_master_url,
                connected=False,
                last_check=datetime.now().isoformat(),
                error_count=1,
                tools_count=len(self.VALID_TOOLS),
                capabilities=[],
            )
            return self._status

    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Appelle un outil Task Master."""
        if tool_name not in self.VALID_TOOLS:
            return {
                "error": f"Outil invalide: {tool_name}",
                "valid_tools": self.VALID_TOOLS,
            }

        result = await self.rpc_client.make_rpc_call(
            self.config.task_master_url,
            method=tool_name,
            params=params,
            timeout_ms=self.config.task_master_timeout_ms,
            api_key=self.config.task_master_api_key,
        )
        return result if isinstance(result, dict) else {}

    async def get_tasks(self, status_filter: Optional[str] = None) -> List[ShrimpTaskMasterTask]:
        params: Dict[str, Any] = {}
        if status_filter:
            params["status"] = status_filter

        result = await self.call_tool("get_tasks", params)
        tasks_data = result.get("tasks") if isinstance(result, dict) else None
        if not isinstance(tasks_data, list):
            return []

        return [
            ShrimpTaskMasterTask(
                id=task.get("id", ""),
                title=str(task.get("title", "")),
                description=str(task.get("description", "")),
                status=str(task.get("status", "pending")),
                priority=str(task.get("priority", "medium")),
                dependencies=task.get("dependencies", []) if isinstance(task.get("dependencies", []), list) else [],
                subtasks=task.get("subtasks", []) if isinstance(task.get("subtasks", []), list) else [],
            )
            for task in tasks_data
            if isinstance(task, dict)
        ]

    async def get_next_task(self) -> Optional[ShrimpTaskMasterTask]:
        result = await self.call_tool("get_next_task", {})
        task = result.get("task") if isinstance(result, dict) else None
        if not isinstance(task, dict):
            return None
        return ShrimpTaskMasterTask(
            id=task.get("id", ""),
            title=str(task.get("title", "")),
            description=str(task.get("description", "")),
            status=str(task.get("status", "pending")),
            priority=str(task.get("priority", "medium")),
            dependencies=task.get("dependencies", []) if isinstance(task.get("dependencies", []), list) else [],
            subtasks=task.get("subtasks", []) if isinstance(task.get("subtasks", []), list) else [],
        )

    async def get_stats(self) -> ShrimpTaskMasterStats:
        tasks = await self.get_tasks()
        stats = ShrimpTaskMasterStats(total_tasks=len(tasks))
        for task in tasks:
            if task.status == "pending":
                stats.pending += 1
            elif task.status == "in-progress":
                stats.in_progress += 1
            elif task.status == "done":
                stats.done += 1
            elif task.status == "blocked":
                stats.blocked += 1
            elif task.status == "deferred":
                stats.deferred += 1
        return stats

    async def parse_prd(
        self,
        input_file: str,
        research_enabled: bool = False,
        num_tasks: int = 10,
    ) -> Dict[str, Any]:
        return await self.call_tool(
            "parse_prd",
            {
                "input": input_file,
                "research": research_enabled,
                "numTasks": num_tasks,
            },
        )

    async def expand_task(
        self,
        task_id: int,
        num_subtasks: int = 5,
        prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "id": task_id,
            "num": str(num_subtasks),
        }
        if prompt:
            params["prompt"] = prompt
        return await self.call_tool("expand_task", params)

    async def initialize_project(self, project_root: str, init_git: bool = True) -> Dict[str, Any]:
        return await self.call_tool(
            "initialize_project",
            {
                "projectRoot": project_root,
                "initGit": init_git,
            },
        )

    async def set_task_status(self, task_id: int, status: str, subtask_id: Optional[str] = None) -> Dict[str, Any]:
        task_ref = f"{task_id}" if not subtask_id else f"{task_id},{subtask_id}"
        return await self.call_tool(
            "set_task_status",
            {
                "id": task_ref,
                "status": status,
            },
        )

    def is_available(self) -> bool:
        return self._status is not None and self._status.connected
