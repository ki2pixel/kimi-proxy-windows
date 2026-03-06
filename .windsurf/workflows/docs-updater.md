---
description: Docs Updater, Windows PowerShell 5.1, MCP/ripgrep, cloc/radon, quality context
---

# Workflow: Docs Updater — Windows 11 / PowerShell 5.1

**TL;DR**: Ce workflow met à jour la documentation Kimi Proxy depuis Windows 11 sans supposer `bash` ni `pwsh`. Les audits locaux passent par PowerShell 5.1, les inspections de contenu restent sur MCP fast-filesystem et ripgrep, et les dépendances facultatives (`cloc`, `radon`) sont vérifiées avant usage puis seulement proposées à l'installation.

Vous êtes sur Windows. Le workflow historique cassait précisément au moment où l'audit devait être fiable: options GNU non supportées par `tree.com`, chemins Memory Bank Linux, et dépendances CLI implicites absentes sur une installation Windows standard. Cette version conserve les protocoles MCP déjà portables, remplace les hypothèses Linux par des équivalents PowerShell robustes, et impose un pré-flight non interactif avant tout audit.

## La Règle d'Or

**MCP et ripgrep restent la couche d'inspection portable; PowerShell 5.1 devient la couche d'audit local Windows-native.**

## ❌ Ce workflow ne suppose plus

- `bash`
- `pwsh`
- `ls`
- `tree -L` ou `tree -I`
- des chemins `/home/...`
- la présence implicite de `cloc` ou `radon`

## ✅ Ce workflow suppose désormais

- Windows PowerShell 5.1+
- Chemins absolus Windows pour la Memory Bank
- MCP fast-filesystem pour les fichiers projet et Memory Bank
- MCP ripgrep pour la recherche de patterns
- `python` et `pip` disponibles avant audit `radon`
- Un mode non interactif, idempotent, sans alias PowerShell

## 🚨 Protocoles critiques

1. **Outils autorisés**: MCP fast-filesystem (`fast_read_file`, `fast_list_directory`, `fast_search_files`, `edit_file`), MCP ripgrep (`search`, `advanced-search`, `count-matches`), et Windows PowerShell 5.1+ limité aux audits système (`Get-ChildItem`, `tree.com`, `cloc`, `python -m radon`).
2. **Contexte**: Initialiser le contexte en appelant `fast_read_file` sur `C:\Users\kidpixel\Documents\kimi-proxy\memory-bank\activeContext.md`. Ne lire les autres fichiers de la Memory Bank qu'en cas de divergence majeure détectée pendant le diagnostic.
3. **Source de vérité**: Code > Documentation existante > Memory Bank.
4. **Sécurité Memory Bank**: Utiliser uniquement fast-filesystem avec des chemins absolus Windows dans `C:\Users\kidpixel\Documents\kimi-proxy\memory-bank\`.
5. **Dépendances manquantes**: Toute installation système doit être proposée en plan, jamais exécutée automatiquement.
6. **PowerShell strict**: Pas d'alias (`gci`, `ls`, `cat`, `?`, `%` interdits dans le protocole final). Utiliser `try/catch`, `-ErrorAction Stop`, `Write-Verbose`, paramètres explicites et `Write-Output` ou objets structurés.

## Étape 0 — Pré-flight Windows obligatoire

L'audit ne commence pas tant que l'état de l'environnement Windows n'est pas explicite.

### ✅ Fonction de validation recommandée

```powershell
function Get-KimiWindowsAuditStatus {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string]$RepositoryRoot
    )

    $ErrorActionPreference = 'Stop'

    try {
        $resolvedRoot = (Resolve-Path -Path $RepositoryRoot -ErrorAction Stop).Path
        Write-Verbose "Audit root resolved to $resolvedRoot"

        $toolStatus = [ordered]@{
            PowerShell = $PSVersionTable.PSVersion.ToString()
            Tree       = [bool](Get-Command tree -ErrorAction SilentlyContinue)
            Python     = [bool](Get-Command python -ErrorAction SilentlyContinue)
            Pip        = [bool](Get-Command pip -ErrorAction SilentlyContinue)
            Cloc       = [bool](Get-Command cloc -ErrorAction SilentlyContinue)
            Pwsh       = [bool](Get-Command pwsh -ErrorAction SilentlyContinue)
        }

        $radonInstalled = $false
        if ($toolStatus.Python -and $toolStatus.Pip) {
            & python -m pip show radon *> $null
            if ($LASTEXITCODE -eq 0) {
                $radonInstalled = $true
            }
        }

        Write-Output ([PSCustomObject]@{
            RepositoryRoot  = $resolvedRoot
            ToolStatus      = $toolStatus
            RadonInstalled  = $radonInstalled
            ExecutionPolicy = (Get-ExecutionPolicy).ToString()
        })
    }
    catch {
        throw "Pré-flight Windows impossible: $($_.Exception.Message)"
    }
}

