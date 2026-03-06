---
name: debugging-strategies
description: Utiliser ce skill pour diagnostiquer un bug, une régression ou un problème de performance Kimi Proxy (proxy HTTPX, WebSocket, SSE, DB). Ne pas l’utiliser pour implémenter une nouvelle fonctionnalité sans incident à investiguer.
license: Repository license (see project root)
---

# Debugging Strategies (Kimi Proxy)

## Purpose
Mener une analyse RCA (Root Cause Analysis) reproductible et actionnable sur un incident Kimi Proxy.

## When to use
- Erreurs runtime (ReadError, TimeoutException, ConnectError, 5xx).
- Régressions après merge/upgrade.
- Problèmes de performance (latence, CPU, DB, WebSocket).
- Comportements intermittents difficiles à reproduire.

## When NOT to use
- Développement d’une fonctionnalité neuve sans bug observé.
- Refactor purement stylistique.
- Documentation fonctionnelle sans diagnostic technique.

## Inputs required
- Symptôme exact + message d’erreur complet.
- Étapes de reproduction minimales.
- Environnement (OS, config, provider, version commit).
- Logs pertinents (sans secrets).

## Workflow
1. Reproduire le bug sur un scénario minimal et stable.
2. Définir une hypothèse unique à tester.
3. Isoler la couche impactée (API, Services, Features, Proxy, Core).
4. Collecter preuves: logs, timings, diff git, traces SSE/WebSocket.
5. Tester l’hypothèse par expérience ciblée (une variable à la fois).
6. Identifier la cause racine et ses conditions de déclenchement.
7. Proposer un correctif minimal + test de non-régression.
8. Vérifier en local puis en scénario proche production.

## Output contract
- Cause racine validée (pas une supposition).
- Correctif proposé avec zone de code impactée.
- Plan de vérification (tests ciblés + résultat attendu).
- Risques résiduels documentés.

## Guardrails
- Respect architecture 5 couches: API ← Services ← Features ← Proxy ← Core.
- Async/await obligatoire; aucune E/S bloquante.
- HTTPX only côté Python réseau.
- Typing strict, pas de `Any`.
- Aucun secret en clair dans logs, commits ou exemples.
- Respect strict du workspace MCP autorisé.

## Exemples minimaux
- « Diagnostiquer un `httpx.ReadError` durant un stream SSE provider Kimi ».
- « Expliquer une hausse latence endpoint `/chat/completions` après migration DB ».

## Kimi Proxy references
- `.clinerules/codingstandards.md`
- `docs/codex/skills.md`
- `docs/architecture/modular-architecture-v2.md`
- `docs/features/mcp.md`
- `README.md`
