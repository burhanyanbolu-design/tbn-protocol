# ════════════════════════════════════════════════════════════════════
# Universal cookie deployer for TBN Video Agent
# Picks up the latest *.instagram.* and *.youtube.* cookie files from
# your Downloads folder, uploads them, and restarts the service.
#
# Usage:  .\deploy_cookies.ps1
# ════════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"
$SSH_KEY = "C:\Users\Burhan Yanbolu\OneDrive\Desktop\tbn-protocol\.ssh_temp_key"
$SERVER = "ubuntu@3.11.229.68"
$DOWNLOADS = "C:\Users\Burhan Yanbolu\Downloads"

function Find-LatestCookies($pattern) {
    Get-ChildItem $DOWNLOADS -Filter $pattern -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
}

Write-Host "═══ TBN Universal Cookie Deployer ═══" -ForegroundColor Cyan
Write-Host ""

$deployed = @()

# ── Instagram ──
$ig = Find-LatestCookies "*instagram*cookies*.txt"
if ($ig) {
    Write-Host "[Instagram] Found: $($ig.Name) ($($ig.Length) bytes, $($ig.LastWriteTime))" -ForegroundColor Green
    & scp -i $SSH_KEY -o StrictHostKeyChecking=no $ig.FullName "${SERVER}:/tmp/ig_cookies.txt"
    & ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "sudo python3 /tmp/convert_cookies.py"
    $deployed += "Instagram"
} else {
    Write-Host "[Instagram] No cookie file found in Downloads (expected: *instagram*cookies*.txt)" -ForegroundColor Yellow
}

# ── YouTube ──
$yt = Find-LatestCookies "*youtube*cookies*.txt"
if (-not $yt) { $yt = Find-LatestCookies "*youtu*cookies*.txt" }
if ($yt) {
    Write-Host "[YouTube] Found: $($yt.Name) ($($yt.Length) bytes, $($yt.LastWriteTime))" -ForegroundColor Green
    & scp -i $SSH_KEY -o StrictHostKeyChecking=no $yt.FullName "${SERVER}:/tmp/yt_cookies.txt"
    & ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "sudo cp /tmp/yt_cookies.txt /opt/tbn-protocol/youtube_cookies.txt && sudo chmod 644 /opt/tbn-protocol/youtube_cookies.txt"
    $deployed += "YouTube"
} else {
    Write-Host "[YouTube] No cookie file found in Downloads (expected: *youtube*cookies*.txt)" -ForegroundColor Yellow
}

if ($deployed.Count -gt 0) {
    Write-Host ""
    Write-Host "Restarting TBN service..." -ForegroundColor Cyan
    & ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "sudo systemctl restart tbn"
    Write-Host ""
    Write-Host "✅ Deployed: $($deployed -join ', ')" -ForegroundColor Green
    Write-Host ""
    Write-Host "Test: https://tbn.hardinai.co.uk/video-agent" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "❌ No cookie files found in $DOWNLOADS" -ForegroundColor Red
    Write-Host "   Export cookies from your browser using a 'Get cookies.txt' extension" -ForegroundColor Yellow
}
