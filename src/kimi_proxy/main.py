"""
Kimi Proxy - Application FastAPI Factory.
Proxy streaming + Pure Middleware MCP.
Intégration Log Watcher pour PyCharm/Continue.
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.database import init_database, create_session, get_active_session
from .config.loader import load_config
from .services.cline_polling import ClinePollingConfig, create_cline_polling_service
from .features.log_watcher import create_log_watcher
from .api.router import api_router
from .api.routes.health import set_log_watcher


def create_app() -> FastAPI:
    """
    Factory pour créer l'application FastAPI.

    Returns:
        Instance configurée de FastAPI
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Gestion du cycle de vie de l'application."""
        # Startup
        _startup(app)
        yield
        # Shutdown
        await _shutdown(app)

    app = FastAPI(
        title="Kimi Proxy API",
        description="Proxy transparent Pure Middleware MCP",
        version="2.0.0",
        lifespan=lifespan
    )

    # CORS
    allowed_origins_raw = os.environ.get(
        "KIMI_PROXY_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000"
    )
    allowed_origins = [orig.strip() for orig in allowed_origins_raw.split(",") if orig.strip()]
    allow_credentials = os.environ.get("KIMI_PROXY_ALLOW_CREDENTIALS", "false").lower() in ("true", "1", "yes")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Inclusion des routes API
    app.include_router(api_router)

    return app


def _startup(app: FastAPI):
    """Initialisation au démarrage."""
    print("🚀 Démarrage du Kimi Proxy (Pure Middleware MCP)...")

    # Validation critique de l'authentification (production)
    env = os.environ.get("KIMI_PROXY_ENV", "production").lower()
    secret = os.environ.get("KIMI_PROXY_SECRET")
    import sys
    is_pytest = "pytest" in sys.modules
    if not secret and env != "development" and env != "dev" and not is_pytest:
        raise RuntimeError(
            "CRITICAL SECURITY ERROR: KIMI_PROXY_SECRET is not configured, and KIMI_PROXY_ENV is not set to 'development'."
        )

    # Charge la configuration
    config = load_config()
    providers = config.get("providers", {})
    models = config.get("models", {})

    print(f"✅ {len(providers)} provider(s) chargé(s)")
    print(f"✅ {len(models)} modèle(s) chargé(s)")

    # Initialise la base de données
    init_database()

    # Crée une session par défaut si aucune
    if not get_active_session():
        provider_key = "managed:kimi-code"
        create_session("Session par défaut", provider_key)
        print(f"✅ Session par défaut créée (provider: {provider_key})")

    # Démarre le Log Watcher
    async def broadcast_log_metrics(metrics, watcher):
        """Callback pour logger les métriques du log watcher."""
        from .core.database import get_active_session
        from .config.display import get_max_context_for_session

        session = get_active_session()
        if not session:
            return

        max_context = watcher.get_max_context(
            get_max_context_for_session(session, models)
        )
        total_tokens = metrics.total_tokens
        percentage = (total_tokens / max_context) * 100 if max_context > 0 else 0

        # Log détaillé selon le type
        if metrics.is_compile_chat:
            print(f"📊 [COMPILE] Context: {metrics.context_length}, "
                  f"Tools: {metrics.tools_tokens}, "
                  f"System: {metrics.system_message_tokens} "
                  f"= {total_tokens} ({percentage:.1f}%)")
        elif metrics.is_api_error:
            print(f"⚠️ [API ERROR] Tokens: {total_tokens} (limite atteinte)")
        elif total_tokens > 100:
            print(f"📊 [LOGS] Tokens: {total_tokens} ({percentage:.1f}%)")

    log_watcher = create_log_watcher(broadcast_callback=broadcast_log_metrics)

    # Démarre le polling Cline (ledger local)
    cline_polling_raw = config.get("cline", {}).get("polling", {})
    try:
        cline_polling_enabled = bool(cline_polling_raw.get("enabled", True))
        cline_interval_seconds = float(cline_polling_raw.get("interval_seconds", 60.0))
        cline_backoff_max_seconds = float(cline_polling_raw.get("backoff_max_seconds", 600.0))
    except (TypeError, ValueError):
        cline_polling_enabled = True
        cline_interval_seconds = 60.0
        cline_backoff_max_seconds = 600.0

    cline_polling_config = ClinePollingConfig(
        enabled=cline_polling_enabled,
        interval_seconds=max(cline_interval_seconds, 5.0),
        # backoff >= interval (sinon on clamp au minimum fonctionnel)
        backoff_max_seconds=max(cline_backoff_max_seconds, max(cline_interval_seconds, 30.0)),
    )
    cline_polling = create_cline_polling_service(config=cline_polling_config)

    # Stocke le log watcher dans l'app state
    app.state.log_watcher = log_watcher
    app.state.cline_polling = cline_polling
    app.state.config = config

    # Enregistre pour le health check
    set_log_watcher(log_watcher)

    # Démarre le watcher (dans la lifespan async)
    import asyncio
    asyncio.create_task(log_watcher.start())

    # Démarre le polling Cline (tâche asyncio)
    asyncio.create_task(cline_polling.start())

    print("🌐 API Kimi Proxy disponible sur http://localhost:8000")


async def _shutdown(app: FastAPI):
    """Arrêt de l'application."""
    print("\n👋 Arrêt du serveur...")

    # Arrête le Log Watcher
    if hasattr(app.state, 'log_watcher'):
        await app.state.log_watcher.stop()

    # Arrête le polling Cline
    if hasattr(app.state, 'cline_polling'):
        await app.state.cline_polling.stop()

    print("✅ Serveur arrêté proprement")


# Crée l'application pour uvicorn
app = create_app()
