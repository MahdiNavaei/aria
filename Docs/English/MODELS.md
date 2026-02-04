# 🤖 LLM Models Setup Guide

> **Important:** LLM model files are **not included** in this repository due to their large size (several GB each). You need to download them separately.

---

## 📋 Quick Start

1. **Install Ollama** (if not already installed):
   ```bash
   # Windows (PowerShell)
   winget install Ollama.Ollama
   
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Download required models** using the links below or the automated script.

3. **Register models in Ollama** with the names ARIA expects (see below).

4. **Configure model paths** in `config/llm.yaml` (see Configuration section).

---

## 🧠 Required Models

### Core Models (MVP - Minimum Required)

| Component | Model | Size | Download Source | Status |
|-----------|-------|------|-----------------|--------|
| **Brain** | `qwen3-7b-instruct-q4_k_m` | ~4.5 GB | [HuggingFace](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) or [Ollama](https://ollama.com/library/qwen2.5:7b) | ✅ Required |
| **Eye** | `Qwen3-VL-4B-Thinking` | ~3 GB | [HuggingFace](https://huggingface.co/Qwen/Qwen3-VL-4B-Thinking) | ✅ Required |
| **Embedding** | `Tooka-SBERT-V2-Large` | ~400 MB | [HuggingFace](https://huggingface.co/PartAI/Tooka-SBERT-V2-Large) | ✅ Required |

### Optional Models (Enhanced Features)

| Component | Model | Size | Download Source | Use Case |
|-----------|-------|------|-----------------|----------|
| **Brain (Persian)** | `aya-expanse-8b` | ~5.5 GB | [HuggingFace](https://huggingface.co/CohereForAI/aya-expanse-8b) | Persian chat/cover letters |
| **Eye (OCR Persian)** | `Qwen3-VL-2B-Persian-Arabic-Ocr` | ~2 GB | [HuggingFace](https://huggingface.co/mohajesmaeili/Qwen3-VL-2B-Persian-Arabic-Ocr-v1.0) | Persian text extraction |
| **Coder** | `qwen2.5-coder-7b-instruct` | ~4.5 GB | [HuggingFace](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct) | Code generation |
| **STT (Persian)** | `whisper-persian-v4` | ~1.5 GB | [HuggingFace](https://huggingface.co/nezamisafa/whisper-persian-v4) | Speech-to-text (Persian) |

---

## 📥 Download Methods

### Method 1: Using Ollama (Recommended for GGUF models)

```bash
# Core models - these will be registered with default names
ollama pull qwen2.5:7b
ollama pull qwen2.5-coder:7b

# Note: Vision models (Qwen3-VL) may need manual download from HuggingFace
```

**Important:** After pulling models, you need to create custom model names that ARIA expects. See "Registering Models in Ollama" below.

### Method 2: Direct Download from HuggingFace

#### For GGUF models:
1. Visit the model page on HuggingFace
2. Go to "Files and versions" tab
3. Download the `.gguf` file (usually Q4_K_M quantization)
4. Place it in your Ollama models directory:
   ```bash
   # Windows (default)
   E:\Programs\.ollama\models\
   # or
   C:\Users\<YourUser>\.ollama\models\
   
   # Linux/macOS (default)
   ~/.ollama/models/
   ```
5. Register the model in Ollama (see below)

#### For safetensors models (need conversion):
1. Download from HuggingFace
2. Convert to GGUF using `llama.cpp`:
   ```bash
   git clone https://github.com/ggerganov/llama.cpp.git
   cd llama.cpp
   pip install -r requirements.txt
   
   python convert_hf_to_gguf.py <model_path> \
       --outfile <output_path>.gguf \
       --outtype q4_k_m
   ```
3. Place the `.gguf` file in Ollama models directory
4. Register the model in Ollama (see below)

### Method 3: Automated Download Script

We provide a Python script to automate model downloads:

```bash
# Install required dependencies
pip install huggingface-hub sentence-transformers

