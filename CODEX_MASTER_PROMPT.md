# 🤖 ARIA Project - Codex Master Prompt

> **Version:** 1.1  
> **Project:** ARIA (Adaptive Reasoning & Intelligent Automation)  
> **Language:** Implementation in English, Reports in Persian (فارسی)

---

## 🎯 PROJECT OVERVIEW

You are building **ARIA**, an Agentic AI Personal Assistant with the following core components:

| Component | Role | Tech | Local Model |
|-----------|------|------|-------------|
| **Brain** | Reasoning, Planning | LangGraph + Ollama | `qwen3-7b-instruct` |
| **Brain (فارسی)** | Persian Chat | Ollama | `aya-expanse-8b` 🆕 |
| **Brain (فارسی Reasoning)** | Persian Reasoning | Ollama | `DeepSeek-R1-Persian` |
| **Eye** | Visual Perception | VLM | `Qwen3-VL-4B-Thinking` |
| **Coder** | Code Generation | Ollama | `qwen2.5-coder-7b` |
| **Memory** | Embeddings | Sentence Transformers | `Tooka-SBERT-V2-Large` 🆕 |
| **Hand** | Execution | Playwright, pyautogui | — |
| **Learning** | Self-improvement | Kafka Event Sourcing | — |
| **Voice** | Persian STT | Whisper | `whisper-persian-v4` 🆕 |
| **Audio** | Audio Understanding | Qwen2-Audio | `Qwen2-Audio-7B` 🆕 |

**First Domain Plugin:** Job Application Automation (LinkedIn, Indeed, etc.)

---

## 🤖 LOCAL LLM MODELS (ALREADY AVAILABLE)

> **Models Path:** `E:\Programs\.ollama\models`  
> **Full Documentation:** `Docs/llm-models.md`

### Available Models (NO DOWNLOAD NEEDED)

| Usage | Model File | Ollama Name |
|-------|------------|-------------|
| **Brain (reasoning)** | `qwen3-7b-instruct-q4_k_m.gguf` | `aria-brain` |
| **Brain (فارسی chat)** 🆕 | `aya-expanse-8b-model.safetensors` | `aria-persian-chat` |
| **Brain (فارسی reasoning)** | `DeepSeek-R1-Distill-Llama-8B-Persian .gguf` | `aria-brain-persian` |
| **Eye (vision)** | `Qwen3-VL-4B-Thinking-Q4_K_M.gguf` | `aria-eye` |
| **Coder** | `qwen2.5-coder-7b-instruct-q4_k_m.gguf` | `aria-coder` |
| **Embedding** 🆕 | `Tooka-SBERT-V2-Large.safetensors` | (sentence-transformers) |
| **Persian Chat (alt)** | `gemma-3-4b-persian-v0-abliterated-q8_0.gguf` | `aria-persian` |
| **STT فارسی** 🆕 | `whisper-persian-v4-*.safetensors` | (transformers) |
| **Audio** 🆕 | `Qwen2-Audio-7B-Instruct-Q4_K_M.gguf` | `aria-audio` |

### Setup Ollama Models (REQUIRED before Phase 3)

```bash
# Create Modelfiles and register with Ollama:
cat > Modelfile.aria-brain << 'EOF'
FROM E:/Programs/.ollama/models/qwen3-7b-instruct-q4_k_m.gguf
PARAMETER temperature 0.7
EOF
ollama create aria-brain -f Modelfile.aria-brain

cat > Modelfile.aria-coder << 'EOF'
FROM E:/Programs/.ollama/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf
PARAMETER temperature 0.2
EOF
ollama create aria-coder -f Modelfile.aria-coder

cat > Modelfile.aria-eye << 'EOF'
FROM E:/Programs/.ollama/models/Qwen3-VL-4B-Thinking-Qwen3VL-4B-Thinking-Q4_K_M.gguf
PARAMETER temperature 0.1
EOF
ollama create aria-eye -f Modelfile.aria-eye
```

### ⚠️ IMPORTANT: DO NOT download other models - use what's available!

---

## 🔧 SPECIAL MODEL SETUP (REQUIRED)

Some models are in `safetensors` format and need special handling:

### 1. Aya Expanse 8B (Persian Chat) - CONVERT TO GGUF

