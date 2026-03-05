Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$VenvPython = Join-Path $ProjectDir "venv\Scripts\python.exe"

$RuntimeRoot = if ($env:KIMI_PROXY_TMP_ROOT) { $env:KIMI_PROXY_TMP_ROOT } else { Join-Path $env:TEMP "kimi-proxy" }
$McpRuntimeDir = Join-Path $RuntimeRoot "mcp"
$McpLogDir = Join-Path $RuntimeRoot "logs"
$ProxyHealthUrl = if ($env:KIMI_PROXY_HEALTH_URL) { $env:KIMI_PROXY_HEALTH_URL } else { "http://127.0.0.1:8000/health" }
$ProxyPidFile = Join-Path $ProjectDir ".server.pid"
$ProxyLogFile = Join-Path $ProjectDir "server.log"
$ProxyErrLogFile = Join-Path $ProjectDir "server.err.log"

$CompressionPort = 8001
$SequentialPort = 8003
$FastFilesystemPort = 8004
$JsonQueryPort = 8005
$PrunerPort = 8006

$CompressionPidFile = Join-Path $McpRuntimeDir "mcp_compression.pid"
$SequentialPidFile = Join-Path $McpRuntimeDir "mcp_sequential_thinking.pid"
$FastFilesystemPidFile = Join-Path $McpRuntimeDir "mcp_fast_filesystem.pid"
$JsonQueryPidFile = Join-Path $McpRuntimeDir "mcp_json_query.pid"
$PrunerPidFile = Join-Path $McpRuntimeDir "mcp_pruner.pid"

function Write-Info([string]$Message) { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Ok([string]$Message) { Write-Host "[OK]   $Message" -ForegroundColor Green }
function Write-Warn([string]$Message) { Write-Host "[WARN] $Message" -ForegroundColor Yellow }

function Get-ProcessCommandLine([int]$ProcessId) {
    try {
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction Stop
        return $proc.CommandLine
    }
    catch {
        return $null
    }
}

function Test-IsMcpHelperProcess([int]$ProcessId) {
    $commandLine = Get-ProcessCommandLine -ProcessId $ProcessId
    if ([string]::IsNullOrWhiteSpace($commandLine)) {
        return $false
    }

    return (
        $commandLine -match "scripts[\\/]mcp_http_server.py" -or
        $commandLine -match "kimi_proxy.features.mcp_pruner.server"
    )
}

function Test-HttpHealth([string]$Url, [int]$TimeoutSec = 2) {
    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec
        return ([int]$resp.StatusCode -eq 200)
    }
    catch {
        return $false
    }
}