Get-KimiWindowsAuditStatus -RepositoryRoot 'C:\Users\kidpixel\Documents\kimi-proxy' -Verbose
```

### Interprétation attendue

- Si `Cloc = False`: proposer `choco install cloc -y`.
- Si `RadonInstalled = False`: proposer `python -m pip install radon`.
- Si `ExecutionPolicy = Restricted`: proposer `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- Si `Pwsh = False`: noter que **Windows PowerShell 5.1 suffit**, donc ce n'est pas bloquant.
- Si `Python = False` ou `Pip = False`: bloquer uniquement l'audit `radon`; poursuivre le reste du workflow avec mention explicite.

## Étape 1 — Audit structurel et métrique

Lancer les audits en ignorant les dossiers de données et en ciblant le cœur applicatif selon l'architecture 5 couches.

### 1. Cartographie structurelle

`tree.com` existe sous Windows, mais **ne supporte pas nativement les options GNU `-L` et `-I`**. Il peut servir à un aperçu brut, mais il ne doit pas être la base principale d'une cartographie filtrée.

### ❌ Ancienne logique fragile

```bash
bash "tree -L 3 -I '__pycache__|venv|node_modules|.git|*.db|*.backup|logs|debug|assets|*_output|test*|mcp|shrimp_data|.shrimp_task_manager'"
```

### ✅ Remplacement Windows recommandé

```powershell
function Get-KimiFilteredTree {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string]$RootPath,

        [Parameter()]
        [ValidateRange(1, 10)]
        [int]$MaxDepth = 3
    )

    $ErrorActionPreference = 'Stop'

    try {
        $resolvedRoot = (Resolve-Path -Path $RootPath -ErrorAction Stop).Path
        $excludedNames = @(
            '__pycache__',
            'venv',
            'node_modules',
            '.git',
            'logs',
            'debug',
            'assets',
            'mcp',
            'shrimp_data',
            '.shrimp_task_manager'
        )

        Get-ChildItem -Path $resolvedRoot -Directory -Recurse -Force -ErrorAction Stop |
            Where-Object {
                $relativePath = $_.FullName.Substring($resolvedRoot.Length).TrimStart('\')
                $depth = if ([string]::IsNullOrWhiteSpace($relativePath)) { 0 } else { ($relativePath -split '\\').Count }
                $isExcludedName = $excludedNames -contains $_.Name
                $isExcludedPath = $_.FullName -match '\\(test[^\\]*|[^\\]*_output)(\\|$)' -or
                    $_.FullName -match '\.(db|backup)$'

                (-not $isExcludedName) -and (-not $isExcludedPath) -and $depth -le $MaxDepth
            } |
            Select-Object FullName
    }
    catch {
        throw "Cartographie Windows impossible: $($_.Exception.Message)"
    }
}

$sourceRoot = Join-Path -Path 'C:\Users\kidpixel\Documents\kimi-proxy' -ChildPath 'src'
Get-KimiFilteredTree -RootPath $sourceRoot -MaxDepth 3 -Verbose
```

**But**: Visualiser l'architecture `src\kimi_proxy\{api,services,features,proxy,core}` sans dépendre d'options GNU absentes.

### 2. Volumétrie code

```powershell
if (Get-Command cloc -ErrorAction SilentlyContinue) {
    & cloc 'src\kimi_proxy' --md --exclude-dir=__pycache__,tests,mcp,shrimp_data,.shrimp_task_manager
}
else {
    Write-Output 'cloc absent: proposer choco install cloc -y avant audit volumétrique complet.'
}
```

**But**: Quantifier le code réel par couche.

### 3. Complexité cyclomatique

```powershell
& python -m pip show radon *> $null
if ($LASTEXITCODE -eq 0) {
    & python -m radon cc 'src\kimi_proxy' -a -nc --min C
}
else {
    Write-Output 'radon absent: proposer python -m pip install radon avant audit de complexité.'
}
```

**But**: Repérer les points chauds dans les couches critiques.

**Règle**: Si score > 10 (C), la documentation doit expliquer la logique interne et les décisions de traitement d'erreur.

### 4. Analyse API

- Utiliser MCP ripgrep `advanced-search` avec le pattern `@app\.(get|post|put|delete|patch)` sur `src/kimi_proxy/api`.
- **But**: Détecter tous les endpoints et vérifier leur présence dans `docs/api/`.

### 5. Analyse frontend

- Utiliser MCP ripgrep `advanced-search` avec le pattern `class.*\{|function.*\(|const.*=.*\(` sur `static/js/modules`.
- Utiliser MCP ripgrep `advanced-search` avec le pattern `<.*id=|class=` sur `static`.
- **But**: Vérifier la cohérence entre modules UI, HTML et documentation `docs/features/`.

### 6. Analyse base de données

- Utiliser MCP fast-filesystem `fast_list_directory` sur `C:\Users\kidpixel\Documents\kimi-proxy\src\kimi_proxy\core`.
- Utiliser MCP ripgrep `advanced-search` avec le pattern `CREATE TABLE|ALTER TABLE|INSERT INTO|UPDATE|DELETE FROM` sur `src/kimi_proxy/core`.
- **But**: Détecter les changements de schéma et vérifier leur documentation dans `docs/core/`.

### 7. Analyse configuration