The `aya-expanse-8b` model is in safetensors format. To use with Ollama, convert it:

```bash
# Option A: Use llama.cpp convert script
# 1. Clone llama.cpp if not already:
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp

# 2. Install requirements
pip install -r requirements.txt

# 3. Convert safetensors to GGUF
python convert_hf_to_gguf.py "E:/Programs/.ollama/models/aya-expanse-8b" \
    --outfile "E:/Programs/.ollama/models/aya-expanse-8b-Q4_K_M.gguf" \
    --outtype q4_k_m

# 4. Create Ollama model
cat > Modelfile.aria-persian-chat << 'EOF'
FROM E:/Programs/.ollama/models/aya-expanse-8b-Q4_K_M.gguf
PARAMETER temperature 0.8
PARAMETER num_predict 2000
SYSTEM "You are a helpful assistant that speaks Persian fluently."
EOF
ollama create aria-persian-chat -f Modelfile.aria-persian-chat

# Option B: Use transformers directly (no conversion needed)
# See Python code below
```

### 2. Whisper Persian V4 (STT) - USE WITH TRANSFORMERS

This model does NOT work with Ollama. Use `transformers` or `faster-whisper`:

```python
# src/aria/core/voice/stt.py

from transformers import WhisperProcessor, WhisperForConditionalGeneration
import torch

class PersianSTT:
    """Persian Speech-to-Text using whisper-persian-v4"""
    
    def __init__(self):
        self.model_name = "nezamisafa/whisper-persian-v4"
        self.processor = None
        self.model = None
    
    def load(self):
        """Load model (lazy loading)"""
        if self.model is None:
            self.processor = WhisperProcessor.from_pretrained(self.model_name)
            self.model = WhisperForConditionalGeneration.from_pretrained(self.model_name)
            
            # Use GPU if available
            if torch.cuda.is_available():
                self.model = self.model.to("cuda")
    
    def transcribe(self, audio_path: str) -> str:
        """Transcribe audio file to Persian text"""
        self.load()
        
        import librosa
        audio, sr = librosa.load(audio_path, sr=16000)
        
        inputs = self.processor(audio, sampling_rate=16000, return_tensors="pt")
        
        if torch.cuda.is_available():
            inputs = inputs.to("cuda")
        
        generated_ids = self.model.generate(inputs["input_features"])
        transcription = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        return transcription

# Usage:
# stt = PersianSTT()
# text = stt.transcribe("voice.wav")
# print(text)  # فارسی output
```

**Required packages:**
```bash
pip install transformers>=4.36.0
pip install torch>=2.0.0
pip install librosa>=0.10.0
pip install soundfile>=0.12.0
```

### 3. Tooka-SBERT-V2-Large (Embedding) - USE WITH SENTENCE-TRANSFORMERS

This model does NOT work with Ollama. Use `sentence-transformers`:

```python
# src/aria/core/memory/embedder.py

from sentence_transformers import SentenceTransformer

class PersianEmbedder:
    """Persian text embeddings using Tooka-SBERT-V2-Large"""
    
    def __init__(self):
        self.model_name = "PartAI/Tooka-SBERT-V2-Large"
        self.model = None
        self.dimensions = 1024
    
    def load(self):
        """Load model (lazy loading)"""
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
    
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts"""
        self.load()
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
    
    def embed_single(self, text: str) -> list[float]:
        """Generate embedding for single text"""
        return self.embed([text])[0]

# Usage:
# embedder = PersianEmbedder()
# vectors = embedder.embed(["متن فارسی", "another text"])
# print(len(vectors[0]))  # 1024
```

**Required packages:**
```bash
pip install sentence-transformers>=2.2.0
```

### 4. Qwen2-Audio (Audio Understanding) - ALREADY GGUF

This model is already in GGUF format and works with Ollama:

```bash
cat > Modelfile.aria-audio << 'EOF'
FROM E:/Programs/.ollama/models/Qwen2-Audio-7B-Instruct-Q4_K_M.gguf
PARAMETER temperature 0.3
EOF
ollama create aria-audio -f Modelfile.aria-audio
```

### 📋 Model Format Summary

