param(
  [string]$Python = ".\.venv-smoke\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Python)) {
  $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
  if ($pythonCommand) {
    $Python = $pythonCommand.Source
  }
}

$env:PYTHONPATH = "backend"
& $Python scripts/smoke/llm_provider_smoke.py
