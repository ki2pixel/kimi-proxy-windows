"""
Tests pour MCP Phase 3 - Optimisations Avancées.

Couverture:
- Client MCP externe (Qdrant, Compression)
- Mémoire standardisée (frequent/episodic)
- Routage provider optimisé
- API endpoints Phase 3
"""
import pytest
from unittest.mock import Mock, patch

from kimi_proxy.features.mcp.client import (
    MCPExternalClient,
    MCPClientConfig,
    reset_mcp_client
)
from kimi_proxy.features.mcp.memory import (
    MemoryManager,
    reset_memory_manager
)
from kimi_proxy.core.models import (
    MCPMemoryEntry,
    MCPCompressionResult,
    QdrantSearchResult,
    ProviderRoutingDecision
)


# ============================================================================
# Tests Client MCP Externe
# ============================================================================

class TestMCPExternalClient:
    """Tests du client MCP externe."""
    
    @pytest.fixture
    def client(self):
        """Fixture client MCP."""
        reset_mcp_client()
        config = MCPClientConfig(
            qdrant_url="http://localhost:6333",
            compression_url="http://localhost:8001"
        )
        return MCPExternalClient(config)
    
    @pytest.mark.asyncio
    async def test_check_qdrant_status_success(self, client):
        """Test vérification statut Qdrant succès."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            status = await client.check_qdrant_status()
            
            assert status.connected is True
            assert status.name == "qdrant-mcp"
            assert "semantic_search" in status.capabilities
    
    @pytest.mark.asyncio
    async def test_check_qdrant_status_failure(self, client):
        """Test vérification statut Qdrant échec."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("Connection refused")
            
            status = await client.check_qdrant_status()
            
            assert status.connected is False
            assert status.error_count == 1
    
    @pytest.mark.asyncio
    async def test_search_similar_fallback_empty(self, client):
        """Test recherche sémantique fallback vide."""
        with patch.object(client.qdrant.rpc_client, 'make_rpc_call') as mock_call:
            mock_call.side_effect = Exception("Qdrant unavailable")
            
            results = await client.search_similar("test query")
            
            assert results == []
    
    @pytest.mark.asyncio
    async def test_compress_content_success(self, client):
        """Test compression succès."""
        with patch.object(client.compression.rpc_client, 'make_rpc_call') as mock_call:
            mock_call.return_value = {
                "compressed": "compressed content here",
                "quality_score": 0.85
            }
            
            result = await client.compress_content(
                content="This is a test content for compression",
                algorithm="context_aware"
            )
            
            assert result is not None
            assert result.algorithm == "context_aware"
            assert result.quality_score == 0.85
    
    @pytest.mark.asyncio
    async def test_compress_content_fallback_zlib(self, client):
        """Test compression fallback vers zlib."""
        with patch.object(client.compression.rpc_client, 'make_rpc_call') as mock_call:
            mock_call.side_effect = Exception("Compression server down")
            
            result = await client.compress_content(
                content="This is a test content for compression fallback",
                algorithm="context_aware"
            )
            
            assert result is not None
            assert "zlib_fallback" in result.algorithm
    
    @pytest.mark.asyncio
    async def test_find_redundant_memories(self, client):
        """Test détection mémoires redondantes."""
        with patch.object(client.qdrant, 'search_similar') as mock_search:
            mock_search.return_value = [
                QdrantSearchResult(id="mem_1", score=0.92),
                QdrantSearchResult(id="mem_2", score=0.88),
            ]
            
            redundant = await client.find_redundant_memories(
                content="Test content",
                similarity_threshold=0.90
            )
            
            assert len(redundant) == 1
            assert redundant[0] == "mem_1"


# ============================================================================
# Tests Memory Manager
# ============================================================================

