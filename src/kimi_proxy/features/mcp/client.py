"""Facade MCP avec délégation vers les clients spécialisés."""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import time

from kimi_proxy.core.models import (
    QdrantSearchResult,
    MCPCluster,
    MCPCompressionResult,
    MCPExternalServerStatus,
    MCPPhase4ServerStatus,
    ShrimpTaskMasterTask,
    ShrimpTaskMasterStats,
    SequentialThinkingStep,
    FileSystemResult,
    JsonQueryResult,
    MCPToolCall,
)
from kimi_proxy.core.tokens import count_tokens_text
from kimi_proxy.core.constants import MCP_MAX_RESPONSE_TOKENS, MCP_CHUNK_OVERLAP_TOKENS
from .base.config import MCPClientConfig
from .base.rpc import MCPRPCClient, MCPClientError, MCPConnectionError, MCPTimeoutError
from .servers import (
    QdrantMCPClient,
    CompressionMCPClient,
    TaskMasterMCPClient,
    SequentialThinkingMCPClient,
    FileSystemMCPClient,
    JsonQueryMCPClient,
)


def chunk_large_response(content: str, max_tokens_per_chunk: int = MCP_MAX_RESPONSE_TOKENS, overlap_tokens: int = MCP_CHUNK_OVERLAP_TOKENS) -> List[str]:
    if not content:
        return [""]
    
    total_tokens = count_tokens_text(content)

    if total_tokens <= max_tokens_per_chunk:
        return [content]
    
    print(f"[MCP CHUNKING] Reponse de {total_tokens:,} tokens > {max_tokens_per_chunk:,} limite, chunking...")
    
    chunks = []
    start_idx = 0
    
    while start_idx < len(content):
        chunk_end_idx = _find_chunk_boundary(content, start_idx, max_tokens_per_chunk)

        if chunk_end_idx <= start_idx:
            chunk = content[start_idx:]
            if chunk:
                chunks.append(chunk)
            break

        chunk = content[start_idx:chunk_end_idx]
        chunks.append(chunk)

        overlap_start = max(start_idx, chunk_end_idx - overlap_tokens * 4)
        next_start = _find_word_boundary(content, overlap_start)

        if next_start <= start_idx:
            start_idx = chunk_end_idx
        else:
            start_idx = next_start
    
    print(f"[MCP CHUNKING] Produit {len(chunks)} chunks")
    return chunks


def _find_chunk_boundary(text: str, start_idx: int, max_tokens: int) -> int:
    current_tokens = 0
    current_idx = start_idx

    while current_idx < len(text) and current_tokens < max_tokens:
        word_start = current_idx
        while current_idx < len(text) and text[current_idx].isspace():
            current_idx += 1

        word_end = current_idx
        while word_end < len(text) and not text[word_end].isspace():
            word_end += 1

        if word_start < word_end:
            word = text[word_start:word_end]
            word_tokens = count_tokens_text(word)

            if current_tokens + word_tokens > max_tokens:
                return word_start

            current_tokens += word_tokens
            current_idx = word_end

    return current_idx


def _find_word_boundary(text: str, start_idx: int) -> int:
    idx = start_idx

    while idx < len(text) and text[idx].isspace():
        idx += 1

    if idx == 0 or text[idx-1].isspace():
        return idx

    while idx > 0 and not text[idx-1].isspace():
        idx -= 1

    return idx


def should_chunk_response(result: Dict[str, Any], tool_name: str) -> bool:
    large_response_tools = {
        "fast_get_directory_tree",
        "fast_search_code", 
        "fast_search_files",
        "fast_read_file",
        "fast_read_multiple_files",
        "fast_list_directory",
        "fast_find_large_files"
    }
    if tool_name not in large_response_tools:
        return False

    content = ""
    if isinstance(result, dict):
        content = str(result.get("content", ""))
    else:
        content = str(result)
    
    total_tokens = count_tokens_text(content)
    return total_tokens > MCP_MAX_RESPONSE_TOKENS


