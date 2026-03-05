@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "SHRIMP_DIST=%PROJECT_DIR%\mcp\mcp-shrimp-task-manager-main\dist\index.js"

if not exist "%SHRIMP_DIST%" (
  echo [ERR] shrimp-task-manager dist not found: "%SHRIMP_DIST%" 1>&2
  exit /b 1
)

node "%SHRIMP_DIST%"
