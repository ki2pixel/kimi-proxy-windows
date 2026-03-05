Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$VenvPython = Join-Path $ProjectDir "venv\Scripts\python.exe"

function Write-Info([string]$Message) { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Ok([string]$Message) { Write-Host "[OK]   $Message" -ForegroundColor Green }
function Write-Err([string]$Message) { Write-Host "[ERR]  $Message" -ForegroundColor Red }

if (-not (Test-Path (Join-Path $ProjectDir "src\kimi_proxy\features\mcp\client.py"))) {
    Write-Err "Invalid project root: src/kimi_proxy/features/mcp/client.py not found"
    exit 1
}

if (-not (Test-Path $VenvPython)) {
    Write-Err "Missing virtual environment: $VenvPython"
    exit 1
}

Write-Info "Running MCP quick smoke subset (Windows)"
Write-Info "Scope: stable MCP tests aligned with current implementation"

Push-Location $ProjectDir
try {
    & $VenvPython -m pytest tests/mcp/test_mcp_qdrant.py tests/mcp/test_mcp_compression.py -v --tb=short -k "(check_status or is_available or compression_ratio_calculation or search_similar or find_redundant or cluster_memories or generate_vector_id or timeout_respected or api_key_passed_to_rpc or decompress_no_compression or decompress_zlib_failure) and not store_vector_success"
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "MCP quick smoke subset passed"
        exit 0
    }

    Write-Err "MCP quick smoke subset failed with code $LASTEXITCODE"
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
