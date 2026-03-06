---
name: fast-filesystem-ops
description: Utiliser ce skill pour faire des lectures/éditions chirurgicales dans le repo Kimi Proxy avec un budget de contexte réduit. Ne pas l’utiliser pour une refonte fonctionnelle complète qui exige une vue globale de tout le code.
license: Repository license (see project root)
---

# Fast Filesystem Ops (Kimi Proxy)

## Purpose
Exécuter des opérations fichiers précises, sûres et économes en contexte/token.

## When to use
- Recherche ciblée d’implémentations (routes, services, helpers).
- Modifications locales sur 1 à quelques fichiers.
- Revue de gros fichiers sans chargement complet.
- Batch de corrections chirurgicales répétitives.

## When NOT to use
- Conception d’architecture globale.
- Migration massive sans stratégie préalable.
- Analyse produit/documentation sans besoin d’édition code.

## Inputs required
- Cible fonctionnelle précise (fichier, motif, symbole).
- Type de modification attendue.
- Contraintes de sûreté (zones interdites, fichiers sensibles).

## Workflow
1. Localiser via recherche regex/symboles.
2. Lire uniquement le contexte minimal nécessaire.
3. Appliquer une édition atomique et vérifiable.
4. Contrôler les impacts croisés (imports/usages).
5. Vérifier rapidement (lint/test ciblé si disponible).

## Output contract
- Diff minimal, lisible, sans bruit.
- Aucun changement hors périmètre demandé.
- Liste claire des fichiers touchés.

## Guardrails
- Respect architecture 5 couches Kimi Proxy.
- Ne pas toucher `.env`, secrets, ou chemins hors workspace.
- Préserver compatibilité async/await et typing strict.
- Ne pas introduire de dépendances synchrones bloquantes.

## Exemples minimaux
- « Remplacer une logique de mapping dans un module précis ».
- « Corriger un import cassé sur 3 fichiers ciblés ».

## Kimi Proxy references
- `.clinerules/codingstandards.md`
- `docs/codex/skills.md`
- `docs/architecture/modular-architecture-v2.md`
- `README.md`