- Utiliser MCP ripgrep `advanced-search` avec le pattern `providers\[|models\[|config\.` sur `src/kimi_proxy`.
- **But**: Détecter les nouveaux providers ou paramètres et vérifier leur documentation fonctionnelle.

### 8. Analyse métriques et monitoring

- Utiliser MCP ripgrep `advanced-search` avec le pattern `METRICS|LOGGING|ALERT` sur `src/kimi_proxy`.
- **But**: Détecter les nouveaux mécanismes de monitoring et vérifier leur couverture documentaire.

## Tableau de référence — audits Windows

| Audit | Remplacement Windows recommandé | Dépendance | Limite connue |
| --- | --- | --- | --- |
| Cartographie | `Get-KimiFilteredTree` | PowerShell 5.1 | `tree.com` ne remplace pas GNU `tree -L/-I` |
| Volumétrie | `cloc 'src\\kimi_proxy' --md --exclude-dir=...` | `cloc` | Installation externe possible via Chocolatey |
| Complexité | `python -m radon cc 'src\\kimi_proxy' -a -nc --min C` | `python`, `pip`, `radon` | `radon` doit être présent dans l'environnement Python |
| Listing simple | `Get-ChildItem -Path ...` | PowerShell 5.1 | Aucun alias dans le protocole final |

## Étape 2 — Analyse comparative Code vs Docs

Générer un plan de modification avant toute écriture.

```markdown
## 📝 Plan de mise à jour documentation

### Audit métrique
- **Cible**: `src/kimi_proxy/services/websocket_manager.py`
- **Métriques**: 320 LOC, complexité max C (11), patterns de gestion d'erreur explicités.

### Modifications proposées
#### 📄 docs/development/services/websocket-manager.md
- **Type**: [API | Services | Features | Proxy | Core]
- **Diagnostic**: [Obsolète | Incomplet | Manquant]
- **Correction**:
  ```markdown
  [Contenu proposé respectant les patterns système Kimi Proxy]
  ```
```

## Étape 3 — Application et finalisation

1. **Exécution**: Après validation, utiliser `edit_file` ou `apply_patch` dans le repo.
2. **Mise à jour Memory Bank**:
   - Utiliser exclusivement des chemins absolus Windows sous `C:\Users\kidpixel\Documents\kimi-proxy\memory-bank\`.
   - Ajouter des timestamps `[YYYY-MM-DD HH:MM:SS]`.

## Sous-protocole rédaction — application du skill documentation

### 3.1 Point d'entrée explicite

- **Mode rédaction**: Déclenché après validation du plan.
- **Lecture obligatoire**: `.cline/skills/documentation/SKILL.md`.
- **Modèle à appliquer**: Article deep-dive, README, fiche technique ou note d'architecture selon le plan.

### 3.2 Checkpoints obligatoires

**Avant rédaction**:

- [ ] TL;DR présent
- [ ] Problem-first opening présent

**Pendant rédaction**:

- [ ] Comparaison ❌/✅ si un choix technique doit être clarifié
- [ ] Trade-offs table si plusieurs approches coexistent
- [ ] Golden Rule si le document formalise une décision récurrente
- [ ] Artefacts AI évités
- [ ] Architecture 5 couches explicitement respectée

**Après rédaction**:

- [ ] Vérification ponctuation et suppression des artefacts ` - ` en prose
- [ ] Vérification des chemins Windows et des commandes non interactives
- [ ] Cohérence Code > Docs > Memory Bank

### 3.3 Traçabilité

Dans la proposition de mise à jour, ajouter:

```markdown
#### Application du skill documentation
- **Modèle**: [Article deep-dive | README | Technique]
- **Éléments appliqués**: TL;DR ✔, Problem-First ✔, Comparaison ✔, Trade-offs ✔, Golden Rule ✔
- **Patterns système**: [Architecture 5 couches, gestion d'erreur, DI, sécurité Memory Bank]
```

### 3.4 Hook d'automatisation

- **Validation Git**: mentionner le guidage par `.windsurf\skills\documentation\SKILL.md` dans le résumé de changement.
- **Blocage**: le workflow ne se termine pas si le pré-flight Windows n'a pas été exécuté ou si les checkpoints rédactionnels restent ouverts.
- **Audit trail**: chaque proposition de mise à jour doit mentionner les commandes Windows réellement utilisées.
- **Memory Bank sync**: mise à jour ciblée de `progress.md` et `decisionLog.md` si le workflow a conduit à une décision durable.

## Trade-offs

| Choix | Avantage | Coût |
| --- | --- | --- |
| PowerShell 5.1 au lieu de `bash` | Compatible Windows 11 par défaut | Les commandes GNU doivent être réécrites |
| `Get-ChildItem` filtré au lieu de `tree -L/-I` | Contrôle précis du bruit | Snippet plus long qu'une commande GNU |
| `python -m radon` au lieu de `radon` nu | Plus fiable avec l'interpréteur actif | Dépend de `python` et `pip` |
| MCP ripgrep conservé | Shell-independent et cohérent avec le repo | Nécessite de rester aligné avec les noms d'outils MCP |
