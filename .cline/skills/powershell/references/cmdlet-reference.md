# PowerShell Essential Cmdlets Quick Reference

Quick reference for the most commonly used PowerShell cmdlets organized by category.

## Discovery & Help

```powershell
# Get help
Get-Help <cmdlet> -Full           # Full documentation
Get-Help <cmdlet> -Examples       # Just examples
Get-Help <cmdlet> -Online         # Open online docs

# Find commands
Get-Command -Verb Get             # All "Get-*" commands
Get-Command -Noun Service         # All "*-Service" commands
Get-Command -Module <name>        # Commands in module
Get-Verb                          # List approved verbs

# Discover object members
<object> | Get-Member             # Properties & methods
<object> | Get-Member -MemberType Property
```

## File System

```powershell
# Navigation
Get-Location                      # Current directory (pwd)
Set-Location <path>               # Change directory (cd)
Push-Location <path>              # Save location and change
Pop-Location                      # Return to saved location

# List contents
Get-ChildItem                     # List items (ls, dir)
Get-ChildItem -Recurse            # Include subdirectories
Get-ChildItem -Filter *.log       # Filter by pattern
Get-ChildItem -Hidden             # Show hidden items

# File operations
New-Item -ItemType File -Path <path>
New-Item -ItemType Directory -Path <path>
Copy-Item <src> <dest>
Copy-Item <src> <dest> -Recurse   # Copy directories
Move-Item <src> <dest>
Rename-Item <path> -NewName <name>
Remove-Item <path>
Remove-Item <path> -Recurse -Force

# File content
Get-Content <file>                # Read file (cat, type)
Get-Content <file> -Raw           # Read as single string
Get-Content <file> -Tail 10       # Last 10 lines
Set-Content <file> -Value <data>  # Write file (overwrite)
Add-Content <file> -Value <data>  # Append to file
Clear-Content <file>              # Empty file

# File info
Test-Path <path>                  # Check if exists
Get-Item <path>                   # Get item metadata
Get-ItemProperty <path>           # Get properties
```

## Output & Formatting

```powershell
# Format output
Format-Table                      # Table format
Format-List                       # List format
Format-Wide                       # Wide format

# Output destinations
Out-File <path>                   # Write to file
Out-GridView                      # GUI grid (Windows)
Out-Null                          # Discard output
Out-String                        # Convert to string

# Export data
Export-Csv <path> -NoTypeInformation
Export-Clixml <path>              # PowerShell XML format
ConvertTo-Json                    # JSON string
ConvertTo-Html                    # HTML table
```

## Selection & Filtering

```powershell
# Select properties
Select-Object -Property Name, Status
Select-Object -First 10           # First N items
Select-Object -Last 5             # Last N items
Select-Object -Unique             # Unique values
Select-Object -ExpandProperty <prop>  # Expand single property

# Filter objects
Where-Object { $_.Status -eq "Running" }
Where-Object Status -eq "Running" # Simplified syntax
Where-Object { $_ -gt 10 }        # Filter values

# Sort objects
Sort-Object -Property Name
Sort-Object -Property CPU -Descending
Sort-Object -Property @{e='CPU';d=$true}, @{e='Name';d=$false}

# Group objects
Group-Object -Property Status
Measure-Object                    # Count
Measure-Object -Property Size -Sum -Average -Maximum -Minimum
```

## Services

```powershell
Get-Service                       # List all services
Get-Service -Name <name>          # Specific service
Get-Service -DisplayName "*sql*"  # By display name

Start-Service -Name <name>        # Start service
Stop-Service -Name <name>         # Stop service
Restart-Service -Name <name>      # Restart service
Suspend-Service -Name <name>      # Pause service
Resume-Service -Name <name>       # Resume service

Set-Service -Name <name> -StartupType Automatic
Set-Service -Name <name> -Status Running
```

## Processes

```powershell
Get-Process                       # List all processes
Get-Process -Name <name>          # By name
Get-Process -Id <pid>             # By PID

Start-Process <path>              # Start process
Start-Process <path> -ArgumentList <args>
Start-Process <path> -Wait        # Wait for exit
Start-Process <path> -Verb RunAs  # Run as admin

Stop-Process -Name <name>
Stop-Process -Id <pid>
Stop-Process -Name <name> -Force

Wait-Process -Name <name>         # Wait for exit
Wait-Process -Id <pid> -Timeout 60
```

## Network

```powershell
# Connectivity
Test-Connection <host>            # Ping
Test-Connection <host> -Count 2 -Quiet  # True/False result
Test-NetConnection <host> -Port 443     # Port test

# DNS
Resolve-DnsName <hostname>

# Web requests
Invoke-WebRequest <url>           # HTTP request
Invoke-WebRequest <url> -OutFile <path>  # Download
Invoke-RestMethod <url>           # Parse JSON response

# Network config (Windows)
Get-NetIPConfiguration
Get-NetAdapter
Get-NetIPAddress
```