class MCPExternalClient:
    """Facade pour tous les serveurs MCP externes."""
    
    def __init__(self, config: Optional[MCPClientConfig] = None):
        self.config = config or MCPClientConfig()
        self._rpc_client = MCPRPCClient(
            max_retries=self.config.max_retries,
            retry_delay_ms=self.config.retry_delay_ms
        )
        
        self.qdrant = QdrantMCPClient(self.config, self._rpc_client)
        self.compression = CompressionMCPClient(self.config, self._rpc_client)
        self.task_master = TaskMasterMCPClient(self.config, self._rpc_client)
        self.sequential = SequentialThinkingMCPClient(self.config, self._rpc_client)
        self.filesystem = FileSystemMCPClient(self.config, self._rpc_client)
        self.json_query = JsonQueryMCPClient(self.config, self._rpc_client)
        
        self._status_cache: Dict[str, MCPExternalServerStatus] = {}
        self._chunk_cache: Dict[str, Dict[str, Any]] = {}
        self._tool_cache: Dict[str, Dict[str, Any]] = {}
    
    async def close(self):
        await self._rpc_client.aclose()
    
    def _store_remaining_chunks(
        self,
        server_type: str,
        tool_name: str,
        params: Dict[str, Any],
        remaining_chunks: List[str],
        original_result: Dict[str, Any],
        execution_time_ms: float
    ) -> str:
        import hashlib
        key_data = f"{server_type}:{tool_name}:{str(params)}:{datetime.now().isoformat()}"
        cache_key = hashlib.md5(key_data.encode()).hexdigest()[:16]
        self._chunk_cache[cache_key] = {
            "server_type": server_type,
            "tool_name": tool_name,
            "params": params,
            "remaining_chunks": remaining_chunks,
            "original_result": original_result,
            "execution_time_ms": execution_time_ms,
            "created_at": datetime.now().isoformat(),
            "total_chunks": len(remaining_chunks) + 1
        }
        print(f"[MCP CHUNK CACHE] Stocke {len(remaining_chunks)} chunks sous cle {cache_key}")
        return cache_key
    
    async def get_next_chunk(self, cache_key: str, chunk_number: int) -> Optional[MCPToolCall]:
        if cache_key not in self._chunk_cache:
            return None
        cache_entry = self._chunk_cache[cache_key]
        remaining_chunks = cache_entry["remaining_chunks"]
        chunk_index = chunk_number - 1
        if chunk_index < 0 or chunk_index >= len(remaining_chunks):
            return None
        chunked_result = cache_entry["original_result"].copy()
        chunked_result["chunked"] = True
        chunked_result["total_chunks"] = cache_entry["total_chunks"]
        chunked_result["current_chunk"] = chunk_number
        chunked_result["content"] = remaining_chunks[chunk_index]
        chunked_result["cache_key"] = cache_key
        if chunk_index == len(remaining_chunks) - 1:
            del self._chunk_cache[cache_key]
            print(f"[MCP CHUNK CACHE] Nettoie cache pour {cache_key}")
        
        return MCPToolCall(
            server_type=cache_entry["server_type"],
            tool_name=cache_entry["tool_name"],
            params=cache_entry["params"],
            status="success",
            result=chunked_result,
            execution_time_ms=cache_entry["execution_time_ms"]
        )
    
    def _get_tool_cache_key(self, server_type: str, tool_name: str, params: Dict[str, Any]) -> str:
        import hashlib
        key_data = f"{server_type}:{tool_name}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    def _should_cache_tool_result(self, tool_name: str, result: Dict[str, Any]) -> bool:
        cacheable_tools = {
            "fast_read_file",
            "fast_list_directory", 
            "fast_get_file_info",
            "fast_search_code",
            "fast_search_files",
            "json_query_jsonpath",
            "json_query_search_keys"
        }
        if tool_name not in cacheable_tools:
            return False
        content = ""
        if isinstance(result, dict) and "content" in result:
            content = str(result.get("content", ""))
        else:
            content = str(result)
        return len(content) > 1000
    
    async def _compress_large_response(self, content: str) -> str:
        if len(content) < 5000:
            return content
        try:
            if self.is_compression_available():
                compressed_result = await self.compress_content(
                    content, 
                    algorithm="context_aware", 
                    target_ratio=0.7
                )
                if compressed_result.success and compressed_result.compressed_content:
                    print(f"[COMPRESSION] Contenu compresse: {len(content)} -> {len(compressed_result.compressed_content)} chars")
                    return f"[COMPRESSED CONTENT - {compressed_result.compression_ratio:.1%} saved]\n{compressed_result.compressed_content}"
        except Exception as e:
            print(f"[COMPRESSION] Erreur lors de la compression: {e}")
        if len(content) > 10000:
            truncated = content[:8000] + f"\n\n[... CONTENU TRONQUÉ - {len(content) - 8000} caractères supprimés ...]"
            print(f"[TRUNCATION] Contenu tronque: {len(content)} -> {len(truncated)} chars")
            return truncated
        return content
    
    async def _get_cached_tool_result(self, server_type: str, tool_name: str, params: Dict[str, Any]) -> Optional[MCPToolCall]:
        cache_key = self._get_tool_cache_key(server_type, tool_name, params)
        if cache_key in self._tool_cache:
            cached_entry = self._tool_cache[cache_key]
            import time
            if time.time() - cached_entry["cached_at"] < 300:
                print(f"[TOOL CACHE] Hit pour {tool_name}: {cache_key}")
                return MCPToolCall(
                    server_type=server_type,
                    tool_name=tool_name,
                    params=params,
                    status="success",
                    result=cached_entry["result"],
                    execution_time_ms=cached_entry["execution_time_ms"]
                )
            else:
                del self._tool_cache[cache_key]
        return None
    
    def _cache_tool_result(self, server_type: str, tool_name: str, params: Dict[str, Any], result: Dict[str, Any], execution_time_ms: float):
        if not self._should_cache_tool_result(tool_name, result):
            return
        cache_key = self._get_tool_cache_key(server_type, tool_name, params)
        self._tool_cache[cache_key] = {
            "server_type": server_type,
            "tool_name": tool_name,
            "params": params,
            "result": result,
            "execution_time_ms": execution_time_ms,
            "cached_at": time.time()
        }
        print(f"[TOOL CACHE] Stored {tool_name}: {cache_key} ({len(str(result))} chars)")
    
    # ========================================================================
    # Qdrant - Recherche sémantique
    # ========================================================================
    
    async def check_qdrant_status(self) -> MCPExternalServerStatus:
        """Vérifie le statut du serveur Qdrant MCP."""  
        status = await self.qdrant.check_status()
        self._status_cache["qdrant"] = status
        return status
    
    async def search_similar(self, query: str, limit: int = 5, score_threshold: float = 0.7) -> List[QdrantSearchResult]:
        """Recherche sémantique via Qdrant MCP."""
        return await self.qdrant.search_similar(query, limit, score_threshold)
    
    async def store_memory_vector(self, content: str, memory_type: str = "episodic", metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Stocke un vecteur mémoire dans Qdrant."""
        return await self.qdrant.store_vector(content, memory_type, metadata)
    
    async def find_redundant_memories(self, content: str, similarity_threshold: float = 0.85) -> List[str]:
        """Détecte les mémoires redondantes."""
        return await self.qdrant.find_redundant(content, similarity_threshold)
    
    async def cluster_memories(self, session_id: int, min_cluster_size: int = 3) -> List[MCPCluster]:
        """Clusterise les mémoires d'une session."""
        return await self.qdrant.cluster_memories(session_id, min_cluster_size)
    
    # ========================================================================
    # Compression - Compression contextuelle
    # ========================================================================
    
    async def check_compression_status(self) -> MCPExternalServerStatus:
        """Vérifie le statut du serveur Context Compression MCP."""
        status = await self.compression.check_status()
        self._status_cache["compression"] = status
        return status

    async def check_task_master_status(self) -> bool:
        status = await self.task_master.check_status()
        self._status_cache["task_master"] = status
        return bool(status.connected)

    async def check_sequential_thinking_status(self) -> bool:
        status = await self.sequential.check_status()
        self._status_cache["sequential_thinking"] = status
        return bool(status.connected)

    async def check_fast_filesystem_status(self) -> bool:
        status = await self.filesystem.check_status()
        self._status_cache["fast_filesystem"] = status
        return bool(status.connected)

    async def check_json_query_status(self) -> bool:
        status = await self.json_query.check_status()
        self._status_cache["json_query"] = status
        return bool(status.connected)
    
    async def compress_content(self, content: str, algorithm: str = "context_aware", target_ratio: float = 0.5) -> MCPCompressionResult:
        """Compresse du contenu via Context Compression MCP."""
        return await self.compression.compress(content, algorithm, target_ratio)
    
    async def decompress_content(self, compressed_data: str, algorithm: str = "zlib") -> str:
        """Décompresse du contenu."""
        return await self.compression.decompress(compressed_data, algorithm)
    
    async def get_all_server_statuses(self) -> List[MCPExternalServerStatus]:
        """Récupère le statut de tous les serveurs MCP externes."""
        statuses = []
        statuses.append(await self.qdrant.check_status())
        statuses.append(await self.compression.check_status())
        return statuses

    async def get_all_phase4_server_statuses(self) -> List[MCPPhase4ServerStatus]:
        """Récupère les statuts des serveurs Phase 4 (et rafraîchit aussi Phase 3)."""
        # Rafraîchissement global (utilisé par les tests d'isolation)
        await self.qdrant.check_status()
        await self.compression.check_status()

        task_master_status = await self.task_master.check_status()
        sequential_status = await self.sequential.check_status()
        filesystem_status = await self.filesystem.check_status()
        json_query_status = await self.json_query.check_status()

        return [
            task_master_status,
            sequential_status,
            filesystem_status,
            json_query_status,
        ]
    
    # ========================================================================
    # Disponibilité rapide (cache)
    # ========================================================================
    
    def is_qdrant_available(self) -> bool:
        """Vérifie si Qdrant est disponible."""
        return self.qdrant.is_available()
    
    def is_compression_available(self) -> bool:
        """Vérifie si le serveur de compression est disponible."""
        return self.compression.is_available()

    def is_task_master_available(self) -> bool:
        """Vérifie si le serveur Task Master est disponible."""
        return self.task_master.is_available()

    def is_sequential_available(self) -> bool:
        """Vérifie si le serveur Sequential Thinking est disponible."""
        return self.sequential.is_available()

    def is_filesystem_available(self) -> bool:
        """Vérifie si le serveur Fast Filesystem est disponible."""
        return self.filesystem.is_available()

    def is_json_query_available(self) -> bool:
        """Vérifie si le serveur JSON Query est disponible."""
        return self.json_query.is_available()

    # ========================================================================
    # Phase 4 - Délégations explicites
    # ========================================================================

    async def call_task_master_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Délègue un appel d'outil Task Master."""
        return await self.task_master.call_tool(tool_name, params)

    async def call_sequential_thinking(
        self,
        thought: str,
        thought_number: int = 1,
        total_thoughts: int = 5,
        next_thought_needed: bool = True,
        available_mcp_tools: Optional[List[str]] = None,
    ) -> SequentialThinkingStep:
        """Délègue un appel Sequential Thinking."""
        return await self.sequential.call_tool(
            thought=thought,
            thought_number=thought_number,
            total_thoughts=total_thoughts,
            next_thought_needed=next_thought_needed,
            available_mcp_tools=available_mcp_tools,
        )

    async def call_fast_filesystem_tool(self, tool_name: str, params: Dict[str, Any]) -> FileSystemResult:
        """Délègue un appel d'outil Fast Filesystem."""
        return await self.filesystem.call_tool(tool_name, params)

    async def call_json_query_tool(
        self,
        tool_name: str,
        file_path: str,
        query: str,
        limit: int = 50,
    ) -> JsonQueryResult:
        """Délègue un appel d'outil JSON Query."""
        return await self.json_query.call_tool(tool_name, file_path, query, limit)

    # Helpers Fast Filesystem
    async def fast_read_file(self, path: str, line_count: Optional[int] = None) -> FileSystemResult:
        return await self.filesystem.read_file(path, line_count)

    async def fast_write_file(self, path: str, content: str, append: bool = False) -> FileSystemResult:
        return await self.filesystem.write_file(path, content, append)

    async def fast_search_code(self, path: str, pattern: str, max_results: int = 100) -> FileSystemResult:
        return await self.filesystem.search_code(path, pattern, max_results)

    async def fast_list_directory(
        self,
        path: str,
        recursive: bool = False,
        show_hidden: Optional[bool] = None,
    ) -> FileSystemResult:
        return await self.filesystem.list_directory(path, recursive, show_hidden)

    # Helpers JSON Query
    async def jsonpath_query(self, file_path: str, jsonpath: str) -> JsonQueryResult:
        return await self.json_query.jsonpath_query(file_path, jsonpath)

    async def search_json_keys(self, file_path: str, key_pattern: str, limit: int = 50) -> JsonQueryResult:
        return await self.json_query.search_keys(file_path, key_pattern, limit)

    async def search_json_values(self, file_path: str, value_pattern: str, limit: int = 50) -> JsonQueryResult:
        return await self.json_query.search_values(file_path, value_pattern, limit)
    
    # ========================================================================
    # API générique (compatibilité ascendante)
    # ========================================================================
    
    async def call_mcp_tool(
        self,
        server_type: str,
        tool_name: str,
        params: Dict[str, Any]
    ) -> MCPToolCall:
        """
        Appelle un outil MCP de manière générique (compatibilité ascendante).
        
        Args:
            server_type: Type de serveur
            tool_name: Nom de l'outil
            params: Paramètres de l'outil
            
        Returns:
            Résultat de l'appel
        """
        start_time = datetime.now()
        
        try:
            # Vérifie le cache d'abord
            cached_result = await self._get_cached_tool_result(server_type, tool_name, params)
            if cached_result:
                return cached_result
            
            # Type de serveur inconnu
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            return MCPToolCall(
                server_type=server_type,
                tool_name=tool_name,
                params=params,
                status="error",
                result={"error": f"Type de serveur inconnu: {server_type}"},
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            print(f" [MCP TOOL] Erreur lors de l'appel {server_type}.{tool_name}: {e}")
            
            return MCPToolCall(
                server_type=server_type,
                tool_name=tool_name,
                params=params,
                status="error",
                result={"error": str(e), "server_type": server_type, "tool_name": tool_name},
                execution_time_ms=execution_time_ms
            )


# Singleton global (préservé pour compatibilité ascendante avec les 15+ routes API)
_mcp_client: Optional[MCPExternalClient] = None


def get_mcp_client(config: Optional[MCPClientConfig] = None) -> MCPExternalClient:
    """
    Récupère le client MCP global avec config chargée depuis config.toml.
    
    Args:
        config: Configuration MCP (optionnel)
        
    Returns:
        Instance singleton de MCPExternalClient
    """
    global _mcp_client
    if _mcp_client is None:
        if config is None:
            # Charge la config depuis config.toml
            try:
                from kimi_proxy.config.loader import get_config
                toml_config = get_config()
                config = MCPClientConfig.from_toml(toml_config)
            except Exception:
                # Fallback: config par défaut
                config = MCPClientConfig()
        
        _mcp_client = MCPExternalClient(config)
    return _mcp_client


def reset_mcp_client():
    """Réinitialise le client MCP global (pour tests)."""
    global _mcp_client
    _mcp_client = None
