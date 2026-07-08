$ErrorActionPreference = "Continue"

$ports = @(8000, 8081, 19000, 19001, 19002)
$processIds = New-Object System.Collections.Generic.HashSet[int]

foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        [void]$processIds.Add([int]$connection.OwningProcess)
    }
}

foreach ($processId in $processIds) {
    try {
        $process = Get-Process -Id $processId -ErrorAction Stop
        Write-Host "Stopping PID $processId ($($process.ProcessName)) on mobile QA port..."
        Stop-Process -Id $processId -Force
    } catch {
        Write-Host "PID $processId is no longer running."
    }
}

if ($processIds.Count -eq 0) {
    Write-Host "No mobile QA backend or Expo ports are currently listening."
}

Write-Host "Mobile QA debug processes stopped."
