# Audit Backend Kimi Proxy

**TL;DR** : Audit terminé, sans modification de code. 
Le backend présente une base fonctionnelle solide (FastAPI structuré, proxy/streaming, intégration MCP, couverture de tests utile sur proxy/MCP/streaming/Cline),
mais avec plusieurs écarts de production significatifs : architecture 5 couches contournée par des imports directs API→Core/Services/Features/Proxy, état global/singletons (`_manager`, `_limiter`, `_config_cache`, `_log_watcher`),
SQLite synchrone dans des chemins async, contrats API hétérogènes, observabilité majoritairement basée sur `print()`, et posture sécurité trop permissive sur certains points (CORS global, exposition de `original_content`/`file_path`, log de clé API tronquée).
Les risques les plus critiques concernent 1) sécurité/exposition de données, 2) contention et blocage event loop via SQLite sync, 3) duplications et incohérences de routes/handlers, 4) diagnostics insuffisants en cas d’incident, 5) couverture de tests lacunaire sur endpoints sensibles et opérations de maintenance DB.

## Risques Critiques

### Top 5 Risques

J'ai identifié ces cinq risques majeurs après avoir passé au crible l'architecture et les implémentations :

1. **[CRITIQUE]** Exposition potentielle de données sensibles via `/api/mask/{hash}` + stockage disque en clair + CORS permissif
2. **[HAUTE]** Accès `sqlite3` synchrones dans handlers async et `VACUUM` synchrone
3. **[HAUTE]** Duplication/incohérence de surface (`/ws`, `sessions.py`, `memory.py` non monté mais handlers WS réutilisés)
4. **[HAUTE]** Observabilité faible (`print`, `except Exception`, erreurs absorbées)
5. **[MOYENNE]** Couverture de tests inégale sur endpoints sensibles et opérations de maintenance DB

## Findings Détaillés

### SEV-1 : Sécurité sanitizer/CORS/logs

Preuves : `src/kimi_proxy/main.py:48-53`, `src/kimi_proxy/api/routes/sanitizer.py:20-37`, `src/kimi_proxy/features/sanitizer/storage.py:79-113`, `src/kimi_proxy/api/routes/proxy.py:274-276`

Impact : Fuite de contenu sensible/chemins, surface cross-origin excessive

Recommandation : Restreindre CORS, supprimer `original_content` de l'API, éviter tout log de secret

Effort : M

### SEV-2 : SQLite synchrone dans chemins async

Preuves : `src/kimi_proxy/core/database.py:1-50`, `src/kimi_proxy/api/routes/sessions.py:120-180`, `src/kimi_proxy/api/routes/memory.py:21,545-699`, `src/kimi_proxy/services/websocket_manager.py:130-200`

Impact : Blocage event loop, performance dégradée, contention en charge

Recommandation : Migrer vers `aiosqlite` pour tous accès DB, implémenter pool de connexions

Effort : M

### SEV-3 : Architecture et imports

Preuves : `src/kimi_proxy/api/router.py:18,27-47`, `src/kimi_proxy/api/routes/memory.py:21,545-699`

Impact : Divergence comportementale, maintenance risquée, erreurs client

Recommandation : Unifier les surfaces et schémas d'erreur

Effort : M

### SEV-4 : Observabilité/résilience limitées

Preuves : `src/kimi_proxy/proxy/stream.py:128-161,218-249,283-289`, `src/kimi_proxy/services/websocket_manager.py:25-58`, `src/kimi_proxy/api/routes/health.py:24-82`, `src/kimi_proxy/services/rate_limiter.py:66-125`

Impact : RCA difficile, erreurs silencieuses, saturation WS/RPM moins lisible

Recommandation : Logs structurés + métriques explicites + alerting cohérent

Effort : M

### SEV-5 : Couverture de tests incomplète

Preuves positives : `tests/e2e/test_regression.py`, `tests/e2e/test_streaming_errors.py`, `tests/unit/proxy/test_stream.py`, `tests/unit/features/test_mcp_gateway.py`, `tests/integration/test_cline_api.py`, `tests/unit/test_mcp_http_server.py`

Angles morts mesurés : `/api/mask:0`, `original_content:0`, `delete_sessions_bulk:0`, `VACUUM:0`, `rate_limiter.py:0`, `/api/sanitizer/toggle:0`

Impact : Régressions probables sur sécurité/ops

Recommandation : Ajouter tests ciblés de non-régression

Effort : S/M

## Quick Wins (≤2 jours)

- Désactiver exposition `original_content`/`file_path`
- Retirer logs de clé API
- Homogénéiser erreurs HTTP
- Tester `/api/mask`/rate-limit/VACUUM/suppressions bulk

## Chantiers Structurants

- Refonte accès DB async/sérialisation
- Rationalisation des routeurs WS/API
- Suppression des singletons globaux
- Observabilité structurée

## Plan Priorisé

| Phase | Délai | Actions | Impact |
|-------|-------|---------|--------|
| J+2 | Sécurité visible + tests manquants critiques | Quick wins + tests SEV-5 | Réduction exposition données + couverture |
| J+7 | Unification contrats API/WS + instrumentation | SEV-3 + SEV-4 | Cohérence + diagnostics |
| J+30 | Refonte DB/concurrence + assainissement | SEV-2 + singletons | Performance + architecture |

## Risques Résiduels à Monitorer

- Contention SQLite
- Erreurs streaming provider
- Saturation broadcasts WS
- Appels MCP fail-open

## Score Global Backend

| Aspect | Score | Commentaire |
|--------|-------|-------------|
| Maintenabilité | 52/100 | Imports directs nombreux, singletons |
| Sécurité | 41/100 | Exposition données, logs secrets |
| Performance | 57/100 | SQLite sync, pas de pooling |
| Résilience | 54/100 | Observabilité faible, erreurs absorbées |
| Testabilité | 68/100 | Couverture utile mais angles morts critiques |