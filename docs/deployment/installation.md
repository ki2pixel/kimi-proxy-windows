# Installation Windows (fiable) — Kimi Proxy Dashboard

**TL;DR**: **Sur Windows, la méthode fiable est: démarrer le proxy, attendre `GET /health = 200`, puis lancer les helpers MCP**. Depuis la stabilisation du 2026-03-05, cette séquence élimine le piège principal derrière les `fetch failed`.

Le vrai problème que les équipes ont subi n’était pas l’installation Python en soi; c’était une séquence de boot fragile. En clair, les "plats" MCP sortaient de cuisine avant que la cuisine (proxy `:8000`) soit réellement ouverte.

## 1) Prérequis Windows

- Windows 10/11 avec PowerShell 5.1+ ou PowerShell 7+
- Python 3.10+
- Git
- Droits d’exécution scripts PowerShell pour la session

### Vérification rapide

```powershell
python --version
git --version
$PSVersionTable.PSVersion
```

### Politique PowerShell (session locale)

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

> Cette commande ne modifie pas la policy globale machine; elle s’applique à la session courante.

## 2) Installation pas à pas (PowerShell)

Depuis la racine du dépôt:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 3) Démarrage standard + vérification santé

### Étape A — Démarrer le proxy

```powershell
.\bin\kimi-proxy.ps1 start
```

### Étape B — Vérifier que la cuisine est ouverte (`/health`)

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health | Select-Object -ExpandProperty StatusCode
```

Attendu: `200`

### Étape C — Démarrer les helpers MCP

```powershell
.\scripts\start-mcp-servers.ps1 start
```

### Étape D — Vérifier les statuts MCP

```powershell
.\scripts\start-mcp-servers.ps1 status
```

Compatibilité validée côté Cline/Continue avec:
- `sequential-thinking`
- `fast-filesystem`
- `json-query`

## 4) Smoke tests et validation

### Smoke Cline MCP

```powershell
.\tests\run_cline_mcp_smoke.ps1
```

### Campagne rapide

Ordre de grandeur attendu (contexte produit): **4 passed**.

### Validation étendue MCP Windows (audit interne)

Ordre de grandeur documenté: **173 passed, 13 skipped**.

## 5) Check-list de validation finale

- [ ] `venv` actif
- [ ] `bin/kimi-proxy.ps1 start` exécuté sans erreur
- [ ] `GET http://127.0.0.1:8000/health` retourne `200`
- [ ] `scripts/start-mcp-servers.ps1 start` exécuté
- [ ] `scripts/start-mcp-servers.ps1 status` indique des services actifs
- [ ] smoke test Cline MCP passe

## 6) Erreurs fréquentes (❌ / ✅)

### Exemple A — Santé proxy
❌ Ancien pattern: lancer les serveurs MCP sans vérifier que le proxy écoute réellement `:8000`.  
✅ Nouveau pattern: démarrer proxy, boucler sur `GET /health`, puis seulement démarrer/annoncer MCP prêt.

### Exemple B — Incident `fetch failed`
❌ Message vague `fetch failed` sans diagnostic actionnable.  
✅ Message guidé: vérifier `http://127.0.0.1:8000/health`, statut ports MCP, puis script `restart`.

### Exemple C — Runbook démarrage
❌ Enchaîner des commandes manuelles non déterministes.  
✅ Procédure idempotente PowerShell + checklists post-boot.

## 7) Commandes de redémarrage propre

```powershell
.\scripts\start-mcp-servers.ps1 restart
```

Si nécessaire:

```powershell
.\bin\kimi-proxy.ps1 restart
```

## 8) Trade-offs (installation/exploitation locale)

| Choix | Avantage | Inconvénient |
| --- | --- | --- |
| Auto-start proxy + health-check | Réduit fortement les `fetch failed` liés au boot | Légère latence au démarrage (attente health) |
| Démarrage entièrement manuel | Contrôle fin pour debug | Plus d’erreurs humaines de séquencement |

## Golden Rule

**Sous Windows, considère le système prêt uniquement après `http://127.0.0.1:8000/health = 200`.**
