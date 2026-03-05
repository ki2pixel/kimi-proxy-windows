---
name: powershell
description: PowerShell scripting toolkit for Windows automation. Use when building scripts for Windows system administration, managing services, processes, files, registry, users, or any Windows automation task. Covers cmdlets, pipelines, functions, error handling, and best practices.
---

# PowerShell Scripting

Comprehensive reference for building PowerShell scripts for Windows automation and system administration.

**Target:** Windows PowerShell 5.1 and PowerShell 7.x (cross-platform)

## When to Use This Skill

- Building automation scripts for Windows systems
- Managing Windows services, processes, and scheduled tasks
- Working with files, folders, and registry operations
- Creating reusable functions and modules
- System administration tasks (users, groups, permissions)
- Automating repetitive administrative tasks
- Migrating bash/shell scripts to Windows equivalents

## Prerequisites

### PowerShell Versions

| Version | Platform | Notes |
|---------|----------|-------|
| Windows PowerShell 5.1 | Windows only | Pre-installed on Windows 10/11, Server 2016+ |
| PowerShell 7.x | Cross-platform | Install separately, runs alongside 5.1 |

### Check Version

```powershell
$PSVersionTable.PSVersion
```

### Execution Policy

Scripts require appropriate execution policy:

```powershell
# Check current policy
Get-ExecutionPolicy

# Set policy (run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

| Policy | Description |
|--------|-------------|
| `Restricted` | No scripts allowed (Windows default) |
| `RemoteSigned` | Local scripts run; downloaded scripts need signature |
| `Unrestricted` | All scripts run with warning for downloaded |

## Core Concepts

### Cmdlet Naming Convention

PowerShell uses **Verb-Noun** naming:

```
Get-Process      # Retrieves process information
Stop-Service     # Stops a service
New-Item         # Creates a new item
Set-Location     # Changes current location
```

**Common Verbs:**

| Verb | Use For | Example |
|------|---------|---------|
| `Get` | Retrieve data | `Get-Service`, `Get-ChildItem` |
| `Set` | Modify existing | `Set-Content`, `Set-Variable` |
| `New` | Create new | `New-Item`, `New-Object` |
| `Remove` | Delete | `Remove-Item`, `Remove-Variable` |
| `Start` | Begin operation | `Start-Process`, `Start-Service` |
| `Stop` | End operation | `Stop-Process`, `Stop-Service` |
| `Test` | Verify/check | `Test-Path`, `Test-Connection` |
| `Invoke` | Execute action | `Invoke-Command`, `Invoke-WebRequest` |

### Discovery Commands

```powershell
# Find all approved verbs
Get-Verb | Sort-Object Verb

# Find commands by verb
Get-Command -Verb Get

# Find commands by noun
Get-Command -Noun Service

# Find commands in a module
Get-Command -Module ActiveDirectory

# Get detailed help
Get-Help Get-Process -Full

# Get examples only
Get-Help Get-Process -Examples

# Discover object properties and methods
Get-Service | Get-Member
```

### The Pipeline

PowerShell passes **objects** (not text) through the pipeline:

```powershell
# Chain commands with |
Get-Service | Where-Object Status -eq 'Running' | Select-Object Name, Status

# Filter early (filter left)
Get-Service -Name w* | Where-Object Status -eq 'Running'

# Format output
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10
```

**Pipeline Best Practices:**
- Filter as early as possible ("filter left")
- Use native parameters before `Where-Object`
- Objects maintain type information through pipeline

## Variables and Data Types

### Variable Basics

```powershell
# Assign variable
$name = "Server01"

# Multiple assignment
$a, $b, $c = 1, 2, 3

# Typed variable
[string]$message = "Hello"
[int]$count = 42
[datetime]$date = Get-Date

