---
name: kimi-proxy-performance-optimization
description: Performance optimization expert for Kimi Proxy Dashboard. Utiliser ce skill pour optimiser latence, token counting, accès DB, WebSocket et cache. Ne pas l’utiliser pour corriger un bug fonctionnel sans enjeu performance.
license: Repository license (see project root)
---

# Kimi Proxy Performance Optimization

## Purpose
Réduire la latence et améliorer le débit/efficience de Kimi Proxy sans dégrader la stabilité.

## When to use
- Latence élevée sur endpoints API/proxy.
- Coûts CPU/mémoire anormaux.
- Requêtes DB lentes ou contention.
- Token counting trop coûteux.
- Saturation WebSocket sous charge.

## When NOT to use
- Bug logique sans impact performance.
- Refonte produit globale sans métrique cible.
- Changement purement documentation/UI copy.

## Inputs required
- Métriques de base (p50/p95, CPU, RAM, QPS).
- Zone suspecte (DB, proxy, websocket, token count).
- Scénario de charge minimal reproductible.
- Seuils de performance attendus.

## Workflow
1. Mesurer baseline avant toute modification.
2. Identifier le goulot (I/O, CPU, DB, réseau).
3. Proposer optimisation ciblée par priorité d’impact.
4. Implémenter un changement à la fois.
5. Re-mesurer et comparer baseline vs après.
6. Valider absence de régression fonctionnelle.

## Output contract
- Mesures avant/après comparables.
- Optimisation localisée et justifiée.
- Plan de suivi (monitoring + rollback simple).

## Guardrails
- Async/await obligatoire, HTTPX only, typing strict.
- Tiktoken pour comptage de tokens (pas d’estimation grossière).
- Respect architecture 5 couches et DI/factory patterns.
- Pas de global state non maîtrisé.
- Aucune fuite de secrets.

## Exemples minimaux
- « Réduire p95 `/chat/completions` de 20% via optimisation DB ».
- « Diminuer coût token counting sur gros messages avec cache contrôlé ».

## Kimi Proxy references
- `.clinerules/codingstandards.md`
- `docs/codex/skills.md`
- `docs/architecture/modular-architecture-v2.md`
- `docs/features/mcp.md`
- `README.md`