function Wait-HttpHealth([string]$Url, [int]$MaxWaitSeconds = 15) {
    $deadline = (Get-Date).AddSeconds($MaxWaitSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-HttpHealth -Url $Url -TimeoutSec 2) {
            return $true
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Get-LiveProcessByPidFile([string]$PidFile) {
    if (-not (Test-Path $PidFile)) {
        return $null
    }

    $procIdText = (Get-Content $PidFile -Raw).Trim()
    if ([string]::IsNullOrWhiteSpace($procIdText)) {
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        return $null
    }

    $proc = Get-Process -Id ([int]$procIdText) -ErrorAction SilentlyContinue
    if ($null -eq $proc) {
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        return $null
    }
    return $proc
}

function Ensure-Dirs {
    New-Item -ItemType Directory -Path $McpRuntimeDir -Force | Out-Null
    New-Item -ItemType Directory -Path $McpLogDir -Force | Out-Null
}

function Ensure-Venv {
    if (-not (Test-Path $VenvPython)) {
        throw "Missing virtual environment: $VenvPython"
    }
}

function Test-PortListening([int]$Port) {
    $conn = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq $Port }
    return ($null -ne $conn)
}

function Wait-PortListening([int]$Port, [int]$MaxWaitSeconds = 15) {
    $deadline = (Get-Date).AddSeconds($MaxWaitSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-PortListening $Port) {
            return $true
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Wait-PortClosed([int]$Port, [int]$MaxWaitSeconds = 10) {
    $deadline = (Get-Date).AddSeconds($MaxWaitSeconds)
    while ((Get-Date) -lt $deadline) {
        if (-not (Test-PortListening $Port)) {
            return $true
        }
        Start-Sleep -Milliseconds 300
    }
    return (-not (Test-PortListening $Port))
}

function Start-Pruner {
    Ensure-Venv
    $existing = Get-LiveProcessByPidFile -PidFile $PrunerPidFile
    if ($null -ne $existing -and (Test-PortListening $PrunerPort) -and (Wait-HttpHealth -Url "http://127.0.0.1:$PrunerPort/health" -MaxWaitSeconds 3)) {
        Write-Ok "MCP pruner already active on port $PrunerPort"
        return
    }

    $logFile = Join-Path $McpLogDir "mcp_pruner.log"
    $env:PYTHONPATH = "$ProjectDir\src"
    $env:MCP_PRUNER_PORT = "$PrunerPort"

    $errFile = Join-Path $McpLogDir "mcp_pruner.err.log"
    $proc = Start-Process -FilePath $VenvPython `
        -ArgumentList @("-m", "kimi_proxy.features.mcp_pruner.server") `
        -WorkingDirectory $ProjectDir `
        -RedirectStandardOutput $logFile `
        -RedirectStandardError $errFile `
        -WindowStyle Hidden `
        -PassThru

    Set-Content -Path $PrunerPidFile -Value "$($proc.Id)"
    Start-Sleep -Seconds 1

    $portReady = Wait-PortListening -Port $PrunerPort -MaxWaitSeconds 15
    $healthReady = Wait-HttpHealth -Url "http://127.0.0.1:$PrunerPort/health" -MaxWaitSeconds 15
    $live = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
    if ($null -ne $live -and $portReady -and $healthReady) {
        Write-Ok "MCP pruner started (PID: $($proc.Id), port: $PrunerPort)"
    } else {
        Write-Warn "MCP pruner startup check failed (pid/port/health). Check logs: $logFile and $errFile"
        throw "Pruner startup failed"
    }
}

function Start-GenericMcpHttpServer {
    param(
        [string]$Name,
        [string]$Kind,
        [int]$Port,
        [string]$PidFile,
        [string]$LogFile
    )

    Ensure-Venv

    $existing = Get-LiveProcessByPidFile -PidFile $PidFile
    if ($null -ne $existing -and (Test-PortListening $Port) -and (Wait-HttpHealth -Url "http://127.0.0.1:$Port/health" -MaxWaitSeconds 3)) {
        Write-Ok "$Name already active on port $Port"
        return
    }

    $env:MCP_SERVER_KIND = $Kind
    $env:MCP_SERVER_HOST = "0.0.0.0"
    $env:MCP_SERVER_PORT = "$Port"
    $diskRoots = $env:MCP_DISK_ROOTS
    if ([string]::IsNullOrWhiteSpace($diskRoots)) {
        $diskRoots = $ProjectDir
    }
    $env:MCP_DISK_ROOTS = $diskRoots
    $env:MCP_ALLOWED_ROOT = $ProjectDir

    $errFile = "$LogFile.err"
    $proc = Start-Process -FilePath $VenvPython `
        -ArgumentList @("scripts/mcp_http_server.py") `
        -WorkingDirectory $ProjectDir `
        -RedirectStandardOutput $LogFile `
        -RedirectStandardError $errFile `
        -WindowStyle Hidden `
        -PassThru

    Set-Content -Path $PidFile -Value "$($proc.Id)"
    Start-Sleep -Seconds 1

    $portReady = Wait-PortListening -Port $Port -MaxWaitSeconds 15
    $healthReady = Wait-HttpHealth -Url "http://127.0.0.1:$Port/health" -MaxWaitSeconds 15
    $live = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
    if ($null -ne $live -and $portReady -and $healthReady) {
        Write-Ok "$Name started (PID: $($proc.Id), port: $Port)"
    } else {
        Write-Warn "$Name startup check failed (pid/port/health). Check logs: $LogFile and $errFile"
        throw "$Name startup failed"
    }
}

function Stop-FromPidFile([string]$PidFile) {
    if (-not (Test-Path $PidFile)) { return }
    $rawPid = (Get-Content $PidFile -Raw).Trim()
    if (-not [string]::IsNullOrWhiteSpace($rawPid)) {
        try {
            Stop-Process -Id ([int]$rawPid) -Force -ErrorAction SilentlyContinue
        } catch {
        }
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

function Stop-ByPort([int]$Port) {
    $connections = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq $Port }
    foreach ($connection in $connections) {
        if (-not (Test-IsMcpHelperProcess -ProcessId $connection.OwningProcess)) {
            Write-Warn "Skipping non-MCP process on port $Port (PID: $($connection.OwningProcess))"
            continue
        }

        try {
            Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
        }
        catch {
        }
    }
}

function Show-PortStatus([string]$Name, [int]$Port) {
    if (Test-PortListening $Port) {
        Write-Host "  - $Name ($Port): Active" -ForegroundColor Green
    } else {
        Write-Host "  - $Name ($Port): Inactive" -ForegroundColor Yellow
    }
}

function Show-McpStatus {
    Show-PortStatus -Name "Context Compression MCP" -Port $CompressionPort
    Show-PortStatus -Name "Sequential Thinking MCP" -Port $SequentialPort
    Show-PortStatus -Name "Fast Filesystem MCP" -Port $FastFilesystemPort
    Show-PortStatus -Name "JSON Query MCP" -Port $JsonQueryPort
    Show-PortStatus -Name "MCP Pruner" -Port $PrunerPort
}

function Get-ProxyProcessByPidFile {
    if (-not (Test-Path $ProxyPidFile)) {
        return $null
    }

    $procIdText = (Get-Content $ProxyPidFile -Raw).Trim()
    if ([string]::IsNullOrWhiteSpace($procIdText) -or $procIdText -notmatch '^[0-9]+$') {
        Remove-Item $ProxyPidFile -Force -ErrorAction SilentlyContinue
        return $null
    }

    $proc = Get-Process -Id ([int]$procIdText) -ErrorAction SilentlyContinue
    if ($null -eq $proc) {
        Remove-Item $ProxyPidFile -Force -ErrorAction SilentlyContinue
        return $null
    }
    return $proc
}

function Ensure-ProxyRunning {
    if (Test-HttpHealth -Url $ProxyHealthUrl -TimeoutSec 2) {
        return
    }

    Write-Warn "Proxy health unreachable via $ProxyHealthUrl. Attempting auto-start on port 8000..."
    Ensure-Venv

    $existing = Get-ProxyProcessByPidFile
    if ($null -eq $existing) {
        $existingPythonPath = if ($env:PYTHONPATH) { "$($env:PYTHONPATH);" } else { "" }
        $env:PYTHONPATH = "${existingPythonPath}$ProjectDir\src"
        $env:PYTHONIOENCODING = "utf-8"
        $env:PYTHONUTF8 = "1"

        $proxyProc = Start-Process -FilePath $VenvPython `
            -ArgumentList @("-m", "uvicorn", "kimi_proxy.main:app", "--host", "0.0.0.0", "--port", "8000") `
            -WorkingDirectory $ProjectDir `
            -RedirectStandardOutput $ProxyLogFile `
            -RedirectStandardError $ProxyErrLogFile `
            -PassThru

        Set-Content -Path $ProxyPidFile -Value "$($proxyProc.Id)"
        Start-Sleep -Milliseconds 500
    }

    if (Wait-HttpHealth -Url $ProxyHealthUrl -MaxWaitSeconds 20) {
        Write-Ok "Proxy health reachable via $ProxyHealthUrl"
        return
    }

    Write-Warn "Proxy auto-start failed. Cline streamableHttp MCP servers may return fetch failed."
}

function Start-McpServers {
    param(
        [switch]$ForceCleanStart
    )

    if ($ForceCleanStart) {
        Write-Info "Force clean start requested: stopping existing MCP helper processes first"
        Stop-McpServers -SkipBanner
        Start-Sleep -Milliseconds 700
    }

    Ensure-Dirs
    Ensure-ProxyRunning
    Write-Info "Starting MCP Windows helpers"
    Write-Info "Expected ports: compression=$CompressionPort sequential=$SequentialPort fast-filesystem=$FastFilesystemPort json-query=$JsonQueryPort pruner=$PrunerPort"

    Start-GenericMcpHttpServer -Name "Context Compression MCP" -Kind "context-compression" -Port $CompressionPort -PidFile $CompressionPidFile -LogFile (Join-Path $McpLogDir "mcp_compression.log")
    Start-GenericMcpHttpServer -Name "Sequential Thinking MCP" -Kind "sequential-thinking" -Port $SequentialPort -PidFile $SequentialPidFile -LogFile (Join-Path $McpLogDir "mcp_sequential_thinking.log")
    Start-GenericMcpHttpServer -Name "Fast Filesystem MCP" -Kind "fast-filesystem" -Port $FastFilesystemPort -PidFile $FastFilesystemPidFile -LogFile (Join-Path $McpLogDir "mcp_fast_filesystem.log")
    Start-GenericMcpHttpServer -Name "JSON Query MCP" -Kind "json-query" -Port $JsonQueryPort -PidFile $JsonQueryPidFile -LogFile (Join-Path $McpLogDir "mcp_json_query.log")
    Start-Pruner
    Show-McpStatus

    if (Test-HttpHealth -Url $ProxyHealthUrl -TimeoutSec 2) {
        Write-Ok "Proxy health reachable via $ProxyHealthUrl"
    } else {
        Write-Warn "Proxy health unreachable via $ProxyHealthUrl. Cline streamableHttp MCP servers (sequential-thinking / fast-filesystem / json-query) will return fetch failed until proxy is running."
    }
}

function Stop-McpServers {
    param(
        [switch]$SkipBanner
    )

    if (-not $SkipBanner) {
        Write-Info "Stopping MCP Windows helpers"
    }

    foreach ($pidFile in @($CompressionPidFile, $SequentialPidFile, $FastFilesystemPidFile, $JsonQueryPidFile, $PrunerPidFile)) {
        Stop-FromPidFile -PidFile $pidFile
    }

    foreach ($port in @($CompressionPort, $SequentialPort, $FastFilesystemPort, $JsonQueryPort, $PrunerPort)) {
        Stop-ByPort -Port $port
    }

    foreach ($port in @($CompressionPort, $SequentialPort, $FastFilesystemPort, $JsonQueryPort, $PrunerPort)) {
        if (-not (Wait-PortClosed -Port $port -MaxWaitSeconds 8)) {
            Write-Warn "Port $port still listening after stop attempt (possible non-MCP process or delayed release)"
        }
    }

    if (-not $SkipBanner) {
        Write-Ok "MCP stop completed"
    }
}

$command = if ($args.Count -gt 0) { $args[0] } else { "start" }

switch ($command) {
    "start" { Start-McpServers -ForceCleanStart }
    "stop" { Stop-McpServers }
    "status" { Show-McpStatus }
    "restart" {
        Start-McpServers -ForceCleanStart
    }
    default {
        Write-Host "Usage: .\scripts\start-mcp-servers.ps1 [start|stop|status|restart]"
        exit 1
    }
}