# Environment variables
$env:COMPUTERNAME
$env:USERNAME
$env:PATH
```

### Common Data Types

```powershell
[string]    # Text
[int]       # Integer
[double]    # Decimal number
[bool]      # $true or $false
[array]     # Collection
[hashtable] # Key-value pairs
[datetime]  # Date and time
```

### Arrays and Collections

```powershell
# Array
$servers = @("Server01", "Server02", "Server03")
$servers[0]           # First element
$servers[-1]          # Last element
$servers += "Server04" # Add element

# Hashtable
$config = @{
    Name = "MyApp"
    Version = "1.0"
    Enabled = $true
}
$config.Name          # Access by key
$config["Version"]    # Alternative syntax
```

### String Operations

```powershell
# String interpolation (double quotes)
$name = "World"
"Hello, $name!"       # Hello, World!

# Literal string (single quotes)
'Hello, $name!'       # Hello, $name!

# Subexpressions
"Date: $(Get-Date -Format 'yyyy-MM-dd')"

# Here-strings (multiline)
$script = @"
Line 1
Line 2 with $variable
"@

# String methods
$text = "PowerShell"
$text.ToUpper()       # POWERSHELL
$text.Length          # 10
$text.Contains("Shell") # True
$text.Replace("Shell", "Script")
```

## Control Flow

### Conditionals

```powershell
# If/ElseIf/Else
if ($value -gt 10) {
    "Greater than 10"
} elseif ($value -eq 10) {
    "Equal to 10"
} else {
    "Less than 10"
}

# Switch statement
switch ($status) {
    "Running" { "Service is running" }
    "Stopped" { "Service is stopped" }
    default   { "Unknown status" }
}

# Ternary operator (PowerShell 7+)
$result = $value -gt 10 ? "High" : "Low"
```

### Comparison Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `-eq` | Equal | `$a -eq $b` |
| `-ne` | Not equal | `$a -ne $b` |
| `-gt` | Greater than | `$a -gt 10` |
| `-lt` | Less than | `$a -lt 10` |
| `-ge` | Greater or equal | `$a -ge 10` |
| `-le` | Less or equal | `$a -le 10` |
| `-like` | Wildcard match | `$name -like "*.txt"` |
| `-match` | Regex match | `$text -match "\d+"` |
| `-contains` | Collection contains | `$arr -contains "item"` |
| `-in` | Value in collection | `"item" -in $arr` |

### Loops

```powershell
# ForEach-Object (pipeline)
Get-Service | ForEach-Object { $_.Name }

# foreach statement
foreach ($server in $servers) {
    Test-Connection -ComputerName $server -Count 1
}

# For loop
for ($i = 0; $i -lt 10; $i++) {
    "Iteration $i"
}

# While loop
while ($condition) {
    # code
}

# Do-While / Do-Until
do {
    # code
} while ($condition)

do {
    # code
} until ($condition)
```

## Functions

### Basic Function

```powershell
function Get-Greeting {
    param (
        [string]$Name = "World"
    )
    
    "Hello, $Name!"
}

Get-Greeting -Name "PowerShell"
```

### Advanced Function

```powershell
function Get-SystemInfo {
    <#
    .SYNOPSIS
        Retrieves system information from computers.
    
    .DESCRIPTION
        Gets OS, memory, and CPU information from local or remote computers.
    
    .PARAMETER ComputerName
        The computer(s) to query. Defaults to local computer.
    
    .EXAMPLE
        Get-SystemInfo -ComputerName "Server01"
    
    .EXAMPLE
        "Server01", "Server02" | Get-SystemInfo
    #>
    
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $false,
                   ValueFromPipeline = $true,
                   ValueFromPipelineByPropertyName = $true)]
        [ValidateNotNullOrEmpty()]
        [string[]]$ComputerName = $env:COMPUTERNAME
    )
    
    process {
        foreach ($computer in $ComputerName) {
            try {
                $os = Get-CimInstance -ClassName Win32_OperatingSystem -ComputerName $computer
                
                [PSCustomObject]@{
                    ComputerName = $computer
                    OSName       = $os.Caption
                    Version      = $os.Version
                    Memory       = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
                }
            }
            catch {
                Write-Warning "Failed to query $computer: $_"
            }
        }
    }
}
```

### Parameter Validation

```powershell
param (
    [Parameter(Mandatory)]
    [string]$Name,
    
    [ValidateSet("Low", "Medium", "High")]
    [string]$Priority = "Medium",
    
    [ValidateRange(1, 100)]
    [int]$Count = 10,
    
    [ValidateScript({ Test-Path $_ })]
    [string]$Path,
    
    [ValidatePattern("^\d{3}-\d{4}$")]
    [string]$PhoneNumber
)
```

## Error Handling

### Try/Catch/Finally

```powershell
try {
    # Code that might fail
    $result = Get-Content -Path $filePath -ErrorAction Stop
}
catch [System.IO.FileNotFoundException] {
    Write-Warning "File not found: $filePath"
}
catch {
    # Generic catch
    Write-Error "An error occurred: $_"
    Write-Error $_.Exception.Message
}
finally {
    # Always runs
    # Cleanup code here
}
```

### Error Action Preference

```powershell
# For single command
Get-Content -Path "missing.txt" -ErrorAction SilentlyContinue

