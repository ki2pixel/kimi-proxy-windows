---
name: shrimp-task-manager
description: Expert en gestion de tâches via les outils shrimp-task-manager. Gère les backlogs, roadmaps et analyse de complexité pour transformer les demandes complexes en plans d'action structurés.
license: Repository license (see project root)
---

# Shrimp Task Manager (Kimi Proxy)

## Purpose
Transformer des demandes complexes en plan exécutable (analyse, découpage, dépendances, vérification).

## When to use
- Besoin de planification multi-étapes.
- Backlog à structurer/prioriser.
- Décomposition d’un objectif en sous-tâches vérifiables.
- Gouvernance de livraison (score, critères, dépendances).

## When NOT to use
- Correctif simple mono-fichier.
- Réponse factuelle immédiate sans exécution projet.
- Rédaction doc pure sans backlog.

## Inputs required
- Objectif global clair.
- Contraintes techniques/qualité.
- Contexte projet et périmètre.
- Critères d’acceptation attendus.

## Workflow
1. Planifier (`plan_task`) avec contexte complet.
2. Analyser faisabilité/risques (`analyze_task`).
3. Réviser critiquement (`reflect_task`).
4. Découper (`split_tasks`) en tâches atomiques + dépendances.
5. Exécuter guidé (`execute_task`) tâche par tâche.
6. Vérifier/scorer (`verify_task`) selon critères.

## Output contract
- Backlog structuré et priorisé.
- Dépendances explicites.
- Critères de vérification mesurables.
- Traçabilité des décisions.

## Guardrails
- Pas d’hypothèses non vérifiées: collecter les faits avant décision.
- Granularité 1-2 jours par sous-tâche.
- Éviter tâches cross-domain trop larges.
- Respect architecture et standards Kimi Proxy.

## Exemples minimaux
- « Découper une migration MCP en sous-tâches avec ordre critique ».
- « Évaluer la complétude d’une implémentation via score de vérification ».

## Kimi Proxy references
- `.clinerules/codingstandards.md`
- `docs/codex/skills.md`
- `docs/architecture/modular-architecture-v2.md`
- `docs/features/mcp.md`
- `README.md`
