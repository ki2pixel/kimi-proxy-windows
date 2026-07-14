"""
Gestion du streaming et extraction des tokens avec gestion d'erreurs robuste.

Pourquoi cette complexité:
- Les providers peuvent interrompre le stream (ReadError)
- Le réseau peut être instable
- Les timeouts doivent être gérés gracieusement
- Les tokens partiels doivent être extraits même en cas d'erreur
"""
import json
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime

import httpx

from ..core.database import update_metric_with_real_tokens
from ..config.display import get_max_context_for_session


# Types d'erreurs streaming connus
STREAMING_ERROR_TYPES = {
    "read_error": "Connexion interrompue par le provider",
    "connect_error": "Impossible de se connecter au provider",
    "timeout_error": "Timeout lors de la lecture du stream",
    "decode_error": "Erreur de décodage des données",
    "unknown": "Erreur streaming inconnue"
}


async def stream_generator(
    response: httpx.Response,
    session_id: int,
    metric_id: int,
    body: Optional[bytes] = None,
    headers: Optional[Dict[str, Any]] = None,
    provider_type: str = "openai",
    models: Optional[Dict[str, Any]] = None,
    max_retries: int = 1,
    retry_delay: float = 1.0
) -> AsyncGenerator[bytes, None]:
    """
    Générateur de streaming + extraction des vrais tokens avec gestion d'erreurs.

    Pourquoi le retry à l'intérieur du générateur:
    - Une fois que le stream commence, on ne peut pas "recommencer" la requête
    - Le retry ici concerne les reconnexions si le provider supporte les resumes
    - La plupart du temps, on fait du best-effort: on extrait ce qu'on peut

    Args:
        response: Réponse HTTPX en streaming
        session_id: ID de la session
        metric_id: ID de la métrique
        body: Body de la requête (optionnel)
        headers: Headers de la requête (optionnel)
        provider_type: Type de provider
        models: Dictionnaire des modèles
        max_retries: Nombre max de retries (pour futures implémentations resume)
        retry_delay: Délai entre retries en secondes

    Yields:
        Chunks de la réponse

    Raises:
        Aucune: Les erreurs sont loggées et le stream se termine proprement
    """
    buffer = b""
    first_chunk = True
    chunk_count = 0
    stream_start_time = datetime.now()

    try:
        # Itération sur les chunks avec gestion d'erreurs granulaire
        async for chunk in _iter_stream_with_error_handling(response, provider_type):
            chunk_count += 1

            # Log du premier chunk pour debug
            if first_chunk and response.status_code >= 400:
                _log_error_response(chunk, response.status_code)
            first_chunk = False

            # Accumulation et yield
            buffer += chunk
            yield chunk

    except httpx.ReadError as e:
        # Erreur la plus courante: connexion interrompue
        ("read_error", str(e))
        _log_streaming_error(
            error_type="read_error",
            provider=provider_type,
            session_id=session_id,
            metric_id=metric_id,
            chunks_received=chunk_count,
            error=str(e),
            start_time=stream_start_time
        )

    except httpx.ConnectError as e:
        ("connect_error", str(e))
        _log_streaming_error(
            error_type="connect_error",
            provider=provider_type,
            session_id=session_id,
            metric_id=metric_id,
            chunks_received=chunk_count,
            error=str(e),
            start_time=stream_start_time
        )

    except httpx.TimeoutException as e:
        ("timeout_error", str(e))
        _log_streaming_error(
            error_type="timeout_error",
            provider=provider_type,
            session_id=session_id,
            metric_id=metric_id,
            chunks_received=chunk_count,
            error=str(e),
            start_time=stream_start_time
        )

    except Exception as e:
        # Erreur inattendue - on log et on continue
        ("unknown", str(e))
        _log_streaming_error(
            error_type="unknown",
            provider=provider_type,
            session_id=session_id,
            metric_id=metric_id,
            chunks_received=chunk_count,
            error=str(e),
            start_time=stream_start_time
        )

    finally:
        # Extraction des tokens même si le stream a échoué
        # Pourquoi: les tokens partiels sont valides et doivent être comptabilisés
        if metric_id and session_id:
            try:
                usage_data = extract_usage_from_stream(buffer, provider_type)
                if usage_data and models:
                    _process_token_update(session_id, metric_id, usage_data, models)
            except Exception as e:
                # Même l'extraction peut fail - on log mais on ne crash pas
                print(f"⚠️  [STREAM] Erreur extraction usage après stream: {e}")

        client_ref = getattr(response, "_client_ref", None)
        if client_ref is not None:
            try:
                await client_ref.aclose()
                print("🔒 [STREAM] Client HTTPX de streaming fermé.")
            except Exception as e:
                print(f"⚠️  [STREAM] Erreur lors de la fermeture du client HTTPX: {e}")


