# Run this ONCE to create a desktop shortcut
# Right-click -> "Run with PowerShell"

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = "$desktopPath\Hardin AI Control Panel.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$shortcut = $WshShell.CreateShortcut($shortcutPath)

$shortcut.TargetPath = "$projectDir\TBN-Launcher.bat"
$shortcut.WorkingDirectory = $projectDir
$shortcut.Description = "Hardin AI Solutions — Open all services"
$shortcut.WindowStyle = 1

# Use Python icon if available
$pythonIcon = (Get-Command python -ErrorAction SilentlyContinue)?.Source
if ($pythonIcon) {
    $shortcut.IconLocation = $pythonIcon
}

$shortcut.Save()

Write-Host ""
Write-Host "  Desktop shortcut created!" -ForegroundColor Green
Write-Host "  'Hardin AI Control Panel' is now on your Desktop." -ForegroundColor Cyan
Write-Host ""
Read-Host "  Press Enter to close"
