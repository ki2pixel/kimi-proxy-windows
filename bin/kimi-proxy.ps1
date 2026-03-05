Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$VenvPython = Join-Path $ProjectDir "venv\Scripts\python.exe"
$PidFile = Join-Path $ProjectDir ".server.pid"
$LogFile = Join-Path $ProjectDir "server.log"
$ErrLogFile = Join-Path $ProjectDir "server.err.log"
$McpScript = Join-Path $ProjectDir "scripts\start-mcp-servers.ps1"

function Write-Info([string]$Message) { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Ok([string]$Message) { Write-Host "[OK]   $Message" -ForegroundColor Green }
function Write-Warn([string]$Message) { Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Err([string]$Message) { Write-Host "[ERR]  $Message" -ForegroundColor Red }

function Get-ProcessCommandLine([int]$ProcessId) {
    try {
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction Stop
        return $proc.CommandLine
    }
    catch {
        return $null
    }
}

function Test-ProxyProcessIdentity([System.Diagnostics.Process]$Process) {
    if ($null -eq $Process) { return $false }

    if ($Process.ProcessName -notin @("python", "python3", "pythonw")) {
        return $false
    }

    $commandLine = Get-ProcessCommandLine -ProcessId $Process.Id
    if ([string]::IsNullOrWhiteSpace($commandLine)) {
        return $false
    }

    return ($commandLine -match "uvicorn" -and $commandLine -match "kimi_proxy.main:app")
}

function Test-ProxyHealth {
    param([string]$Url = "http://127.0.0.1:8000/health", [int]$TimeoutSec = 2)

    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec
        return ([int]$resp.StatusCode -eq 200)
    }
    catch {
        return $false
    }
}

function Wait-ProxyHealth {
    param([string]$Url = "http://127.0.0.1:8000/health", [int]$MaxWaitSeconds = 20)

    $deadline = (Get-Date).AddSeconds($MaxWaitSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-ProxyHealth -Url $Url -TimeoutSec 2) {
            return $true
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Show-Help {
    Write-Host "Kimi Proxy Dashboard (Windows)"
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  .\bin\kimi-proxy.ps1 <start|stop|restart|status|test|help> [options]"
    Write-Host ""
    Write-Host "Options for start:"
    Write-Host "  --host <host>   default: 0.0.0.0"
    Write-Host "  --port <port>   default: 8000"
    Write-Host "  --reload        enable uvicorn reload"
}

function Get-ServerProcess {
    if (-not (Test-Path $PidFile)) { return $null }
    $pidValue = (Get-Content $PidFile -Raw).Trim()
    if ([string]::IsNullOrWhiteSpace($pidValue)) {
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        return $null
    }

    if ($pidValue -notmatch '^[0-9]+$') {
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        return $null
    }

    $proc = $null
    try {
        $proc = Get-Process -Id ([int]$pidValue) -ErrorAction Stop
    }
    catch {
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        return $null
    }

    if (-not (Test-ProxyProcessIdentity -Process $proc)) {
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        return $null
    }

    return $proc
}

function Ensure-Venv {
    if (-not (Test-Path $VenvPython)) {
        throw "Missing virtual environment: $VenvPython"
    }
}

function Start-Proxy {
    param([string]$BindHost = "0.0.0.0", [int]$Port = 8000, [switch]$Reload)

    $existing = Get-ServerProcess
    if ($null -ne $existing) {
        if (Test-ProxyHealth -Url "http://127.0.0.1:$Port/health" -TimeoutSec 2) {
            Write-Warn "Server already running (PID: $($existing.Id))"
            return
        }

        Write-Warn "Existing proxy process is unhealthy. Recycling PID $($existing.Id)."
        Stop-Process -Id $existing.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
        if (Test-Path $PidFile) { Remove-Item $PidFile -Force -ErrorAction SilentlyContinue }
    }

    Ensure-Venv
    if (Test-Path $PidFile) { Remove-Item $PidFile -Force }

    $existingPythonPath = if ($env:PYTHONPATH) { "$($env:PYTHONPATH);" } else { "" }
    $env:PYTHONPATH = "${existingPythonPath}$ProjectDir\src"
    $env:PYTHONIOENCODING = "utf-8"
    $env:PYTHONUTF8 = "1"

    Write-Info "Starting proxy on $BindHost`:$Port"
    $uvicornArgs = @("-m", "uvicorn", "kimi_proxy.main:app", "--host", $BindHost, "--port", "$Port")
    if ($Reload) { $uvicornArgs += "--reload" }

    $process = Start-Process -FilePath $VenvPython `
        -ArgumentList $uvicornArgs `
        -WorkingDirectory $ProjectDir `
        -RedirectStandardOutput $LogFile `
        -RedirectStandardError $ErrLogFile `
        -PassThru

    Set-Content -Path $PidFile -Value "$($process.Id)"
    Start-Sleep -Seconds 1

    if ($null -ne (Get-ServerProcess) -and (Wait-ProxyHealth -Url "http://127.0.0.1:$Port/health" -MaxWaitSeconds 20)) {
        Write-Ok "Proxy started (PID: $($process.Id))"
        if (Test-Path $McpScript) {
            Write-Info "Starting MCP Windows helper script"
            Start-Process -FilePath "powershell" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $McpScript, "start") -WorkingDirectory $ProjectDir | Out-Null
        }
        return
    }

    Write-Err "Proxy startup failed"
    if (Test-Path $ErrLogFile) {
        Write-Err "Last proxy stderr (tail):"
        Get-Content -Path $ErrLogFile -Tail 30 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host $_ }
    }
    exit 1
}

function Stop-Proxy {
    $proc = Get-ServerProcess
    if ($null -eq $proc) {
        Write-Warn "No running proxy"
    } else {
        Write-Info "Stopping proxy PID $($proc.Id)"
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
        Write-Ok "Proxy stopped"
    }

    if (Test-Path $PidFile) { Remove-Item $PidFile -Force }

    if (Test-Path $McpScript) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $McpScript stop | Out-Null
    }
}

function Show-Status {
    $proc = Get-ServerProcess
    if ($null -eq $proc) {
        Write-Info "Proxy is not running"
    } else {
        Write-Ok "Proxy is running (PID: $($proc.Id))"
        if (Test-ProxyHealth) {
            Write-Ok "Proxy health: OK (/health)"
        } else {
            Write-Warn "Proxy health: KO (/health unreachable)"
        }
    }
}

function Run-Tests {
    Ensure-Venv
    Push-Location $ProjectDir
    try {
        & $VenvPython -m pytest tests -v --ignore=tests/mcp --ignore=tests/test_mcp_phase3.py
    }
    finally {
        Pop-Location
    }
}

$command = if ($args.Count -gt 0) { $args[0] } else { "help" }

switch ($command) {
    "start" {
        $bindHost = "0.0.0.0"
        $port = 8000
        $reload = $false
        for ($i = 1; $i -lt $args.Count; $i++) {
            switch ($args[$i]) {
                "--host" { $bindHost = $args[$i + 1]; $i++ }
                "--port" { $port = [int]$args[$i + 1]; $i++ }
                "--reload" { $reload = $true }
            }
        }
        Start-Proxy -BindHost $bindHost -Port $port -Reload:([bool]$reload)
    }
    "stop" { Stop-Proxy }
    "restart" {
        Stop-Proxy
        Start-Sleep -Seconds 1
        Start-Proxy
    }
    "status" { Show-Status }
    "test" { Run-Tests }
    default { Show-Help }
}
