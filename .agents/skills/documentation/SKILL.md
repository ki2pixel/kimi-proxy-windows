---
name: documentation
description: Utiliser ce skill pour rédiger ou refactorer de la documentation Kimi Proxy (README, guides, API docs) avec structure claire et ton technique naturel. Ne pas l’utiliser pour diagnostiquer un bug ou modifier du code métier.
license: Repository license (see project root)
---

# Documentation (Kimi Proxy)

## Purpose
Produire une documentation technique exploitable par l’équipe Kimi Proxy, centrée sur les décisions, le contexte et les workflows.

## When to use
- Création ou mise à jour de README, guides, docs d’architecture/features.
- Clarification d’un workflow API, MCP, frontend modulaire.
- Harmonisation de style entre plusieurs documents.

## When NOT to use
- Implémentation de code applicatif.
- Débogage d’incident runtime.
- Planification détaillée de backlog (utiliser shrimp-task-manager).

## Inputs required
- Audience cible (dev, ops, contributeur).
- Objectif du document et périmètre.
- Sources à citer (code, docs existantes, standards).
- Contraintes de format attendues.

## Workflow
1. Définir le problème lecteur et le résultat attendu.
2. Structurer le document (TL;DR, sections, exemples).
3. Prioriser le “pourquoi” (décisions, trade-offs) avant le “quoi”.
4. Ajouter exemples concrets et contre-exemples utiles.
5. Vérifier cohérence terminologie et liens internes.
6. Finaliser avec checklist d’usage/limitations.

## Output contract
- Document clair, actionnable, et maintenable.
- Terminologie alignée au projet Kimi Proxy.
- Exemples minimaux valides, sans secret.
- Références explicites aux documents normatifs.

## Guardrails
- Respect architecture 5 couches Kimi Proxy.
- Cohérence avec async/await, HTTPX only, typing strict.
- Aucune clé/API secret en exemple.
- Textes UI mentionnés en français.
- Ne pas inventer des routes de compatibilité non validées.

## Exemples minimaux
- « Mettre à jour `README.md` avec un guide de configuration provider ». 
- « Écrire une note d’architecture pour la couche Features (MCP) ».

## Kimi Proxy references
- `.clinerules/codingstandards.md`
- `docs/codex/skills.md`
- `docs/architecture/modular-architecture-v2.md`
- `docs/development/frontend-modularization.md`
- `docs/features/mcp.md`
- `README.md`
