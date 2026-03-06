---
name: kimi-proxy-streaming-debug
description: Expert debugging for streaming errors in Kimi Proxy Dashboard. Utiliser ce skill pour traiter ReadError, TimeoutException, ConnectError, SSE et WebSocket. Ne pas l’utiliser pour implémenter une nouvelle feature hors incident streaming.
license: Repository license (see project root)
---

# Kimi Proxy Streaming Debug

## Purpose
Diagnostiquer et corriger les incidents de streaming (HTTPX stream, SSE, WebSocket) avec méthode RCA.

## When to use
- `ReadError`, `TimeoutException`, `ConnectError`.
- Flux SSE interrompu ou incomplet.
- Déconnexions WebSocket ou messages corrompus.
- Régressions de streaming après changement infra/config.

## When NOT to use
- Développement d’une fonctionnalité sans erreur streaming.
- Optimisation perf globale sans symptôme streaming.
- Tâches uniquement documentation.

## Inputs required
- Trace d’erreur complète + timestamp.
- Provider/modèle impacté.
- Payload minimal reproductible.
- Logs proxy + état réseau basique.

## Workflow
1. Reproduire sur cas minimal (stream on/off comparatif).
2. Isoler le point de rupture (provider, proxy, client, réseau).
3. Vérifier headers/format SSE et ordre des chunks.
4. Contrôler timeouts, retries, keepalive, backpressure.
5. Tester correctif ciblé avec scénario nominal + dégradé.
6. Ajouter test anti-régression.

## Output contract
- Cause racine streaming identifiée.
- Correctif précis (timeout, parser, retry, framing, etc.).
- Validation par test et logs de confirmation.

## Guardrails
- HTTPX only côté Python réseau.
- Async/await strict, pas de blocage sync.
- Pas de suppression silencieuse d’exception.
- Respect architecture 5 couches.
- Pas de fuite de données sensibles dans logs.

## Exemples minimaux
- « Corriger un flux SSE tronqué avec `[DONE]` manquant ».
- « Stabiliser reconnexion WebSocket avec backoff exponentiel ».

## Kimi Proxy references
- `.clinerules/codingstandards.md`
- `docs/codex/skills.md`
- `docs/features/mcp.md`
- `docs/architecture/modular-architecture-v2.md`
- `README.md`
