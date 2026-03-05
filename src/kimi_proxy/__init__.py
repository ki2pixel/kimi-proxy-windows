"""
Kimi Proxy Dashboard - Package principal.
"""

__version__ = "2.0.0"
__author__ = "Kimi Proxy Team"

try:
    from .main import create_app, app
except ModuleNotFoundError:
    # Permet l'import des sous-modules (ex: tests MCP) sans dépendances runtime API.
    create_app = None  # type: ignore[assignment]
    app = None  # type: ignore[assignment]

__all__ = ["create_app", "app", "__version__"]
