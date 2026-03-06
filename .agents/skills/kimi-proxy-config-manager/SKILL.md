---
name: kimi-proxy-config-manager
description: Expert configuration management pour Kimi Proxy (TOML/YAML, providers, clés API, routing modèles). Utiliser ce skill pour créer, corriger ou auditer la configuration. Ne pas l’utiliser pour implémenter des features métier hors configuration.
license: Repository license (see project root)
---

# Kimi Proxy Config Manager

## Purpose
Gérer la configuration Kimi Proxy de manière sûre, reproductible et compatible production.

## When to use
- Ajout/modification de providers et modèles.
- Correction d’un problème de mapping modèle/provider.
- Mise en place variables d’environnement pour secrets.
- Audit de cohérence entre `config.toml`, `config.yaml` et runtime.

## When NOT to use
- Débogage streaming SSE/WebSocket sans lien config.
- Refonte d’architecture applicative.
- Écriture de tests sans objectif config.

## Inputs required
- Fichiers de config cibles (`config.toml`, `config.yaml`, etc.).
- Provider/model à ajouter ou corriger.
- Variables d’environnement attendues.
- Contrainte de compatibilité (dev/prod, Windows).

## Workflow
1. Lire la config existante et valider syntaxe.
2. Identifier la section à modifier (provider, model, routing, timeout).
3. Appliquer une modification minimale et explicite.
4. Vérifier absence de secrets hardcodés.
5. Contrôler cohérence mapping modèle → provider.
6. Valider via checks de config et scénario API minimal.

## Output contract
- Config valide (syntaxe + logique).
- Secrets référencés via variables d’environnement.
- Mapping modèle/provider documenté et testable.

## Guardrails
- Respect architecture 5 couches Kimi Proxy.
- No hardcoded secrets.
- Rester sur mapping simple (exact match puis logique suffixe).
- Pas de routes de compatibilité expérimentales non demandées.
- Respect workspace MCP.

## Exemples minimaux
- « Ajouter un provider OpenAI-compatible avec `${OPENROUTER_API_KEY}` ».
- « Corriger un `model` mal routé vers le mauvais provider ».

## Kimi Proxy references
- `.clinerules/codingstandards.md`
- `docs/codex/skills.md`
- `docs/features/mcp.md`
- `README.md`