## Registry (Windows)

```powershell
# Read
Get-ItemProperty "HKLM:\SOFTWARE\..."
Get-ChildItem "HKLM:\SOFTWARE\..."

# Write
New-Item "HKCU:\Software\MyApp"
New-ItemProperty "HKCU:\Software\MyApp" -Name "Setting" -Value "Value"
Set-ItemProperty "HKCU:\Software\MyApp" -Name "Setting" -Value "NewValue"

# Delete
Remove-Item "HKCU:\Software\MyApp" -Recurse
Remove-ItemProperty "HKCU:\Software\MyApp" -Name "Setting"
```

## Event Logs (Windows)

```powershell
Get-WinEvent -LogName System -MaxEvents 50
Get-WinEvent -LogName Application -MaxEvents 100

# Filter
Get-WinEvent -FilterHashtable @{
    LogName = 'System'
    Level = 2           # 1=Critical, 2=Error, 3=Warning, 4=Info
    StartTime = (Get-Date).AddDays(-1)
}

# Classic cmdlets (older)
Get-EventLog -LogName System -Newest 50
Get-EventLog -LogName Application -EntryType Error
```

## Scheduled Tasks (Windows)

```powershell
Get-ScheduledTask
Get-ScheduledTask -TaskName <name>
Get-ScheduledTaskInfo -TaskName <name>

# Create
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\script.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At "2:00AM"
Register-ScheduledTask -TaskName "MyTask" -Action $action -Trigger $trigger

# Control
Start-ScheduledTask -TaskName <name>
Stop-ScheduledTask -TaskName <name>
Enable-ScheduledTask -TaskName <name>
Disable-ScheduledTask -TaskName <name>
Unregister-ScheduledTask -TaskName <name> -Confirm:$false
```

## Variables & Environment

```powershell
# Variables
$var = "value"                    # Set variable
Get-Variable                      # List all variables
Get-Variable -Name var            # Get specific
Set-Variable -Name var -Value "new"
Remove-Variable -Name var
Clear-Variable -Name var          # Set to null

# Environment
$env:PATH                         # Read env var
$env:COMPUTERNAME
$env:USERNAME
$env:USERPROFILE
$env:TEMP

[Environment]::SetEnvironmentVariable("VAR", "value", "User")  # Persistent
```

## Modules

```powershell
Get-Module                        # Loaded modules
Get-Module -ListAvailable         # Available modules
Import-Module <name>              # Load module
Remove-Module <name>              # Unload module

# PowerShell Gallery
Find-Module <name>                # Search gallery
Install-Module <name>             # Install from gallery
Update-Module <name>              # Update module
Uninstall-Module <name>           # Remove module
```

## Comparison & Logic Operators

```powershell
# Comparison
-eq    # Equal
-ne    # Not equal
-gt    # Greater than
-lt    # Less than
-ge    # Greater or equal
-le    # Less or equal

# String comparison
-like      # Wildcard (*?)
-notlike
-match     # Regex
-notmatch
-contains  # Collection contains
-notcontains
-in        # Value in collection
-notin

# Logical
-and
-or
-not / !
-xor

# Type
-is        # Is type
-isnot
-as        # Convert type
```

## Common Aliases

| Alias | Cmdlet |
|-------|--------|
| `cd`, `chdir`, `sl` | `Set-Location` |
| `cls`, `clear` | `Clear-Host` |
| `copy`, `cp` | `Copy-Item` |
| `del`, `rm`, `rmdir` | `Remove-Item` |
| `dir`, `ls`, `gci` | `Get-ChildItem` |
| `echo`, `write` | `Write-Output` |
| `cat`, `gc`, `type` | `Get-Content` |
| `md`, `mkdir` | `New-Item -ItemType Directory` |
| `move`, `mv` | `Move-Item` |
| `pwd`, `gl` | `Get-Location` |
| `ren` | `Rename-Item` |
| `sort` | `Sort-Object` |
| `where`, `?` | `Where-Object` |
| `foreach`, `%` | `ForEach-Object` |
| `select` | `Select-Object` |
| `ft` | `Format-Table` |
| `fl` | `Format-List` |
| `gm` | `Get-Member` |
| `gcm` | `Get-Command` |
| `gps`, `ps` | `Get-Process` |
| `gsv` | `Get-Service` |
| `iwr` | `Invoke-WebRequest` |
| `irm` | `Invoke-RestMethod` |

> **Note:** Avoid using aliases in scripts for readability. Use full cmdlet names.