# For script block
$ErrorActionPreference = "Stop"
```

| Value | Behavior |
|-------|----------|
| `Continue` | Display error, continue (default) |
| `Stop` | Terminate on error |
| `SilentlyContinue` | Suppress error, continue |
| `Inquire` | Prompt user |

### Throw Custom Errors

```powershell
if (-not (Test-Path $path)) {
    throw "Path does not exist: $path"
}
```

## Common Operations

### File System

```powershell
# List items
Get-ChildItem -Path C:\Logs -Recurse -Filter *.log

# Create directory
New-Item -Path C:\Backup -ItemType Directory -Force

# Copy files
Copy-Item -Path C:\Source\* -Destination C:\Backup -Recurse

# Move/Rename
Move-Item -Path C:\Old\file.txt -Destination C:\New\
Rename-Item -Path C:\file.txt -NewName "newname.txt"

# Delete
Remove-Item -Path C:\Temp\* -Recurse -Force

# Read file
$content = Get-Content -Path C:\data.txt
$content = Get-Content -Path C:\data.txt -Raw  # Single string

# Write file
Set-Content -Path C:\output.txt -Value $data
Add-Content -Path C:\log.txt -Value "$(Get-Date): Entry"
$data | Out-File -FilePath C:\output.txt -Encoding UTF8
```

### Services

```powershell
# List services
Get-Service | Where-Object Status -eq "Running"

# Service by name
Get-Service -Name "wuauserv"

# Control services (requires elevation)
Start-Service -Name "wuauserv"
Stop-Service -Name "wuauserv"
Restart-Service -Name "wuauserv"

# Set startup type
Set-Service -Name "wuauserv" -StartupType Automatic
```

### Processes

```powershell
# List processes
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10

# Start process
Start-Process -FilePath "notepad.exe"
Start-Process -FilePath "cmd.exe" -ArgumentList "/c dir" -Wait -NoNewWindow

# Stop process
Stop-Process -Name "notepad" -Force
Get-Process -Name "notepad" | Stop-Process
```

### Registry

```powershell
# Read registry value
Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion"