| Model | Format | How to Use |
|-------|--------|------------|
| `qwen3-7b-instruct` | GGUF | Ollama ✓ |
| `aya-expanse-8b` | safetensors | Convert to GGUF OR use transformers |
| `DeepSeek-R1-Persian` | GGUF | Ollama ✓ |
| `Qwen3-VL-4B-Thinking` | GGUF | Ollama ✓ |
| `qwen2.5-coder-7b` | GGUF | Ollama ✓ |
| `Tooka-SBERT-V2-Large` | safetensors | sentence-transformers (NOT Ollama) |
| `whisper-persian-v4` | safetensors | transformers (NOT Ollama) |
| `Qwen2-Audio-7B` | GGUF | Ollama ✓ |
| `gemma-3-4b-persian` | GGUF | Ollama ✓ |

---

## 📚 CRITICAL DOCUMENTATION - READ FIRST

Before starting ANY phase, you MUST read and understand these documents:

```
d:\Projects\WorkFinder\Docs\
├── phases\README.md              ← START HERE (phase overview)
├── phases\phase-XX-*.md          ← Detailed steps for each phase
├── llm-models.md                 ← ⭐ LLM models guide (IMPORTANT!)
├── architecture.md               ← System architecture
├── project-structure.md          ← Folder structure
├── references-and-tools.md       ← Projects to Clone/pip/Idea
├── tool-adapter-contract.md      ← Adapter interfaces
├── event-model.md                ← Kafka event schemas
├── learning-loop.md              ← Learning system
└── ui-design.md                  ← UI specifications
```

---

## 🔒 STRICT RULES (NEVER VIOLATE)

### Rule 1: Follow Phases Sequentially
```
Phase 0 → Phase 1 → Phase 2 → ... → Phase 9
```
- **NEVER** skip phases
- **NEVER** start a phase before completing the previous one
- Each phase has prerequisites - verify them BEFORE starting

### Rule 2: Follow Steps Within Each Phase
- Each phase document (`phase-XX-*.md`) contains numbered steps
- Execute steps in order: گام ۱ → گام ۲ → گام ۳ → ...
- Each step has a **Codex Prompt** section - follow it precisely

### Rule 3: Use Correct Project Integration

| Type | Action | Location |
|------|--------|----------|
| **Clone/Vendor** | `git clone` + remove `.git` | `vendor/` folder |
| **pip install** | Add to `pyproject.toml` | dependencies |
| **Idea Only** | Study architecture, don't copy | N/A |

**Projects requiring Clone (from `references-and-tools.md`):**
- `browser-use` → `vendor/browser-use/`
- `Skyvern` → `vendor/skyvern/`
- `AIHawk` → `vendor/aihawk/`
- `OpenAdapt` → `vendor/openadapt/`

### Rule 4: Create `aria_extensions/` for Vendored Projects
When cloning a project to `vendor/`, ALWAYS create:
```
vendor/<project>/
├── UPSTREAM_VERSION.md          # Record original version/commit
└── aria_extensions/
    ├── __init__.py
    └── <integration_files>.py   # ARIA-specific customizations
```

### Rule 5: Event Sourcing is Mandatory
- ALL significant actions MUST emit Kafka events
- Use the `EventEnvelope` model from `src/aria/models/events/`
- Topics follow pattern: `{component}.{action}.v1`

### Rule 6: Human-in-the-Loop (HITL) Support
- ALL destructive/irreversible actions MUST support HITL approval
- Brain's HITL node handles approval flow
- Never auto-execute actions that could cause harm

### Rule 7: Code Quality Standards
```python
# ALWAYS follow:
- Type hints on all functions
- Docstrings (Google style)
- Async/await for I/O operations
- Pydantic models for data validation
- Structured logging with structlog
```

### Rule 8: Testing Requirements
- Unit tests for all new modules
- Integration tests for adapters
- Use `pytest` + `pytest-asyncio`

---

## 📝 PHASE COMPLETION REPORT (MANDATORY)

At the END of each phase, you MUST create a completion report.

### Report Location
```
d:\Projects\WorkFinder\Docs\phases\reports\
└── phase-XX-report.md
```

### Report Template (IN PERSIAN - فارسی)

