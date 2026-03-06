---
name: powershell
description: PowerShell scripting toolkit for Windows automation. Utiliser ce skill pour automatiser des tâches Windows (services, processus, fichiers, diagnostics Kimi Proxy). Ne pas l’utiliser pour des modifications applicatives Python/JS sans besoin d’automatisation système.
license: Repository license (see project root)
---

# PowerShell (Kimi Proxy Context)

## Purpose
Fournir des scripts et commandes PowerShell robustes pour l’exploitation Windows de Kimi Proxy.

## When to use
- Démarrage/arrêt/diagnostic des services scripts Kimi Proxy.
- Automatisation Windows (processus, ports, tâches planifiées, logs).
- Vérifications environnement local (PS, PATH, réseau, permissions).

## When NOT to use
- Implémentation logique backend/frontend Kimi Proxy.
- Refactor de code Python/JS sans enjeu système Windows.
- Opérations destructives non validées explicitement.

## Inputs required
- Objectif opérationnel (diagnostic, remediation, automation).
- Environnement ciblé (Windows 11, PowerShell version).
- Ressources touchées (fichiers, ports, services/processus).
- Contraintes sécurité (chemins autorisés, secrets).

## Workflow
1. Vérifier prérequis (version PS, droits, contexte repo).
2. Formuler commandes non interactives et idempotentes.
3. Prévoir gestion d’erreur explicite (`try/catch`, codes de sortie).
4. Exécuter en dry-run si impact potentiellement destructif.
5. Appliquer puis valider l’état final attendu.

## Output contract
- Commandes/scripts PowerShell exécutables et commentés.
- Effets attendus clairement décrits.
- Rollback ou mitigation mentionné en cas d’échec.

## Guardrails
- `policy.allow_implicit_invocation=false` (invocation explicite préférée).
- Ne jamais exposer des secrets (`.env`, clés API).
- Pas d’opération destructive sans confirmation explicite.
- Restreindre aux chemins autorisés du workspace.

## Exemples minimaux
- « Diagnostiquer pourquoi `start-mcp-servers.ps1` n’expose pas les endpoints MCP ».
- « Script PowerShell pour vérifier ports 8000-8005 et PIDs associés ».

## Kimi Proxy references
- `.clinerules/codingstandards.md`
- `docs/codex/skills.md`
- `docs/features/mcp.md`
- `README.md`
