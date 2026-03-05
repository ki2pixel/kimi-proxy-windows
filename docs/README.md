# Documentation — Kimi Proxy Dashboard

**TL;DR**: **Si vous êtes sur Windows, commencez ici: la compatibilité MCP locale est stabilisée (2026-03-05) avec auto-start proxy, health-check `:8000` et runbook `fetch failed`**. Ensuite seulement, déroulez le reste de la doc.

Le point douloureux n’était pas "où est la doc", mais "quelle doc suivre quand ça casse en local Windows". Cette page remet l’ordre de lecture dans le bon sens: d’abord la fiabilité de boot, ensuite l’exploration fonctionnelle.

## Compatibilité Windows (priorité)

1. **Installation Windows fiable**  
   [`docs/deployment/installation.md`](deployment/installation.md)
2. **Runbook Windows + troubleshooting MCP**  
   [`docs/dev/windows-compatibility.md`](dev/windows-compatibility.md)

### Ce que vous y trouverez

❌ Ancien parcours: docs généralistes d’abord, diagnostic `fetch failed` en dernier.  
✅ Nouveau parcours: installation PowerShell déterministe + health-check d’abord, puis diagnostic guidé.

## Route de lecture recommandée

### Parcours rapide (mainteneur/dev Windows)
1. Racine: [`README.md`](../README.md) (mini guide 5 minutes)
2. Installation: [`deployment/installation.md`](deployment/installation.md)
3. Troubleshooting: [`dev/windows-compatibility.md`](dev/windows-compatibility.md)

### Parcours architecture
1. [`architecture/README.md`](architecture/README.md)
2. [`architecture/modular-architecture-v2.md`](architecture/modular-architecture-v2.md)

### Parcours fonctionnalités
1. [`features/README.md`](features/README.md)
2. [`features/mcp.md`](features/mcp.md)

## Repères techniques (contexte projet)

- Architecture 5 couches: `API ← Services ← Features ← Proxy ← Core`
- Stack: FastAPI + HTTPX + SQLite + WebSocket
- Taille code: ~10k+ LOC Python
- Port de santé opérationnelle: `http://127.0.0.1:8000/health`

## Trade-off de lecture doc

| Approche | Avantage | Limite |
| --- | --- | --- |
| Quickstart → Install → Troubleshooting | Résout vite les incidents `fetch failed` | Moins de profondeur conceptuelle immédiate |
| Architecture d’abord | Compréhension système globale | Risque de retarder la résolution d’un incident local |

## Golden Rule

**Sous Windows, la bonne documentation commence par la santé runtime (`/health`) avant la théorie.**
