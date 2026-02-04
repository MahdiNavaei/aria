$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path vendor | Out-Null

function Clone-Repo {
    param(
        [string]$Name,
        [string]$Url
    )

    $dest = Join-Path "vendor" $Name
    if (Test-Path $dest) {
        Write-Host "$dest already exists, skipping"
        return
    }

    git clone $Url $dest
    Push-Location $dest
    git rev-parse HEAD | Out-File -FilePath UPSTREAM_VERSION.md -Encoding ascii
    Remove-Item -Recurse -Force .git
    New-Item -ItemType Directory -Force -Path aria_extensions | Out-Null
    New-Item -ItemType File -Force -Path aria_extensions\__init__.py | Out-Null
    Pop-Location
}

Clone-Repo -Name "aihawk" -Url "https://github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk"
Clone-Repo -Name "skyvern" -Url "https://github.com/Skyvern-AI/skyvern"
Clone-Repo -Name "browser-use" -Url "https://github.com/browser-use/browser-use"
Clone-Repo -Name "openadapt" -Url "https://github.com/OpenAdaptAI/OpenAdapt"

Write-Host "Vendor clone complete"
