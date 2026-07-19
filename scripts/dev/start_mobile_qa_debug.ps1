param(
    [int]$BackendPort = 8000,
    [int]$ExpoPort = 8081,
    [string]$DataMode = "api",
    [string]$AuthMode = "auth"
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Get-BackendPython {
    param([string]$RepoRoot)

    $venvRoot = Join-Path $RepoRoot "backend\.venv"
    $venvPython = Join-Path $venvRoot "Scripts\python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }

    Write-Host "Preparing the local backend Python environment (first run only)..." -ForegroundColor Yellow
    & python -m venv $venvRoot
    if ($LASTEXITCODE -ne 0) { throw "Could not create backend/.venv." }

    & $venvPython -m pip install --disable-pip-version-check --quiet `
        alembic fastapi httpx langgraph "psycopg[binary]" pydantic-settings SQLAlchemy "uvicorn[standard]"
    if ($LASTEXITCODE -ne 0) { throw "Could not install backend dependencies." }
    return $venvPython
}

function Test-PortListening {
    param([int]$Port)
    $conn = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    return $null -ne $conn
}

function Stop-PortListeners {
    param(
        [int]$Port,
        [string]$ServiceName
    )

    $connections = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    $processIds = @($connections | Select-Object -ExpandProperty OwningProcess -Unique)
    foreach ($processId in $processIds) {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "Stopping existing $ServiceName on port $Port (PID $processId)..." -ForegroundColor Yellow
            Stop-Process -Id $processId -Force
        }
    }
}

function Wait-ForBackend {
    param([string]$HealthUrl)

    for ($attempt = 1; $attempt -le 45; $attempt++) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $HealthUrl -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                return
            }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    throw "QA backend did not become healthy: $HealthUrl"
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
$python = Get-BackendPython -RepoRoot $repoRoot
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

Stop-PortListeners -Port $BackendPort -ServiceName "backend"
if (Test-Path $dbPath) {
    Remove-Item -LiteralPath $dbPath -Force
}
$backendCommand = @"
`$ErrorActionPreference = 'Stop'
cd '$repoRoot'
`$env:PYTHONPATH = 'backend'
`$env:DATABASE_URL = '$dbUrl'
`$env:AUTH_DEMO_HEADER_ENABLED = 'false'
`$env:AUTH_ENABLED = 'true'
`$env:AUTH_DEMO_LOGIN_ENABLED = 'false'
`$env:JWT_SECRET_KEY = 'mobile-qa-local-dev-secret'
`$env:OCR_ENABLED = 'true'
`$env:OCR_PROVIDER = 'mock'
`$env:RAG_ENABLED = 'true'
`$env:FHA_MOBILE_QA_BACKEND = '1'
# Keep project-local .env as the source of LLM configuration for this launcher.
# This avoids inherited machine-level provider settings selecting another project account.
foreach (`$name in @(
    'LLM_ENABLED', 'LLM_PROVIDER', 'LLM_BASE_URL', 'LLM_API_KEY', 'LLM_MODEL',
    'LLM_TIMEOUT_SECONDS', 'LLM_MAX_TOKENS', 'LLM_TEMPERATURE',
    'DAILY_BRIEF_USE_LLM', 'LLM_PLANNER_ENABLED', 'LLM_ANSWER_COMPOSER_ENABLED',
    'LLM_CRITIC_ENABLED', 'LANGGRAPH_ENABLED', 'LANGGRAPH_CHAT_QUERY_ENABLED',
    'LANGGRAPH_DAILY_BRIEF_ENABLED', 'LANGGRAPH_FREE_TEXT_RECORD_ENABLED',
    'LANGGRAPH_DOCTOR_VISIT_SUMMARY_ENABLED', 'LANGGRAPH_DOCUMENT_EXTRACT_ENABLED',
    'LANGGRAPH_DAILY_REPORT_ENABLED', 'LANGGRAPH_HEALTH_KNOWLEDGE_QA_ENABLED',
    'LANGGRAPH_ALERT_CREATE_ENABLED', 'LANGGRAPH_SYMPTOM_DRAFT_CREATE_ENABLED',
    'LANGGRAPH_MEDICAL_EVENT_DRAFT_CREATE_ENABLED', 'LANGGRAPH_STRICT_MODE'
)) {
    Remove-Item "Env:`$name" -ErrorAction SilentlyContinue
}
Write-Host 'Preparing mobile QA database...'
& '$python' -m alembic -c backend/alembic.ini upgrade head
if (`$LASTEXITCODE -ne 0) { exit `$LASTEXITCODE }
Write-Host 'Starting FastAPI on 0.0.0.0:$BackendPort ...'
& '$python' -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $BackendPort
"@
Start-PowerShellWindow -Title "Backend" -Command $backendCommand -Hidden
Wait-ForBackend -HealthUrl "$apiBaseUrl/health"
Write-Host "QA backend is ready with an empty local database." -ForegroundColor Green

Stop-PortListeners -Port $ExpoPort -ServiceName "Expo/Metro"
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
Write-Host "Scan the new QR code with Expo Go." -ForegroundColor Green

Write-Host ""
Write-Host "QA notes:" -ForegroundColor Cyan
Write-Host "1. Phone and computer must be on the same Wi-Fi."
Write-Host "2. Use $apiBaseUrl on the phone. Do not use localhost."
Write-Host "3. Create an account from the registration screen, then log in."
Write-Host "4. If /health does not open on the phone, allow Windows Firewall port $BackendPort."
Write-Host "5. If LAN QR scanning fails, try from apps/mobile: npx expo start --tunnel"
Write-Host ""
