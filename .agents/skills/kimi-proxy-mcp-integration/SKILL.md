---
name: kimi-proxy-mcp-integration
description: Comprehensive MCP integration for Kimi Proxy Dashboard (phases 2-5, gateway, orchestration outils). Utiliser ce skill pour intégrer, diagnostiquer ou faire évoluer les flux MCP. Ne pas l’utiliser pour des changements frontend isolés sans impact MCP.
license: Repository license (see project root)
---

# Kimi Proxy MCP Integration

## Purpose
Concevoir et sécuriser l’intégration MCP de Kimi Proxy (serveurs, gateway, orchestration, mémoire).

## When to use
- Ajout/évolution d’un serveur MCP dans Kimi Proxy.
- Diagnostic d’échec d’orchestration MCP (gateway, bridge, tools).
- Mise en cohérence des phases MCP 2→5.
- Intégration mémoire/recherche sémantique orientée MCP.

## When NOT to use
- Ajustement purement UI sans impact MCP.
- Refactor backend hors flux MCP.
- Tâches de planning sans implémentation d’intégration.

## Inputs required
- Serveur(s) MCP visés et objectif métier.
- Contrats d’appel (tools/resources) attendus.
- Configuration runtime/gateway disponible.
- Logs d’erreur et scénario de reproduction.

## Workflow
1. Identifier la phase MCP concernée et le flux bout-en-bout.
2. Vérifier connectivité serveur, transport et health checks.
3. Valider contrats tool/resource et payloads JSON-RPC.
4. Contrôler sécurité workspace et filtrage entrées.
5. Implémenter adaptation minimale côté Kimi Proxy.
6. Tester scénario nominal + erreurs fréquentes.
7. Documenter décisions de routage/orchestration.

## Output contract
- Intégration MCP fonctionnelle et vérifiable.
- Liste explicite des tools dépendants.
- Gestion d’erreur claire (pas de silent fail).
- Compatibilité gateway/bridge confirmée.

## Guardrails
- Respect architecture 5 couches Kimi Proxy.
- Validation workspace MCP obligatoire.
- Interdiction d’exfiltrer secrets/credentials.
- Aucune dépendance sync bloquante dans le chemin critique.
- Préserver robustesse JSON-RPC et observabilité.

## Exemples minimaux
- « Intégrer un nouveau tool MCP avec fallback via gateway ».
- « Diagnostiquer un échec `tools/call` entre proxy et serveur MCP ».

## Kimi Proxy references
- `.clinerules/codingstandards.md`
- `docs/codex/skills.md`
- `docs/features/mcp.md`
- `docs/architecture/modular-architecture-v2.md`
- `README.md`
