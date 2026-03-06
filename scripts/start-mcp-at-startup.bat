@echo off
REM Démarrage automatique des serveurs MCP Kimi Proxy au démarrage de Windows
powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Users\kidpixel\Documents\kimi-proxy\scripts\start-mcp-servers.ps1" start
