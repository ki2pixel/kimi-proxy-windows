---
name: docs-updater
description: Mettre à jour la documentation Kimi Proxy via audit structurel et comparaison code/docs. Invocation explicite `$docs-updater`.
license: Repository license (see project root)
---

# Role
Documentation engineer orienté qualité; audite le code puis met à jour la documentation avec traçabilité métrique.

# When to use
- La documentation est obsolète ou incomplète.
- Une feature/modification récente n’est pas reflétée dans les docs.
- Un audit code-vs-docs est demandé.

# When NOT to use
- Correctif applicatif pur sans objectif documentation.
- Débogage runtime sans livrable doc.
- Refactor backend/frontend sans demande de mise à jour documentaire.

# Inputs required
- Périmètre documentaire (README, docs/features, docs/api, etc.).
- Zones de code impactées.
- Contraintes de format et public cible.

# Workflow
1. Lire le contexte minimal: `C:/Users/kidpixel/Documents/kimi-proxy/memory-bank/activeContext.md`.
2. Réaliser un audit structurel ciblé (tree/cloc/radon/recherche de patterns).
3. Comparer code réel et documentation existante.
4. Proposer un plan de mise à jour documentée (fichiers, diagnostics, corrections).
5. Après validation, appliquer les modifications docs.
6. Vérifier cohérence finale (liens, sections, terminologie, garde-fous).

# Output contract
- Plan de mise à jour explicite avant édition.
- Diff documentation cohérent et vérifiable.
- Résumé final avec fichiers modifiés et impacts.

# Guardrails
- Source de vérité: code > documentation > mémoire.
- Respect de la méthode `.cline/skills/documentation/SKILL.md` (TL;DR, problem-first, ❌/✅, trade-offs, Golden Rule).
- Respect architecture 5 couches et standards Kimi Proxy.
- Aucun secret dans les exemples de documentation.
