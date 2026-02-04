$ErrorActionPreference = "Stop"

docker compose up -d

$services = @("aria-redpanda", "aria-redis", "aria-qdrant")
foreach ($svc in $services) {
    Write-Host "Waiting for $svc to be healthy..."
    while ($true) {
        $status = docker inspect -f '{{.State.Health.Status}}' $svc 2>$null
        if ($status -eq "healthy") { break }
        Start-Sleep -Seconds 2
    }
    Write-Host "$svc is healthy"
}

if (-not $env:DEV_CMD) {
    Write-Host "Set DEV_CMD to start the dev server (example: uvicorn aria.api.rest.app:app --reload)"
    exit 0
}

Invoke-Expression $env:DEV_CMD
