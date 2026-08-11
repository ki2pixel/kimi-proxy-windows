@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

:: ============================================================
:: Script de démarrage autonome - Kimi Proxy Server (Windows)
:: Emplacement : bin/start-proxy.bat
:: ============================================================

title Kimi Proxy Server

:: Positionnement à la racine du projet Kimi Proxy
cd /d "%~dp0\.."
set "PROJECT_DIR=%CD%"

echo ============================================================
echo                    Kimi Proxy Server
echo ============================================================
echo.

:: 1. Configuration par défaut des variables d'environnement
if "%HOST%"=="" set "HOST=127.0.0.1"
if "%PORT%"=="" set "PORT=8000"

set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONPATH=src"

:: 2. Vérification de l'environnement virtuel Python
set "VENV_PYTHON=%PROJECT_DIR%\venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo [ERREUR] Environnement virtuel introuvable dans :
    echo         "%VENV_PYTHON%"
    echo.
    echo Veuillez d'abord initialiser l'environnement virtuel venv.
    echo ============================================================
    goto ERROR_PAUSE
)

:: 3. Routine de Nettoyage Sélectif (Libération du port)
echo [INFO] Recherche et fermeture d'une éventuelle instance précédente du proxy sur le port %PORT%...

powershell -NoProfile -ExecutionPolicy Bypass -Command "$conns = Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue; if ($conns) { foreach ($c in $conns) { $pidVal = $c.OwningProcess; $proc = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $pidVal) -ErrorAction SilentlyContinue; if ($proc -and $proc.CommandLine -like '*uvicorn*' -and $proc.CommandLine -like '*kimi_proxy.main:app*') { Write-Host ('[INFO] Fermeture instance precedente Kimi Proxy (PID ' + $pidVal + ')...') -ForegroundColor Yellow; Stop-Process -Id $pidVal -Force -ErrorAction SilentlyContinue } elseif ($proc) { Write-Host ('[AVERTISSEMENT] Le port %PORT% est occupe par PID ' + $pidVal + ' (' + $proc.Name + ') - pas Kimi Proxy.') -ForegroundColor Cyan } } }; exit 0"

:: Tempo de 2 secondes pour la libération complète du socket TCP
ping 127.0.0.1 -n 3 >nul

:: 4. Démarrage du serveur uvicorn
echo [INFO] Démarrage du serveur Kimi Proxy sur http://%HOST%:%PORT% ...
echo.

"%VENV_PYTHON%" -m uvicorn kimi_proxy.main:app --host %HOST% --port %PORT% %*

if errorlevel 1 (
    echo.
    echo ============================================================
    echo [ERREUR] Le serveur Kimi Proxy s'est arreté avec le code d'erreur %ERRORLEVEL%.
    echo ============================================================
    goto ERROR_PAUSE
)

goto END

:ERROR_PAUSE
echo.
echo Appuyez sur une touche pour fermer la fenêtre...
pause >nul

:END