class TestMemoryManager:
    """Tests du gestionnaire de mémoire."""
    
    @pytest.fixture
    def manager(self):
        """Fixture memory manager."""
        reset_memory_manager()
        mock_client = Mock()
        mock_client.is_qdrant_available.return_value = False
        return MemoryManager(mock_client)
    
    def test_generate_content_hash(self, manager):
        """Test génération hash unique."""
        hash1 = manager._generate_content_hash("Test content")
        hash2 = manager._generate_content_hash("Test content")
        hash3 = manager._generate_content_hash("Different content")
        
        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 16
    
    @pytest.mark.asyncio
    async def test_store_memory_episodic(self, manager):
        """Test stockage mémoire épisodique."""
        with patch('kimi_proxy.features.mcp.memory.get_db') as mock_get_db:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.lastrowid = 123
            mock_cursor.fetchone.return_value = None
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_db.return_value.__exit__ = Mock(return_value=False)
            
            entry = await manager.store_memory(
                session_id=1,
                content="Test episodic memory content",
                memory_type="episodic"
            )
            
            assert entry is not None
            assert entry.session_id == 1
            assert entry.memory_type == "episodic"
            assert entry.id == 123
    
    @pytest.mark.asyncio
    async def test_store_memory_empty_content(self, manager):
        """Test stockage contenu vide refusé."""
        entry = await manager.store_memory(
            session_id=1,
            content="",
            memory_type="episodic"
        )
        
        assert entry is None
    
    @pytest.mark.asyncio
    async def test_find_similar_memories_fallback(self, manager):
        """Test recherche similaire avec fallback textuel."""
        with patch('kimi_proxy.features.mcp.memory.get_db') as mock_get_db:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.fetchall.return_value = [
                (1, 1, "episodic", "hash1", "Preview 1", "Content 1", 100, 5, None, None, None, None),
                (2, 1, "frequent", "hash2", "Preview 2", "Content 2", 200, 10, None, None, None, None),
            ]
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_db.return_value.__exit__ = Mock(return_value=False)
            
            results = await manager.find_similar_memories("test query", session_id=1)
            
            assert len(results) == 2
            assert all(isinstance(r, MCPMemoryEntry) for r in results)
    
    @pytest.mark.asyncio
    async def test_detect_and_promote_frequent_patterns(self, manager):
        """Test détection et promotion patterns fréquents."""
        with patch('kimi_proxy.features.mcp.memory.get_db') as mock_get_db:
            mock_conn = Mock()
            mock_cursor = Mock()
            # 3 candidats avec plus de 3 accès
            mock_cursor.fetchall.return_value = [
                (1, 5),
                (2, 8),
                (3, 4),
            ]
            mock_cursor.rowcount = 3
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_get_db.return_value.__exit__ = Mock(return_value=False)
            
            promoted = await manager.detect_and_promote_frequent_patterns(session_id=1)
            
            assert promoted == 3




# ============================================================================
# Tests Modèles de Données
# ============================================================================

class TestMCPModels:
    """Tests des modèles de données MCP Phase 3."""
    
    def test_mcp_memory_entry_to_dict(self):
        """Test sérialisation MCPMemoryEntry."""
        entry = MCPMemoryEntry(
            id=1,
            session_id=2,
            memory_type="frequent",
            content_hash="abc123",
            content_preview="Preview...",
            full_content="Full content here",
            token_count=100,
            access_count=5,
            similarity_score=0.85
        )
        
        # Sans contenu complet
        dict_without = entry.to_dict(include_content=False)
        assert "full_content" not in dict_without
        assert dict_without["similarity_score"] == 0.85
        
        # Avec contenu complet
        dict_with = entry.to_dict(include_content=True)
        assert dict_with["full_content"] == "Full content here"
    
    def test_mcp_compression_result_to_dict(self):
        """Test sérialisation MCPCompressionResult."""
        result = MCPCompressionResult(
            id=1,
            session_id=2,
            original_tokens=1000,
            compressed_tokens=500,
            compression_ratio=0.5,
            algorithm="context_aware",
            quality_score=0.9
        )
        
        dict_without = result.to_dict(include_content=False)
        assert "compressed_content" not in dict_without
        assert dict_without["compression_ratio"] == 0.5
        assert dict_without["quality_score"] == 0.9
    
    def test_qdrant_search_result_to_dict(self):
        """Test sérialisation QdrantSearchResult."""
        result = QdrantSearchResult(
            id="vec_123",
            score=0.92,
            content_preview="Preview",
            full_content="Full",
            vector=[0.1, 0.2, 0.3]
        )
        
        dict_result = result.to_dict(include_content=True)
        assert dict_result["id"] == "vec_123"
        assert dict_result["score"] == 0.92
        assert dict_result["vector_dimension"] == 3
    
    def test_provider_routing_decision_to_dict(self):
        """Test sérialisation ProviderRoutingDecision."""
        decision = ProviderRoutingDecision(
            original_provider="groq",
            selected_provider="gemini",
            required_context=100000,
            available_context=1048576,
            context_remaining=948576,
            confidence_score=0.85,
            fallback_triggered=True,
            estimated_cost=0.05
        )
        
        dict_result = decision.to_dict()
        assert dict_result["original_provider"] == "groq"
        assert dict_result["fallback_triggered"] is True
        assert dict_result["confidence_score"] == 0.85


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
