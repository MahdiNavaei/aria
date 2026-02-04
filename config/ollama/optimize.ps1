# Ollama Performance Optimization Script for Windows
# Run this BEFORE starting Ollama

Write-Host "🚀 Applying Ollama Performance Optimizations..." -ForegroundColor Cyan

# 1. Flash Attention - بهبود حافظه و سرعت attention
$env:OLLAMA_FLASH_ATTENTION = "1"

# 2. Keep Alive - نگه داشتن مدل در حافظه (نه unload شدن)
$env:OLLAMA_KEEP_ALIVE = "-1"

# 3. Max Loaded Models - فقط یک مدل در حافظه
$env:OLLAMA_MAX_LOADED_MODELS = "1"

# 4. Parallel Requests - فقط یک درخواست (کمتر = سریعتر)
$env:OLLAMA_NUM_PARALLEL = "1"

# 5. Context Length کوتاه‌تر = سرعت بیشتر
$env:OLLAMA_CONTEXT_LENGTH = "2048"

# 6. GPU Layers - همه لایه‌ها روی GPU
$env:OLLAMA_GPU_LAYERS = "99"

# 7. مسیر مدل‌ها (SSD)
$env:OLLAMA_MODELS = "E:\Programs\.ollama\models"

# 8. CUDA optimization
$env:CUDA_VISIBLE_DEVICES = "0"

Write-Host "✅ Environment variables set:" -ForegroundColor Green
Write-Host "   OLLAMA_FLASH_ATTENTION = 1" -ForegroundColor Yellow
Write-Host "   OLLAMA_KEEP_ALIVE = -1 (never unload)" -ForegroundColor Yellow
Write-Host "   OLLAMA_MAX_LOADED_MODELS = 1" -ForegroundColor Yellow
Write-Host "   OLLAMA_NUM_PARALLEL = 1" -ForegroundColor Yellow
Write-Host "   OLLAMA_CONTEXT_LENGTH = 2048" -ForegroundColor Yellow
Write-Host "   OLLAMA_GPU_LAYERS = 99" -ForegroundColor Yellow

Write-Host ""
Write-Host "🔄 Restarting Ollama service..." -ForegroundColor Cyan

# Stop and restart Ollama
taskkill /IM ollama.exe /F 2>$null
Start-Sleep -Seconds 2
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden

Write-Host "✅ Ollama restarted with optimizations!" -ForegroundColor Green
Write-Host ""
Write-Host "📌 To preload model, run:" -ForegroundColor Magenta
Write-Host '   ollama run aria-persian-chat ""' -ForegroundColor White