```markdown
# 📋 گزارش تکمیل فاز X: [نام فاز]

> **تاریخ:** [تاریخ]  
> **وضعیت:** ✅ تکمیل شده | ⚠️ ناقص | ❌ متوقف شده

---

## ✅ کارهای انجام شده

### گام ۱: [عنوان]
- [x] کار ۱
- [x] کار ۲
- فایل‌های ایجاد شده:
  - `path/to/file1.py`
  - `path/to/file2.py`

### گام ۲: [عنوان]
...

---

## ❌ کارهای انجام نشده (اگر وجود دارد)

| کار | دلیل | راه‌حل پیشنهادی |
|-----|------|-----------------|
| ... | ... | ... |

---

## 🐛 مشکلات و خطاها

| خطا | علت | نحوه رفع |
|-----|-----|----------|
| ... | ... | ... |

---

## 📦 پکیج‌های نصب شده

```bash
pip install <package1>
pip install <package2>
```

---

## 🔧 فایل‌های Config ایجاد شده

- `config/xyz.yaml`
- `.env` updates

---

## 🧪 تست‌ها

| تست | نتیجه |
|-----|-------|
| Unit tests | ✅/❌ |
| Integration tests | ✅/❌ |

```bash
# دستور اجرای تست‌ها
pytest tests/unit/... -v
```

---

## 📊 وضعیت نهایی

- [ ] همه گام‌ها تکمیل شده
- [ ] تست‌ها پاس شده
- [ ] Linting errors رفع شده
- [ ] Documentation به‌روز شده
- [ ] آماده برای فاز بعدی

---

## 🚀 گام بعدی

فاز بعدی: **Phase X+1: [نام]**
پیش‌نیاز: [چک‌لیست]
```

---

## 🚀 HOW TO START

### Step 1: Read Phase 0 Document
```
Read: d:\Projects\WorkFinder\Docs\phases\phase-00-foundation.md
```

### Step 2: Verify Prerequisites
Before starting Phase 0, verify:
- [ ] Python 3.11+ installed
- [ ] Docker Desktop installed and running
- [ ] Git installed
- [ ] Ollama installed (optional for Phase 0)

### Step 3: Execute Steps
Follow each "گام" (step) in order, using the Codex Prompt provided.

### Step 4: Create Report
After completing all steps, create:
```
d:\Projects\WorkFinder\Docs\phases\reports\phase-00-report.md
```

### Step 5: Move to Next Phase
Only after Phase 0 report is complete, proceed to Phase 1.

---

## 🛠️ WORKSPACE STRUCTURE (Target)

```
d:\Projects\WorkFinder\
├── src\aria\                    # Main source code
│   ├── core\                    # Brain, Eye, Hand, Memory, Learning, Voice
│   ├── adapters\                # Kafka, Redis, Browser, Desktop
│   ├── plugins\                 # Domain plugins (job_apply, etc.)
│   ├── models\                  # Pydantic models
│   ├── api\                     # FastAPI endpoints
│   ├── ui\                      # Streamlit UI
│   └── utils\                   # Utilities
├── vendor\                      # Cloned third-party projects
│   ├── browser-use\
│   ├── skyvern\
│   ├── aihawk\
│   └── openadapt\
├── config\                      # YAML configurations
├── tests\                       # Test suites
├── data\                        # Runtime data (screenshots, etc.)
├── Docs\                        # Documentation
│   └── phases\reports\          # Phase completion reports
├── docker-compose.yml
├── pyproject.toml
├── Makefile
└── .env
```

---

## ⚠️ COMMON MISTAKES TO AVOID

| Mistake | Correct Approach |
|---------|------------------|
| Skipping prerequisites check | ALWAYS verify prerequisites first |
| Not creating `aria_extensions/` | ALWAYS create for vendored projects |
| Missing event emission | ALWAYS emit Kafka events for actions |
| Hardcoding values | ALWAYS use config files |
| Sync I/O in async code | ALWAYS use async/await |
| Missing type hints | ALWAYS add type hints |
| Forgetting phase report | ALWAYS create report at phase end |

---

## 💬 COMMUNICATION

- **Code:** English
- **Comments:** English  
- **Docstrings:** English
- **Reports:** Persian (فارسی)
- **Commit messages:** English

---

## 🎬 BEGIN

Start by reading:
```
d:\Projects\WorkFinder\Docs\phases\README.md
```

Then proceed to:
```
d:\Projects\WorkFinder\Docs\phases\phase-00-foundation.md
```

**Good luck building ARIA!** 🚀
