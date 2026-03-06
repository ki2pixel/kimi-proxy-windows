---
name: json-query-expert
description: Expert en manipulation de données JSON massives via le pattern "Sniper". Utiliser ce skill pour extraire ou modifier des zones JSON ciblées sans charger des fichiers volumineux entièrement. Ne pas l’utiliser pour du refactoring généraliste hors JSON.
license: Repository license (see project root)
---

# JSON Query Expert (Kimi Proxy)

## Purpose
Interroger et modifier des JSON volumineux de manière précise, traçable et token-efficient.

## When to use
- Analyse de gros JSON (config, exports, datasets).
- Recherche d’une clé/valeur précise via JSONPath.
- Modification locale d’un bloc JSON identifié.

## When NOT to use
- Fichiers non JSON.
- Refonte métier multi-couches sans besoin JSON dominant.
- Édition “à l’aveugle” sans localisation préalable.

## Inputs required
- Chemin fichier JSON.
- Cible (JSONPath, clé, valeur).
- Résultat attendu (lecture, patch, suppression, ajout).

## Workflow
1. Valider que le fichier est bien JSON exploitable.
2. Localiser la cible avec JSONPath/scan de clés.
3. Extraire uniquement le sous-ensemble nécessaire.
4. Appliquer l’édition minimale sur la zone ciblée.
5. Revalider structure JSON et impact fonctionnel.

## Output contract
- Résultat JSON localisé et vérifiable.
- Modifications limitées au scope demandé.
- Indication claire des clés touchées.

## Guardrails
- Ne pas charger entièrement les fichiers JSON massifs sans nécessité.
- Pas de fuite de secrets (`api_key`, tokens, credentials).
- Respect workspace MCP autorisé.
- Conserver cohérence config Kimi Proxy (providers/models/routing).

## Exemples minimaux
- « Extraire `$.providers["managed:kimi-code"]` dans `config.toml` converti JSON ».
- « Modifier uniquement une valeur de timeout dans un gros JSON d’export ».

## Kimi Proxy references
- `.clinerules/codingstandards.md`
- `docs/codex/skills.md`
- `README.md`
