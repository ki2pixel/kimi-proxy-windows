"""
Module d'authentification pour Kimi Proxy.
"""
import os
import logging
from typing import Optional
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

async def verify_proxy_secret(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Dépendance FastAPI pour valider le secret du proxy (KIMI_PROXY_SECRET).
    
    Supporte à la fois :
    1. L'en-tête standard 'Authorization: Bearer <secret>' (via credentials).
    2. L'en-tête personnalisé 'X-Proxy-Secret: <secret>' (fallback).
    
    Si KIMI_PROXY_SECRET n'est pas défini dans l'environnement, l'authentification
    est désactivée (fail-open) UNIQUEMENT en mode développement ou en cours de tests (pytest).
    Dans tous les autres cas (production), l'absence de secret lève une exception de configuration.
    """
    secret = os.environ.get("KIMI_PROXY_SECRET")
    if not secret:
        env = os.environ.get("KIMI_PROXY_ENV", "production").lower()
        import sys
        is_pytest = "pytest" in sys.modules
        if env == "development" or env == "dev" or is_pytest:
            return None
        raise HTTPException(
            status_code=500,
            detail="Security misconfiguration: KIMI_PROXY_SECRET is not set."
        )
        
    token = None
    if credentials:
        token = credentials.credentials
    else:
        # Fallback sur l'en-tête personnalisé
        token = request.headers.get("x-proxy-secret")
        
    if not token or token != secret:
        logger.warning("Tentative d'accès non autorisée rejetée (secret invalide ou manquant).")
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: invalid or missing KIMI_PROXY_SECRET"
        )
        
    return token
