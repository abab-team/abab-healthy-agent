$ErrorActionPreference = "Stop"

param(
    [Parameter(Mandatory = $true)]
    [string]$ApiBaseUrl
)

$base = $ApiBaseUrl.TrimEnd("/")
if ($base -match "localhost|127\.0\.0\.1") {
    throw "For Expo Go real-device QA, use the computer LAN IP instead of localhost or 127.0.0.1."
}

$healthUrl = "$base/health"
Write-Host "Checking $healthUrl"
$response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 10
if ($response.StatusCode -ne 200) {
    throw "Expected HTTP 200 from /health, got $($response.StatusCode)."
}

Write-Host "mobile_lan_api_smoke ok: $($response.StatusCode)"

