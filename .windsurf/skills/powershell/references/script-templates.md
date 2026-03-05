# PowerShell Script Templates

Reusable templates for common PowerShell scripting patterns.

## Basic Script Template

```powershell
#Requires -Version 5.1

<#
.SYNOPSIS
    Brief description of script purpose.

.DESCRIPTION
    Detailed description of what the script does.

.PARAMETER ParameterName
    Description of parameter.

.EXAMPLE
    .\Script.ps1 -ParameterName "Value"
    Description of example.

.NOTES
    Author: Your Name
    Date: $(Get-Date -Format 'yyyy-MM-dd')
    Version: 1.0
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory)]
    [string]$ParameterName,
    
    [Parameter()]
    [string]$OptionalParam = "DefaultValue"
)

# Script body
Write-Output "Parameter value: $ParameterName"
```

## Admin Script Template

```powershell
#Requires -Version 5.1
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Administrative script that requires elevation.

.DESCRIPTION
    Detailed description.

.NOTES
    Requires: Administrator privileges
#>

[CmdletBinding(SupportsShouldProcess)]
param (
    [Parameter(Mandatory)]
    [string]$ComputerName,
    
    [Parameter()]
    [switch]$Force
)

$ErrorActionPreference = "Stop"

try {
    if ($PSCmdlet.ShouldProcess($ComputerName, "Perform action")) {
        # Administrative action here
        Write-Verbose "Performing action on $ComputerName"
    }
}
catch {
    Write-Error "Failed: $_"
    exit 1
}
```

## Logging Script Template

```powershell
#Requires -Version 5.1

[CmdletBinding()]
param (
    [Parameter()]
    [string]$LogPath = (Join-Path $PSScriptRoot "script.log")
)

#region Logging Functions
function Write-Log {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory)]
        [string]$Message,
        
        [Parameter()]
        [ValidateSet("INFO", "WARNING", "ERROR")]
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Write to log file
    Add-Content -Path $script:LogPath -Value $logEntry
    
    # Also output based on level
    switch ($Level) {
        "INFO"    { Write-Verbose $Message }
        "WARNING" { Write-Warning $Message }
        "ERROR"   { Write-Error $Message }
    }
}
#endregion

#region Main Script
try {
    Write-Log "Script started" -Level INFO
    
    # Main logic here
    
    Write-Log "Script completed successfully" -Level INFO
}
catch {
    Write-Log "Script failed: $_" -Level ERROR
    exit 1
}
#endregion
```

## Multi-Computer Script Template

```powershell
#Requires -Version 5.1

<#
.SYNOPSIS
    Executes actions against multiple computers.

.PARAMETER ComputerName
    Target computer(s). Accepts pipeline input.

.PARAMETER Credential
    Alternate credentials for remote connections.
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
    [ValidateNotNullOrEmpty()]
    [string[]]$ComputerName,
    
    [Parameter()]
    [System.Management.Automation.PSCredential]$Credential
)

begin {
    $results = [System.Collections.ArrayList]::new()
    Write-Verbose "Starting processing"
}

process {
    foreach ($computer in $ComputerName) {
        Write-Verbose "Processing: $computer"
        
        try {
            # Test connectivity first
            if (-not (Test-Connection -ComputerName $computer -Count 1 -Quiet)) {
                throw "Computer is not reachable"
            }
            
            # Perform action
            $result = [PSCustomObject]@{
                ComputerName = $computer
                Status       = "Success"
                Data         = "Result data here"
                Error        = $null
            }
        }
        catch {
            $result = [PSCustomObject]@{
                ComputerName = $computer
                Status       = "Failed"
                Data         = $null
                Error        = $_.Exception.Message
            }
        }
        
        [void]$results.Add($result)
    }
}

end {
    $results
    Write-Verbose "Processing complete. Total: $($results.Count)"
}
```

## Configuration File Script Template

```powershell
#Requires -Version 5.1

[CmdletBinding()]
param (
    [Parameter()]
    [string]$ConfigPath = (Join-Path $PSScriptRoot "config.json")
)

# Load configuration
if (-not (Test-Path $ConfigPath)) {
    throw "Configuration file not found: $ConfigPath"
}

$config = Get-Content -Path $ConfigPath -Raw | ConvertFrom-Json

# Validate required config values
$requiredKeys = @("Setting1", "Setting2")
foreach ($key in $requiredKeys) {
    if (-not $config.PSObject.Properties.Name.Contains($key)) {
        throw "Missing required configuration: $key"
    }
}

# Use configuration
Write-Verbose "Setting1: $($config.Setting1)"
Write-Verbose "Setting2: $($config.Setting2)"

# Main logic using config values
```

**Example config.json:**
```json
{
    "Setting1": "Value1",
    "Setting2": "Value2",
    "Options": {
        "Verbose": true,
        "MaxRetries": 3
    }
}
```

## Menu-Driven Script Template