async def _iter_stream_with_error_handling(
    response: httpx.Response,
    provider_type: str
) -> AsyncGenerator[bytes, None]:
    """
    Itère sur le stream avec timeout et gestion d'erreurs.

    Pourquoi un timeout de chunk: certains providers peuvent
    "geler" sans fermer la connexion.
    """
    # Timeout par provider (certains sont plus lents)
    chunk_timeout = {
        "gemini": 60.0,      # Gemini peut être lent
        "kimi": 30.0,        # Kimi est généralement rapide
        "default": 30.0
    }.get(provider_type, 30.0)

    try:
        async for chunk in response.aiter_bytes():
            yield chunk
    except httpx.ReadTimeout:
        # Timeout spécifique pendant la lecture
        raise httpx.TimeoutException(
            f"Timeout lecture chunk après {chunk_timeout}s"
        )


def _log_error_response(chunk: bytes, status_code: int) -> None:
    """Log une réponse d'erreur API."""
    try:
        error_text = chunk.decode('utf-8', errors='ignore')[:500]
        print(f"❌ [STREAM] Erreur API {status_code}: {error_text}")
    except Exception:
        pass


def _log_streaming_error(
    error_type: str,
    provider: str,
    session_id: int,
    metric_id: int,
    chunks_received: int,
    error: str,
    start_time: datetime
) -> None:
    """
    Log structuré d'une erreur streaming.

    Pourquoi cette structure: permet de parser les logs
    pour des dashboards de monitoring provider.
    """
    duration = (datetime.now() - start_time).total_seconds()
    error_msg = STREAMING_ERROR_TYPES.get(error_type, STREAMING_ERROR_TYPES["unknown"])

    print(
        f"🔴 [STREAM_ERROR] {error_msg}\n"
        f"   Provider: {provider}\n"
        f"   Session: {session_id}, Metric: {metric_id}\n"
        f"   Chunks reçus: {chunks_received}\n"
        f"   Durée: {duration:.2f}s\n"
        f"   Détail: {error[:200]}"
    )


def _process_token_update(
    session_id: int,
    metric_id: int,
    usage_data: Dict[str, int],
    models: dict
):
    """Met à jour les tokens en base."""
    from ..core.database import get_session_by_id

    session = get_session_by_id(session_id)
    if not session:
        return

    max_context = get_max_context_for_session(session, models)

    prompt_tokens = usage_data.get("prompt_tokens", 0)
    completion_tokens = usage_data.get("completion_tokens", 0)
    total_tokens = usage_data.get("total_tokens", 0) or (prompt_tokens + completion_tokens)

    update_metric_with_real_tokens(
        metric_id,
        prompt_tokens,
        completion_tokens,
        total_tokens,
        max_context
    )


def extract_usage_from_stream(buffer: bytes, provider_type: str = "openai") -> Optional[Dict[str, int]]:
    """
    Extrait les usage tokens du stream SSE.

    Pourquoi on cherche dans les lignes inversées:
    - Les tokens d'usage sont généralement dans le dernier chunk
    - Format SSE: data: {...} par ligne
    - [DONE] marque la fin du stream

    Args:
        buffer: Buffer contenant tout le stream (même partiel)
        provider_type: Type de provider

    Returns:
        Dictionnaire avec prompt_tokens, completion_tokens, total_tokens
        ou None si pas trouvé
    """
    if not buffer:
        return None

    text = buffer.decode('utf-8', errors='ignore')
    lines = text.strip().split('\n')

    for line in reversed(lines):
        if line.startswith('data: '):
            data_str = line[6:]
            if data_str == '[DONE]':
                continue
            try:
                data = json.loads(data_str)

                # Format OpenAI standard
                if 'usage' in data and data['usage']:
                    usage = data['usage']
                    return {
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0)
                    }

                # Format Gemini
                if provider_type == "gemini":
                    if 'usageMetadata' in data:
                        meta = data['usageMetadata']
                        return {
                            "prompt_tokens": meta.get("promptTokenCount", 0),
                            "completion_tokens": meta.get("candidatesTokenCount", 0),
                            "total_tokens": meta.get("totalTokenCount", 0)
                        }

            except json.JSONDecodeError:
                # Ligne malformée - on continue
                continue
            except Exception:
                # Autre erreur - on continue
                continue

    return None


def extract_usage_from_response(response_data: Dict[str, Any]) -> Optional[Dict[str, int]]:
    """
    Extrait les usage tokens d'une réponse complète (non-streaming).

    Args:
        response_data: Données JSON de la réponse (dict ou list pour Gemini)

    Returns:
        Dictionnaire avec prompt_tokens, completion_tokens, total_tokens
    """
    # Gemini peut retourner une liste au lieu d'un dict
    if isinstance(response_data, list) and len(response_data) > 0:
        response_data = response_data[0]

    if not isinstance(response_data, dict):
        return None

    usage = response_data.get('usage', {})
    if usage:
        return {
            "prompt_tokens": usage.get('prompt_tokens', 0),
            "completion_tokens": usage.get('completion_tokens', 0),
            "total_tokens": usage.get('total_tokens', 0)
        }
    return None
