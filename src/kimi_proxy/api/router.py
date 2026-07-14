"""
Router principal de l'API.
"""
from fastapi import APIRouter, Depends

from .auth import verify_proxy_secret
from .routes import (
    sessions,
    providers,
    proxy,
    exports,
    sanitizer,
    mcp,
    compression,
    compaction,
    health,
    models,
    cline,
    mcp_gateway,
)

# Router principal
api_router = APIRouter()

# Inclusion des sous-routers avec authentification requise
api_router.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"], dependencies=[Depends(verify_proxy_secret)])
api_router.include_router(providers.router, prefix="/api/providers", tags=["providers"], dependencies=[Depends(verify_proxy_secret)])
# ... autres routes existantes ...
api_router.include_router(exports.router, prefix="/api/export", tags=["exports"], dependencies=[Depends(verify_proxy_secret)])
api_router.include_router(sanitizer.router, prefix="/api", tags=["sanitizer"], dependencies=[Depends(verify_proxy_secret)])
api_router.include_router(mcp.router, prefix="/api", tags=["mcp"], dependencies=[Depends(verify_proxy_secret)])
api_router.include_router(compression.router, prefix="/api/compress", tags=["compression"], dependencies=[Depends(verify_proxy_secret)])
api_router.include_router(compaction.router, prefix="/api/compaction", tags=["compaction"], dependencies=[Depends(verify_proxy_secret)])
api_router.include_router(health.router, prefix="", tags=["health"])

# MCP Gateway (Observation Masking)
api_router.include_router(mcp_gateway.router, prefix="/api", tags=["mcp-gateway"], dependencies=[Depends(verify_proxy_secret)])

# Cline (Solution 1 - ledger local)
api_router.include_router(cline.router, prefix="", tags=["cline"], dependencies=[Depends(verify_proxy_secret)])

# === API STANDARDS ===
# ✅ Routes standardisées sous /api
api_router.include_router(models.router, prefix="/api/models", tags=["models"], dependencies=[Depends(verify_proxy_secret)])
api_router.include_router(models.openai_router, prefix="", tags=["models-openai"])
api_router.include_router(proxy.router, prefix="", tags=["proxy"])