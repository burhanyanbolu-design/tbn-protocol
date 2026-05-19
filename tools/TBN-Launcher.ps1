# TBN Protocol — PowerShell Launcher
# Hardin AI Solutions
# Double-click TBN-Launcher.bat to run this

$Host.UI.RawUI.WindowTitle = "TBN Protocol — Hardin AI"
$Host.UI.RawUI.BackgroundColor = "Black"
$Host.UI.RawUI.ForegroundColor = "Green"
Clear-Host

Write-Host ""
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host "    TBN PROTOCOL — Hardin AI Solutions" -ForegroundColor Cyan
Write-Host "    Trusted Bot Network" -ForegroundColor Cyan
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host ""

# Go to project directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Activate venv if it exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "  [1/3] Activating virtual environment..." -ForegroundColor Yellow
    & .venv\Scripts\Activate.ps1
} else {
    Write-Host "  [1/3] Using system Python..." -ForegroundColor Yellow
}

# Check Flask is installed
$flaskCheck = python -c "import flask; print('ok')" 2>$null
if ($flaskCheck -ne "ok") {
    Write-Host "  Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

Write-Host "  [2/3] Dependencies ready" -ForegroundColor Green

# Open browser after short delay
Write-Host "  [3/3] Starting server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host "    Dashboard  : http://localhost:5000" -ForegroundColor White
Write-Host "    API        : http://localhost:5000/api/bots" -ForegroundColor White
Write-Host "    Governance : http://localhost:5000/governance" -ForegroundColor White
Write-Host "    Pricing    : http://localhost:5000/pricing" -ForegroundColor White
Write-Host "    Demo       : http://localhost:5000/demo" -ForegroundColor White
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Server running. Close this window to stop." -ForegroundColor Green
Write-Host ""

# Open browser after 2 seconds
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:5000"
} | Out-Null

# Start Flask server
python server.py
