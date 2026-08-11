@echo off
REM Démarrage automatique du Kimi Proxy et des serveurs MCP au démarrage de Windows
powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File "%USERPROFILE%\Documents\kimi-proxy\bin\kimi-proxy.ps1" start