# Run the download script
python scripts/download_models.py --models core
# or
python scripts/download_models.py --models all
```

See `scripts/download_models.py` for details.

---

## 🔧 Registering Models in Ollama

**Critical:** ARIA expects models to be registered in Ollama with specific names. After downloading model files, you must create Ollama model aliases.

### Step 1: Find Your Ollama Models Directory

```bash
# Check Ollama's default models path
ollama show --modelfile

# Or check environment variable
echo $OLLAMA_MODELS_PATH  # Linux/macOS
echo %OLLAMA_MODELS_PATH%  # Windows
```

Default locations:
- **Windows**: `C:\Users\<YourUser>\.ollama\models\` or `E:\Programs\.ollama\models\`
- **Linux/macOS**: `~/.ollama/models/`

### Step 2: Create Modelfiles

Create a Modelfile for each model ARIA needs:

```bash
# For Brain model (qwen3-7b-instruct)
cat > Modelfile.aria-brain << 'EOF'
FROM qwen2.5:7b
PARAMETER temperature 0.7
PARAMETER num_predict 2000
PARAMETER num_ctx 8192
EOF

ollama create aria-brain -f Modelfile.aria-brain

# For Eye model (Qwen3-VL-4B-Thinking)
# First, download the GGUF file manually, then:
cat > Modelfile.aria-eye << 'EOF'
FROM /path/to/Qwen3-VL-4B-Thinking-Q4_K_M.gguf
PARAMETER temperature 0.1
PARAMETER num_predict 1000
PARAMETER num_ctx 2048
EOF

ollama create aria-eye -f Modelfile.aria-eye

# For Persian Brain (aya-expanse-8b)
cat > Modelfile.aria-persian-chat << 'EOF'
FROM /path/to/aya-expanse-8b-Q4_K_M.gguf
PARAMETER temperature 0.8
PARAMETER num_predict 2000
SYSTEM "You are a helpful assistant that speaks Persian fluently."
EOF

ollama create aria-persian-chat -f Modelfile.aria-persian-chat

# For Coder model
cat > Modelfile.aria-coder << 'EOF'
FROM qwen2.5-coder:7b
PARAMETER temperature 0.2
PARAMETER num_predict 4000
PARAMETER num_ctx 8192
EOF

ollama create aria-coder -f Modelfile.aria-coder
```

### Step 3: Verify Models Are Registered

```bash
# List all registered models
ollama list

# You should see:
# aria-brain
# aria-eye
# aria-persian-chat (optional)
# aria-coder (optional)

# Test a model
ollama run aria-brain "Hello, what is 2+2?"
```

---

## ⚙️ Configuration

### Option 1: Using config/llm.yaml (Recommended)

Edit `config/llm.yaml`:

```yaml
llm:
  provider: ollama
  models_path: "~/.ollama/models"  # Default: ~/.ollama/models (Linux/macOS) or C:\Users\<User>\.ollama\models (Windows)
  
  ollama:
    base_url: http://localhost:11434
    
    models:
      # These names must match the Ollama model names you created above
      brain: aria-brain                    # Required
      brain_persian: aria-persian-chat     # Optional
      brain_persian_reasoning: aria-brain-persian  # Optional
      eye: aria-eye                        # Required
      coder: aria-coder                    # Optional
      embedding: null                      # Uses sentence-transformers, not Ollama
      audio: null                          # Not used currently
```

**Important:** The model names in `config/llm.yaml` (e.g., `aria-brain`, `aria-eye`) must match the names you registered in Ollama using `ollama create`.

### Option 2: Using Environment Variables

You can override model names using environment variables in `.env`:

```bash
# Model names (must match Ollama registered names)
OLLAMA_MODEL_BRAIN=aria-brain
OLLAMA_MODEL_BRAIN_PERSIAN=aria-persian-chat
OLLAMA_MODEL_EYE=aria-eye
OLLAMA_MODEL_CODER=aria-coder

