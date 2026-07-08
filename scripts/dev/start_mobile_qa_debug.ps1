param(
    [int]$BackendPort = 8000,
    [int]$ExpoPort = 8081,
    [string]$DataMode = "api-auth",
    [string]$AuthMode = "auth"
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Test-PortListening {
    param([int]$Port)
    $conn = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    return $null -ne $conn
}

function Get-LanIp {
    $preferred = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object {
            $_.IPAddress -notlike "127.*" -and
            $_.IPAddress -notlike "169.254.*" -and
            $_.IPAddress -notlike "172.28.*" -and
            $_.IPAddress -notlike "198.18.*" -and
            $_.InterfaceAlias -match "WLAN|Wi-Fi|Ethernet"
        } |
        Sort-Object @{ Expression = { if ($_.InterfaceAlias -match "WLAN|Wi-Fi") { 0 } else { 1 } } }, InterfaceAlias |
        Select-Object -First 1

    if ($preferred) {
        return $preferred.IPAddress
    }

    $fallback = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -notlike "127.*" -and $_.PrefixOrigin -ne "WellKnown" } |
        Select-Object -First 1

    if (-not $fallback) {
        throw "No LAN IPv4 address found. Connect this computer to Wi-Fi or LAN first."
    }

    return $fallback.IPAddress
}

function Start-PowerShellWindow {
    param(
        [string]$Title,
        [string]$Command,
        [switch]$Hidden
    )
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($Command))
    $args = @("-NoExit", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", $encoded)
    if ($Hidden) {
        Start-Process powershell -WindowStyle Hidden -ArgumentList $args
    } else {
        Start-Process powershell -ArgumentList $args
    }
    Write-Host "$Title window started." -ForegroundColor Green
}

$repoRoot = Get-RepoRoot
$mobileRoot = Join-Path $repoRoot "apps\mobile"
$pythonBundled = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$python = if (Test-Path $pythonBundled) { $pythonBundled } else { "python" }
$lanIp = Get-LanIp
$apiBaseUrl = "http://$lanIp`:$BackendPort"
$dbPath = Join-Path $repoRoot "backend\storage\mobile_qa_debug.db"
$dbUrl = "sqlite:///$($dbPath -replace '\\','/')"

Write-Host ""
Write-Host "Family Health Agent mobile QA launcher" -ForegroundColor Cyan
Write-Host "Repo: $repoRoot"
Write-Host "LAN API: $apiBaseUrl"
Write-Host "Python: $python"
Write-Host ""

if (Test-PortListening -Port $BackendPort) {
    Write-Host "Backend port $BackendPort is already listening. Reusing existing backend." -ForegroundColor Yellow
} else {
    $backendCommand = @"
`$ErrorActionPreference = 'Stop'
cd '$repoRoot'
`$env:PYTHONPATH = 'backend'
`$env:DATABASE_URL = '$dbUrl'
`$env:AUTH_DEMO_HEADER_ENABLED = 'true'
`$env:AUTH_ENABLED = 'true'
`$env:AUTH_DEMO_LOGIN_ENABLED = 'true'
`$env:JWT_SECRET_KEY = 'mobile-qa-local-dev-secret'
`$env:OCR_ENABLED = 'true'
`$env:OCR_PROVIDER = 'mock'
`$env:RAG_ENABLED = 'true'
`$env:FHA_MOBILE_QA_BACKEND = '1'
Write-Host 'Preparing mobile QA database...'
& '$python' -m alembic -c backend/alembic.ini upgrade head
if (`$LASTEXITCODE -ne 0) { exit `$LASTEXITCODE }
& '$python' backend/scripts/seed_demo_data.py
if (`$LASTEXITCODE -ne 0) { exit `$LASTEXITCODE }
Write-Host 'Starting FastAPI on 0.0.0.0:$BackendPort ...'
& '$python' -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $BackendPort
"@
    Start-PowerShellWindow -Title "Backend" -Command $backendCommand -Hidden
    Write-Host "After a few seconds, test: $apiBaseUrl/health" -ForegroundColor Green
}

if (Test-PortListening -Port $ExpoPort) {
    Write-Host "Expo/Metro port $ExpoPort is already listening. Not starting another Node process." -ForegroundColor Yellow
    Write-Host "If the old Expo env is wrong, close the old Expo window and run this launcher again." -ForegroundColor Yellow
} else {
    $expoCommand = @"
`$ErrorActionPreference = 'Stop'
cd '$mobileRoot'
`$env:EXPO_PUBLIC_DATA_MODE = '$DataMode'
`$env:EXPO_PUBLIC_AUTH_MODE = '$AuthMode'
`$env:EXPO_PUBLIC_API_BASE_URL = '$apiBaseUrl'
`$env:FHA_MOBILE_QA_EXPO = '1'
if (-not (Test-Path 'node_modules')) {
    Write-Host 'Installing mobile dependencies...'
    npm install
    if (`$LASTEXITCODE -ne 0) { exit `$LASTEXITCODE }
}
Write-Host 'Starting Expo for real-device QA...'
Write-Host 'API Base URL: $apiBaseUrl'
npx expo start --lan
"@
    Start-PowerShellWindow -Title "Expo" -Command $expoCommand
    Write-Host "Scan the QR code with Expo Go." -ForegroundColor Green
}

Write-Host ""
Write-Host "QA notes:" -ForegroundColor Cyan
Write-Host "1. Phone and computer must be on the same Wi-Fi."
Write-Host "2. Use $apiBaseUrl on the phone. Do not use localhost."
Write-Host "3. Demo login: gala.demo@example.com / DemoPass123!"
Write-Host "4. If /health does not open on the phone, allow Windows Firewall port $BackendPort."
Write-Host "5. If LAN QR scanning fails, try from apps/mobile: npx expo start --tunnel"
Write-Host ""
