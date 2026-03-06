---
name: kimi-proxy-frontend-architecture
description: Real-time dashboard, ES6 modules, Chart.js, WebSocket architecture. Utiliser ce skill pour concevoir ou corriger l’architecture frontend modulaire Kimi Proxy. Ne pas l’utiliser pour la logique backend/API.
license: Repository license (see project root)
---

# Kimi Proxy Frontend Architecture

## Purpose
Structurer et faire évoluer le frontend Kimi Proxy en modules ES6, avec flux temps réel WebSocket et visualisation Chart.js.

## When to use
- Conception/refactor de modules frontend (`static/js/modules`).
- Organisation EventBus, gestion d’état UI, synchronisation WebSocket.
- Évolutions dashboard temps réel et graphiques.

## When NOT to use
- Corrections backend FastAPI/proxy DB.
- Débogage pur streaming provider côté serveur.
- Gestion configuration providers/API keys.

## Inputs required
- Écran/feature visé.
- Modules impactés.
- Contrat API/WebSocket consommé.
- Contraintes UX/performance.

## Workflow
1. Cartographier le flux UI → API/WebSocket → rendu.
2. Définir responsabilité de chaque module ES6.
3. Implémenter interfaces explicites entre modules.
4. Garantir robustesse des états temps réel (reconnect, erreurs).
5. Vérifier rendu graphique et performance perçue.
6. Valider messages UI en français.

## Output contract
- Architecture modulaire claire et découplée.
- Flux temps réel fiable.
- Composants réutilisables avec responsabilités nettes.

## Guardrails
- Respect architecture 5 couches (frontend consomme API/WS, ne contourne pas).
- Vanilla JS + ES6 modules, pas de framework lourd.
- Textes UI en français.
- Pas de secrets côté client.
- Pas de logique métier backend injectée dans UI.

## Exemples minimaux
- « Extraire un gestionnaire WebSocket en module dédié avec retry/backoff ».
- « Modulariser un composant chart sans casser l’EventBus existant ».

## Kimi Proxy references
- `.clinerules/codingstandards.md`
- `docs/codex/skills.md`
- `docs/development/frontend-modularization.md`
- `docs/architecture/modular-architecture-v2.md`
- `README.md`