# Base URL
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 🔄 Using Different Models

ARIA fully supports using different models than the defaults. The system uses **Ollama model names** (not file paths), so you can use any model that Ollama supports.

### Step 1: Download Your Preferred Model

Download any compatible model:
- From Ollama library: `ollama pull <model-name>`
- From HuggingFace: Download GGUF file and place in Ollama directory
- Any other source: Convert to GGUF format if needed

### Step 2: Register in Ollama

Create a Modelfile and register with a custom name:

```bash
# Example 1: Using Llama 3 instead of Qwen for Brain
cat > Modelfile.my-brain << 'EOF'
FROM llama3:8b
PARAMETER temperature 0.7
PARAMETER num_predict 2000
PARAMETER num_ctx 8192
EOF

ollama create my-brain -f Modelfile.my-brain

# Example 2: Using a local GGUF file
cat > Modelfile.my-eye << 'EOF'
FROM /path/to/your/vision-model.gguf
PARAMETER temperature 0.1
PARAMETER num_predict 1000
EOF

ollama create my-eye -f Modelfile.my-eye
```

### Step 3: Update Configuration

**Option A: Update `config/llm.yaml`**

```yaml
llm:
  ollama:
    models:
      brain: my-brain      # Your custom model name
      eye: my-eye          # Your custom vision model
      # ... other models
```

**Option B: Use Environment Variables (in `.env`)**

```bash
OLLAMA_MODEL_BRAIN=my-brain
OLLAMA_MODEL_EYE=my-eye
OLLAMA_MODEL_CODER=my-coder
```

Environment variables override `config/llm.yaml` settings.

### Step 4: Verify Model Works

```bash
# 1. Test model directly in Ollama
ollama run my-brain "Hello, what is 2+2?"

# 2. Verify ARIA can access it
python -c "
import asyncio
from aria.core.llm import get_llm_client
from aria.core.llm.base import ModelRole, Message

async def test():
    client = get_llm_client()
    response = await client.generate(
        [Message(role='user', content='Hello')],
        role=ModelRole.BRAIN
    )
    print(f'Model: {response.model}')
    print(f'Response: {response.content[:100]}')

asyncio.run(test())
"
```

### Model Compatibility Notes

- **Brain models**: Should support instruction following and reasoning
- **Eye models**: Must support vision (VLM) - can process images
- **Coder models**: Should be code-specialized for best results
- **All models**: Must be compatible with Ollama's API format

### Using Cloud Models (OpenAI/Anthropic)

ARIA also supports cloud providers:

```yaml
llm:
  provider: openai  # or "anthropic"
  api_key: "sk-..."  # Set in .env as OPENAI_API_KEY or ANTHROPIC_API_KEY
```

See `config/llm.yaml` for cloud provider configuration options.

---

## 📁 Model File Structure

After setup, your Ollama models directory should look like:

```
.ollama/models/
├── qwen3-7b-instruct-q4_k_m.gguf          # Brain (referenced as aria-brain)
├── Qwen3-VL-4B-Thinking-Q4_K_M.gguf       # Eye (referenced as aria-eye)
├── Qwen3-VL-4B-Thinking-mmproj-F16.gguf   # Eye (mmproj file)
├── qwen2.5-coder-7b-instruct-q4_k_m.gguf  # Coder (referenced as aria-coder)
└── aya-expanse-8b-Q4_K_M.gguf             # Persian Brain (referenced as aria-persian-chat)
```

**Note:** The actual file names don't matter - what matters is the names you register in Ollama (`aria-brain`, `aria-eye`, etc.).

---

## ✅ Verification

Test that models are correctly installed and configured:

