# Compatibilité Windows MCP — Runbook de stabilisation

**TL;DR**: **Le cycle de stabilisation Windows finalisé le 2026-03-05 a supprimé la principale source de `fetch failed`** en imposant une séquence déterministe: proxy prêt (`/health` 200) avant démarrage/annonce MCP. Les durcissements sont centrés sur `scripts/start-mcp-servers.ps1` et `bin/kimi-proxy.ps1`, validés par smoke tests et campagne pytest étendue.

Le problème de production locale était concret: côté IDE, on commandait au serveur (menu MCP) alors que la cuisine (proxy `:8000`) n’était pas encore ouverte. Le message remontait en `fetch failed`, sans diagnostic utile.

## 1) Ce qui a cassé avant (Windows Boot-Loop Trap)

### Symptômes
- `fetch failed` côté client MCP (Continue/Cline)
- démarrage parfois "vert" dans les logs mais indisponible en pratique
- faux positifs liés à PID stale/processus non valides

### Signaux techniques observés
- proxy non prêt au moment où les helpers MCP étaient déjà lancés
- séquence de boot fragile sous Windows (ordre et timing)
- gestion process/PID insuffisamment robuste pour les redémarrages répétés

### ❌ / ✅ (incident)

❌ `fetch failed` sans piste claire  
✅ Diagnostic guidé: health endpoint, statut ports/helpers, puis restart idempotent

## 2) Ce qui a été corrigé

### Durcissement scripts PowerShell
- `scripts/start-mcp-servers.ps1`
- `bin/kimi-proxy.ps1`

### Changements opérationnels clés
- auto-démarrage proxy si nécessaire
- health-check robuste sur `http://127.0.0.1:8000/health`
- validation proxy avant d’annoncer MCP "ready"
- gestion PID/process plus sûre sous Windows (stale/invalide traité)

### Exemple A — Santé proxy
❌ Ancien pattern: lancer MCP sans vérifier que le proxy écoute réellement `:8000`.  
✅ Nouveau pattern: démarrer proxy, boucler sur `GET /health`, puis seulement démarrer/annoncer MCP prêt.

## 3) Procédure d’installation Windows fiable

Référence détaillée: [`docs/deployment/installation.md`](../deployment/installation.md)

### Séquence courte (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
.\bin\kimi-proxy.ps1 start
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health
.\scripts\start-mcp-servers.ps1 start
.\tests\run_cline_mcp_smoke.ps1
```

### Validation factuelle
- Stabilisation finalisée: **2026-03-05**
- Campagne rapide: **4 passed**
- Validation étendue MCP Windows: **173 passed, 13 skipped**

### Exemple C — Runbook démarrage
❌ Enchaîner des commandes manuelles non déterministes.  
✅ Procédure idempotente PowerShell + checklists post-boot.

## 4) Troubleshooting guidé

### Arbre de diagnostic (rapide)

1. `fetch failed` ?
   - Vérifier `/health`
2. `/health` ≠ 200 ?
   - Redémarrer proxy
3. `/health` = 200 mais MCP KO ?
   - Vérifier statut helpers MCP
4. Port occupé / timeout ?
   - restart propre + revalidation

### Commandes concrètes

```powershell
# Santé proxy
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health

# État MCP
.\scripts\start-mcp-servers.ps1 status

# Restart helpers MCP
.\scripts\start-mcp-servers.ps1 restart

# Restart proxy
.\bin\kimi-proxy.ps1 restart
```

### Exemple B — Incident `fetch failed`
❌ Message vague `fetch failed` sans diagnostic actionnable.  
✅ Message guidé: vérifier `http://127.0.0.1:8000/health`, statut ports MCP, puis script `restart`.

## 5) Compatibilité MCP côté IDE (Cline/Continue)

### Ce qui est confirmé
- route MCP via proxy local stable
- helpers MCP opérationnels:
  - `sequential-thinking`
  - `fast-filesystem`
  - `json-query`

### Vérification pratique
1. Démarrer proxy
2. Confirmer `/health` 200
3. Démarrer MCP helpers
4. Lancer smoke test Cline MCP

## 6) Trade-offs et limites

### Tableau 1 — Windows vs Linux

| Sujet | Windows (PowerShell) | Linux (shell) |
| --- | --- | --- |
| Ergonomie scripts | Bonne pour équipes Windows natives | Bonne pour environnements CI/Linux existants |
| Process management | Plus sensible aux PID stale au départ, désormais durci | Historiquement plus homogène (`ps/kill`) |
| Observabilité locale | Bonne via health + status scripts | Bonne via tooling shell standard |

### Tableau 2 — Simplicité vs robustesse (boot)

| Choix | Gain | Coût |
| --- | --- | --- |
| Auto-start + health-check strict | Moins d’incidents `fetch failed` | Légère attente de readiness |
| Contrôle manuel pur | Diagnostic fin ponctuel | Erreurs de séquencement plus fréquentes |

### Limites connues
- Le runbook couvre la production locale Windows; la CI multi-OS reste un axe de surveillance continue.
- Les statuts green doivent toujours être corrélés à `/health = 200`; un statut process seul n’est pas suffisant.

## Architecture et périmètre

- Architecture 5 couches: `API ← Services ← Features ← Proxy ← Core`
- Stack: FastAPI + HTTPX + SQLite + WebSocket
- Taille: ~10k+ LOC Python
- Port pivot de fiabilité: `:8000`

## Golden Rule exploitation Windows

**Dans ce projet, un process “up” ne vaut rien sans health “200”: d’abord `/health`, ensuite MCP, toujours.**