```powershell
#Requires -Version 5.1

function Show-Menu {
    Clear-Host
    Write-Host "================ Main Menu ================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Option One"
    Write-Host "2. Option Two"
    Write-Host "3. Option Three"
    Write-Host ""
    Write-Host "Q. Quit"
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
}

function Invoke-OptionOne {
    Write-Host "Executing Option One..." -ForegroundColor Green
    # Action code here
    Read-Host "Press Enter to continue"
}

function Invoke-OptionTwo {
    Write-Host "Executing Option Two..." -ForegroundColor Green
    # Action code here
    Read-Host "Press Enter to continue"
}

function Invoke-OptionThree {
    Write-Host "Executing Option Three..." -ForegroundColor Green
    # Action code here
    Read-Host "Press Enter to continue"
}

# Main loop
do {
    Show-Menu
    $selection = Read-Host "Select an option"
    
    switch ($selection) {
        '1' { Invoke-OptionOne }
        '2' { Invoke-OptionTwo }
        '3' { Invoke-OptionThree }
        'Q' { return }
        default { Write-Warning "Invalid selection" }
    }
} while ($true)
```

## Parallel Processing Template (PowerShell 7+)

```powershell
#Requires -Version 7.0

[CmdletBinding()]
param (
    [Parameter(Mandatory)]
    [string[]]$ComputerName,
    
    [Parameter()]
    [int]$ThrottleLimit = 10
)

$results = $ComputerName | ForEach-Object -Parallel {
    $computer = $_
    
    try {
        # Perform work
        $data = Test-Connection -ComputerName $computer -Count 1 -ErrorAction Stop
        
        [PSCustomObject]@{
            ComputerName = $computer
            Status       = "Online"
            ResponseTime = $data.Latency
        }
    }
    catch {
        [PSCustomObject]@{
            ComputerName = $computer
            Status       = "Offline"
            ResponseTime = $null
        }
    }
} -ThrottleLimit $ThrottleLimit

$results | Format-Table -AutoSize
```

## Function Module Template

```powershell
# MyModule.psm1

function Get-MyData {
    <#
    .SYNOPSIS
        Retrieves data.
    
    .DESCRIPTION
        Detailed description of the function.
    
    .PARAMETER Name
        The name to look up.
    
    .EXAMPLE
        Get-MyData -Name "Example"
    
    .OUTPUTS
        PSCustomObject
    #>
    
    [CmdletBinding()]
    [OutputType([PSCustomObject])]
    param (
        [Parameter(Mandatory, Position = 0)]
        [ValidateNotNullOrEmpty()]
        [string]$Name
    )
    
    process {
        [PSCustomObject]@{
            Name      = $Name
            Timestamp = Get-Date
            Data      = "Sample data"
        }
    }
}

function Set-MyData {
    <#
    .SYNOPSIS
        Sets data.
    #>
    
    [CmdletBinding(SupportsShouldProcess)]
    param (
        [Parameter(Mandatory)]
        [string]$Name,
        
        [Parameter(Mandatory)]
        [string]$Value
    )
    
    process {
        if ($PSCmdlet.ShouldProcess($Name, "Set value to '$Value'")) {
            # Actual implementation
            Write-Verbose "Setting $Name to $Value"
        }
    }
}

# Export functions
Export-ModuleMember -Function Get-MyData, Set-MyData
```

**Module manifest (MyModule.psd1):**
```powershell
@{
    RootModule        = 'MyModule.psm1'
    ModuleVersion     = '1.0.0'
    GUID              = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
    Author            = 'Your Name'
    Description       = 'Module description'
    PowerShellVersion = '5.1'
    FunctionsToExport = @('Get-MyData', 'Set-MyData')
    CmdletsToExport   = @()
    VariablesToExport = @()
    AliasesToExport   = @()
}
```

## Error Handling Patterns

### Comprehensive Try/Catch

```powershell
try {
    # Risky operation
    $result = Get-Content -Path $path -ErrorAction Stop
}
catch [System.IO.FileNotFoundException] {
    Write-Warning "File not found: $path"
    $result = $null
}
catch [System.UnauthorizedAccessException] {
    Write-Error "Access denied to: $path"
    throw
}
catch {
    Write-Error "Unexpected error: $($_.Exception.Message)"
    Write-Error "Stack trace: $($_.ScriptStackTrace)"
    throw
}
finally {
    # Cleanup (always runs)
    if ($resource) {
        $resource.Dispose()
    }
}
```

### Retry Pattern

```powershell
function Invoke-WithRetry {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory)]
        [scriptblock]$ScriptBlock,
        
        [Parameter()]
        [int]$MaxRetries = 3,
        
        [Parameter()]
        [int]$RetryDelaySeconds = 5
    )
    
    $attempt = 0
    $lastError = $null
    
    while ($attempt -lt $MaxRetries) {
        $attempt++
        
        try {
            return & $ScriptBlock
        }
        catch {
            $lastError = $_
            Write-Warning "Attempt $attempt failed: $_"
            
            if ($attempt -lt $MaxRetries) {
                Write-Verbose "Retrying in $RetryDelaySeconds seconds..."
                Start-Sleep -Seconds $RetryDelaySeconds
            }
        }
    }
    
    throw "All $MaxRetries attempts failed. Last error: $lastError"
}

# Usage
Invoke-WithRetry -ScriptBlock {
    Invoke-WebRequest -Uri "https://api.example.com" -ErrorAction Stop
} -MaxRetries 3 -RetryDelaySeconds 10
```
