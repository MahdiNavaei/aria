# ARIA Startup Script with Model Preloading
# This script starts Ollama with optimizations and preloads models

Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "ARIA Startup Script" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan

# Step 1: Set Environment Variables
Write-Host "`n📋 Setting Ollama optimizations..." -ForegroundColor Yellow
$env:OLLAMA_FLASH_ATTENTION = "1"
$env:OLLAMA_KEEP_ALIVE = "-1"
$env:OLLAMA_NUM_PARALLEL = "1"
$env:OLLAMA_MAX_LOADED_MODELS = "1"
$env:OLLAMA_MODELS = "E:\Programs\.ollama\models"

# Step 2: Restart Ollama
Write-Host "🔄 Restarting Ollama..." -ForegroundColor Yellow
taskkill /IM ollama.exe /F 2>$null
Start-Sleep -Seconds 2
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
Start-Sleep -Seconds 5

# Step 3: Preload Primary Model
Write-Host "`n🔥 Preloading aria-persian-chat model..." -ForegroundColor Yellow
Write-Host "   (This may take 30-60 seconds on first load)" -ForegroundColor DarkGray

$start = Get-Date
try {
    $body = '{"model":"aria-persian-chat","prompt":"hi","stream":false,"options":{"num_predict":1},"keep_alive":-1}'
    
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 120
    $elapsed = ((Get-Date) - $start).TotalSeconds
    Write-Host "✅ Model preloaded in $([math]::Round($elapsed, 1)) seconds" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to preload model: $_" -ForegroundColor Red
}

# Step 4: Verify GPU Usage
Write-Host "`n📊 GPU Status:" -ForegroundColor Yellow
nvidia-smi --query-gpu=name,memory.used,memory.free,utilization.gpu --format=csv,noheader

# Step 5: Check Loaded Models
Write-Host "`n📦 Loaded Models:" -ForegroundColor Yellow
ollama ps

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "ARIA is ready! Run: streamlit run src/aria/ui/app.py" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Cyan
