FROM E:/Programs/.ollama/models/Qwen3-VL-4B-Thinking-Qwen3VL-4B-Thinking-Q4_K_M.gguf

# === SPEED OPTIMIZATIONS ===
PARAMETER num_gpu 99
PARAMETER num_ctx 1024
PARAMETER num_batch 512
PARAMETER num_thread 8

# === GENERATION SETTINGS ===
PARAMETER temperature 0.1
PARAMETER num_predict 256
PARAMETER top_p 0.9

SYSTEM """You are Eye. Output JSON with UI elements."""
