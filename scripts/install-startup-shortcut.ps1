$StartupFolder = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Startup)
$ShortcutPath = Join-Path $StartupFolder "KimiProxy.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$HOME\Documents\kimi-proxy\bin\kimi-proxy.ps1`" start"
$Shortcut.WorkingDirectory = "$HOME\Documents\kimi-proxy"
$Shortcut.Description = "Démarrage automatique du Kimi Proxy au démarrage Windows"
$Shortcut.Save()

Write-Host "✅ Raccourci de démarrage automatique créé : $ShortcutPath"
