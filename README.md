# Kimi Proxy Dashboard

**TL;DR**: **Depuis la session de stabilisation Windows du 2026-03-05, Kimi Proxy Dashboard est exploitable de façon fiable en local Windows pour Continue/Cline avec MCP**. Le correctif clé vise les `fetch failed` via durcissement PowerShell (`scripts/start-mcp-servers.ps1`, `bin/kimi-proxy.ps1`), auto-démarrage proxy, health-check robuste sur `http://127.0.0.1:8000/health`, puis validation smoke + pytest.

Le problème réel n’était pas "MCP ne marche pas", c’était un **démarrage non déterministe**: les helpers MCP répondaient alors que le proxy n’était pas encore prêt, ou pire, un PID stale faisait croire que tout allait bien. Résultat côté IDE: `fetch failed` sans diagnostic exploitable.

## Windows est maintenant supporté en pratique

### Ce qui cassait avant (Boot-Loop Trap)

❌ MCP lancé avant la disponibilité réelle du proxy `:8000`  
❌ PID/processus incohérents sous Windows (stale PID, état faux positif)  
❌ Message `fetch failed` générique, sans chemin de résolution

### Ce qui est stabilisé

✅ Durcissement de `scripts/start-mcp-servers.ps1` et `bin/kimi-proxy.ps1`  
✅ Auto-démarrage proxy avant annonce "MCP prêt"  
✅ Boucle de vérification `GET /health` sur `http://127.0.0.1:8000/health`  
✅ Compatibilité Cline confirmée avec les helpers MCP:
- `sequential-thinking`
- `fast-filesystem`
- `json-query`

### Validation factuelle

- Session de stabilisation Windows finalisée le **2026-03-05**.
- Campagne rapide validée: **4 passed** (smoke produit).
- Validation étendue MCP Windows documentée: **173 passed, 13 skipped** (audit interne).

## Mini guide 5 minutes (Windows)

> Analogie fil rouge: le proxy est la cuisine, les endpoints sont le menu, et `/health` est le maître d’hôtel qui confirme que la cuisine sert vraiment.

### 1) Installer

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2) Démarrer le proxy

```powershell
.\bin\kimi-proxy.ps1 start
```

### 3) Vérifier la santé

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health | Select-Object -ExpandProperty StatusCode
```

Attendu: `200`.

### 4) Démarrer les serveurs MCP

```powershell
.\scripts\start-mcp-servers.ps1 start
```

### 5) Exécuter le smoke test MCP

```powershell
.\tests\run_cline_mcp_smoke.ps1
```

## Si vous voyez `fetch failed` (3 étapes max)

### Étape 1
```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health
```

### Étape 2
```powershell
.\scripts\start-mcp-servers.ps1 status
```

### Étape 3
```powershell
.\scripts\start-mcp-servers.ps1 restart
```

## ❌ / ✅ Exemples de patterns opérationnels

### Exemple A — Santé proxy
❌ Ancien pattern: lancer les serveurs MCP sans vérifier que le proxy écoute réellement `:8000`.  
✅ Nouveau pattern: démarrer proxy, boucler sur `GET /health`, puis seulement démarrer/annoncer MCP prêt.

### Exemple B — Incident `fetch failed`
❌ Message vague `fetch failed` sans diagnostic actionnable.  
✅ Message guidé: vérifier `http://127.0.0.1:8000/health`, statut ports MCP, puis script `restart`.

### Exemple C — Runbook démarrage
❌ Enchaîner des commandes manuelles non déterministes.  
✅ Procédure idempotente PowerShell + checklists post-boot.

## Architecture et ordre de grandeur

- Architecture 5 couches: `API ← Services ← Features ← Proxy ← Core`
- Stack: **FastAPI + HTTPX + SQLite + WebSocket**
- Taille projet: **~10k+ LOC Python**
- Documentation: déjà riche dans `docs/`

## Trade-off rapide (local dev)

| Choix | Avantage | Limite |
| --- | --- | --- |
| Auto-start proxy | Réduit les erreurs de séquence au boot | Moins de contrôle manuel fin |
| Contrôle manuel strict | Observabilité pas à pas | Plus fragile en routine quotidienne |

## Docs détaillées

- Installation Windows: [`docs/deployment/installation.md`](docs/deployment/installation.md)
- Runbook Windows + RCA: [`docs/dev/windows-compatibility.md`](docs/dev/windows-compatibility.md)
- Index documentation: [`docs/README.md`](docs/README.md)

## Golden Rule

**Pas de menu MCP sans maître d’hôtel `/health`: tant que `:8000` n’est pas confirmé en 200, rien n’est "ready".**