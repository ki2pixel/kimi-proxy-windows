---
name: kimi-proxy-testing-strategies
description: Utiliser ce skill pour définir et exécuter des stratégies de tests Kimi Proxy (unitaires, intégration, E2E, async). Ne pas l’utiliser pour implémenter directement des fonctionnalités hors périmètre test.
license: Repository license (see project root)
---

# Kimi Proxy Testing Strategies

## Purpose
Concevoir des tests fiables et ciblés pour sécuriser les évolutions Kimi Proxy.

## When to use
- Ajout de tests unitaires/intégration/E2E.
- Conception de test de non-régression après bugfix.
- Structuration de fixtures async et mocks HTTPX.
- Validation d’un comportement MCP/proxy/API.

## When NOT to use
- Débugging sans intention d’ajouter des tests.
- Refactor purement code sans stratégie test.
- Documentation sans objectif vérification technique.

## Inputs required
- Comportement à valider (nominal + cas limites).
- Périmètre test (module/endpoint/workflow).
- Dépendances à mocker.
- Critères d’acceptation mesurables.

## Workflow
1. Définir le contrat de comportement attendu.
2. Choisir le niveau de test minimal pertinent.
3. Préparer fixtures async et données isolées.
4. Écrire tests nominal + erreur + edge cases.
5. Exécuter la suite ciblée.
6. Corriger flaky tests et stabiliser assertions.

## Output contract
- Tests lisibles, déterministes et maintenables.
- Couverture utile du risque métier/technique ciblé.
- Résultat d’exécution clair (pass/fail, portée).

## Guardrails
- `pytest-asyncio` pour les flux async.
- HTTPX mocké proprement pour appels externes.
- Pas de dépendance réseau non contrôlée en unit test.
- Respect architecture 5 couches dans le découpage des tests.
- Pas de secrets hardcodés dans fixtures.

## Exemples minimaux
- « Ajouter un test de non-régression sur timeout streaming ».
- « Couvrir un endpoint FastAPI avec fixture DB mémoire ».

## Kimi Proxy references
- `.clinerules/codingstandards.md`
- `docs/codex/skills.md`
- `docs/architecture/modular-architecture-v2.md`
- `docs/features/mcp.md`
- `README.md`
