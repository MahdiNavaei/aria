$ErrorActionPreference = "Stop"

$version = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$parts = $version.Split(".")
if ([int]$parts[0] -lt 3 -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -lt 11)) {
    throw "Python 3.11+ is required"
}
Write-Host "Python $version detected"

if (-not (Test-Path .venv)) {
    python -m venv .venv
}

. .\.venv\Scripts\Activate.ps1

pip install -e ".[dev]"
pre-commit install
pre-commit install --hook-type commit-msg
playwright install

if (-not (Test-Path .env) -and (Test-Path .env.example)) {
    Copy-Item .env.example .env
}

Write-Host "Setup complete. Activate venv with: .\.venv\Scripts\Activate.ps1"
