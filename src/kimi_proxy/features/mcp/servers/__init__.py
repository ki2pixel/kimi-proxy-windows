"""
Package des clients MCP spécialisés par serveur.

Ce package contient des clients dédiés pour chaque serveur MCP:
- qdrant: Recherche sémantique et clustering
- compression: Compression contextuelle
- task_master: Gestion de tâches et workflows PRD
- sequential: Raisonnement séquentiel
- filesystem: Opérations filesystem avancées
- json_query: Requêtes JSONPath
"""

from .qdrant import QdrantMCPClient
from .compression import CompressionMCPClient
from .task_master import TaskMasterMCPClient
from .sequential import SequentialThinkingMCPClient
from .filesystem import FileSystemMCPClient
from .json_query import JsonQueryMCPClient

__all__ = [
    "QdrantMCPClient",
    "CompressionMCPClient",
    "TaskMasterMCPClient",
    "SequentialThinkingMCPClient",
    "FileSystemMCPClient",
    "JsonQueryMCPClient",
]