# Get specific value
(Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion").ProductName

# Set registry value
Set-ItemProperty -Path "HKCU:\Software\MyApp" -Name "Setting" -Value "Value"

# Create registry key
New-Item -Path "HKCU:\Software\MyApp" -Force

# Remove registry key
Remove-Item -Path "HKCU:\Software\MyApp" -Recurse
```

### Network

```powershell
# Test connectivity
Test-Connection -ComputerName "server01" -Count 2

# DNS lookup
Resolve-DnsName -Name "example.com"

# HTTP request
Invoke-WebRequest -Uri "https://api.example.com/data" -Method Get
Invoke-RestMethod -Uri "https://api.example.com/data"  # Auto-parses JSON

# Download file
Invoke-WebRequest -Uri $url -OutFile "C:\download.zip"
```

### Scheduled Tasks

```powershell
# List tasks
Get-ScheduledTask | Where-Object State -eq "Ready"

# Create task
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\Scripts\backup.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At "2:00AM"
Register-ScheduledTask -TaskName "DailyBackup" -Action $action -Trigger $trigger -RunLevel Highest

# Run task
Start-ScheduledTask -TaskName "DailyBackup"

# Remove task
Unregister-ScheduledTask -TaskName "DailyBackup" -Confirm:$false
```

### Event Logs

```powershell
# Get recent events
Get-WinEvent -LogName System -MaxEvents 50

# Filter events
Get-WinEvent -FilterHashtable @{
    LogName = 'System'
    Level = 2  # Error
    StartTime = (Get-Date).AddDays(-1)
}

# Write to event log
Write-EventLog -LogName Application -Source "MyScript" -EventId 1000 -Message "Script completed"
```

## Data Formats

### JSON

```powershell
# Convert to JSON
$data | ConvertTo-Json -Depth 3

# Convert from JSON
$object = Get-Content -Path config.json | ConvertFrom-Json

# API example
$response = Invoke-RestMethod -Uri "https://api.example.com/users"
```

### CSV

```powershell
# Export to CSV
Get-Process | Select-Object Name, CPU, WorkingSet | Export-Csv -Path processes.csv -NoTypeInformation

# Import from CSV
$users = Import-Csv -Path users.csv
```

### XML

```powershell
# Convert to XML
$data | ConvertTo-Xml

# Read XML
[xml]$config = Get-Content -Path config.xml
$config.root.setting
```

## Script Template

```powershell
#Requires -Version 5.1
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Brief description of script purpose.

.DESCRIPTION
    Detailed description of what the script does.

.PARAMETER Parameter1
    Description of parameter.

.EXAMPLE
    .\Script.ps1 -Parameter1 "Value"
    
    Description of example.

.NOTES
    Author: Your Name
    Version: 1.0
    Date: 2026-02-01
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory)]
    [string]$Parameter1,
    
    [Parameter()]
    [switch]$Force
)

#region Variables
$ErrorActionPreference = "Stop"
$logPath = Join-Path $PSScriptRoot "script.log"
#endregion

#region Functions
function Write-Log {
    param ([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Add-Content -Path $logPath
    Write-Verbose $Message
}
#endregion

#region Main
try {
    Write-Log "Script started"
    
    # Main script logic here
    
    Write-Log "Script completed successfully"
}
catch {
    Write-Log "ERROR: $_"
    throw
}
finally {
    # Cleanup
}
#endregion
```

## Best Practices

### Do

- Use approved verbs for function names
- Add comment-based help to functions
- Use `[CmdletBinding()]` for advanced functions
- Validate parameters early
- Use `-ErrorAction Stop` with try/catch
- Use single quotes for literal strings
- Filter left in the pipeline
- Use `Write-Verbose` for debugging output

### Avoid

- Hardcoding values (use parameters)
- Using aliases in scripts (`gci` → `Get-ChildItem`)
- Modifying global `$ErrorActionPreference`
- Catching all errors without handling
- Using `Write-Host` for output (use `Write-Output`)
- Running scripts as Administrator unnecessarily

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Script won't run | Check `Get-ExecutionPolicy`, set to `RemoteSigned` |
| Access denied | Run PowerShell as Administrator |
| Command not found | Check module is imported: `Import-Module ModuleName` |
| Pipeline returns nothing | Check `Where-Object` filter conditions |
| Error not caught | Add `-ErrorAction Stop` to command |

## References

- [PowerShell Documentation](https://learn.microsoft.com/en-us/powershell/)
- [about_Functions](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_functions)
- [about_Try_Catch_Finally](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_try_catch_finally)
- [Approved Verbs](https://learn.microsoft.com/en-us/powershell/scripting/developer/cmdlet/approved-verbs-for-windows-powershell-commands)