```bash
# 1. Verify Ollama is running
ollama serve

# 2. List registered models
ollama list

# 3. Test Brain model
ollama run aria-brain "What is 2+2? Think step by step."

# 4. Test Vision model (if downloaded)
ollama run aria-eye "Describe this image" --images screenshot.png

# 5. Test Embedding model (Python)
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('PartAI/Tooka-SBERT-V2-Large')
print('Embedding model loaded successfully!')
"

# 6. Verify ARIA can access models
python -c "
from aria.config import get_settings
settings = get_settings()
print(f'Brain model: {settings.llm.ollama.models.brain}')
print(f'Eye model: {settings.llm.ollama.models.eye}')
"
```

---

## 📚 Detailed Documentation

For comprehensive model information, including:
- Model specifications and capabilities
- Performance benchmarks
- Usage examples
- Troubleshooting

See: **[Docs/English/llm-models.md](Docs/English/llm-models.md)**

For model management strategies (loading, unloading, VRAM optimization):
See: **[Docs/English/model-management-strategy.md](Docs/English/model-management-strategy.md)**

---

## ⚠️ Important Notes

1. **Storage Requirements**: 
   - Core models: ~8 GB
   - All models: ~20+ GB
   - Ensure sufficient disk space

2. **RAM/VRAM Requirements**:
   - Minimum: 8 GB RAM
   - Recommended: 16 GB RAM + 8 GB VRAM (GPU)
   - See [Docs/English/model-management-strategy.md](Docs/English/model-management-strategy.md) for optimization tips

3. **Model Formats**:
   - **GGUF**: Ready for Ollama, no conversion needed
   - **safetensors**: Need conversion to GGUF for Ollama
   - **PyTorch (.pt/.pth)**: Use with transformers library directly

4. **Model Names Matter**: 
   - ARIA uses **Ollama model names** (like `aria-brain`), not file names
   - You must register models in Ollama with the names specified in `config/llm.yaml`
   - You can use different models by changing the names in config

5. **License Compliance**: 
   - Check each model's license before commercial use
   - Some models may have usage restrictions

---

## 🆘 Troubleshooting

### Model not found

**Problem:** ARIA can't find the model.

**Solutions:**
1. Check that the model is registered in Ollama:
   ```bash
   ollama list
   ```
   You should see the model name (e.g., `aria-brain`)

2. Verify the model name in `config/llm.yaml` matches the Ollama name:
   ```yaml
   models:
     brain: aria-brain  # Must match ollama list output
   ```

3. Check Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

4. Verify model files exist in Ollama directory:
   ```bash
   # Windows
   dir E:\Programs\.ollama\models\
   # Linux/macOS
   ls ~/.ollama/models/
   ```

### Model name mismatch

**Problem:** Config says `aria-brain` but Ollama has `qwen2.5:7b`.

**Solution:** Either:
- Create an alias: `ollama create aria-brain -f Modelfile.aria-brain` (see above)
- Or change config to use the actual Ollama name: `brain: qwen2.5:7b`

### Out of Memory (OOM)

- Use smaller quantization (Q4 instead of Q8)
- Reduce context window size (`num_ctx` in Modelfile)
- See [model-management-strategy.md](Docs/English/model-management-strategy.md) for VRAM optimization

### Download fails

- Check internet connection
- Verify HuggingFace access (may need login)
- Try downloading manually from browser
- For large models, consider using `huggingface-cli` with resume capability

### Using custom models

If you want to use different models:

1. Download your preferred model
2. Register it in Ollama with a name (e.g., `ollama create my-model -f Modelfile`)
3. Update `config/llm.yaml` to use your model name:
   ```yaml
   models:
     brain: my-model  # Your custom model name
   ```
4. Restart ARIA

---

## 📝 Summary Checklist

- [ ] Ollama installed and running
- [ ] Model files downloaded to Ollama directory
- [ ] Models registered in Ollama with correct names (`aria-brain`, `aria-eye`, etc.)
- [ ] `config/llm.yaml` updated with model names
- [ ] Models verified with `ollama list` and `ollama run`
- [ ] ARIA can access models (test with verification script)

---

**Last Updated**: 2026-02-04  
**For questions or issues**: Open an issue on GitHub
