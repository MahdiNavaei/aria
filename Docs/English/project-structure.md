---
title: "Project Structure"
version: v4
date: "2026-02-02"
---

# Project Structure

This document defines the **folder structure** of the project, which is **extensible**, **readable**, and **scalable**.

**Key Principle:** Code should be as readable as documentation — each file has one responsibility, each folder represents one domain.

---

## 1) Overall Structure

```
aria/                               # Project name: ARIA
├── README.md                       # Project introduction
├── LICENSE
├── pyproject.toml                  # Python project config (Poetry/PDM)
├── setup.py                        # Backward compat (optional)
│
├── .env.example                    # Environment variables template
├── .gitignore
├── .pre-commit-config.yaml         # Pre-commit hooks
│
├── Makefile                        # Common commands (make test, make run)
├── docker-compose.yml              # Development services
├── Dockerfile                      # Production image
│
├── config/                         # 📁 Configuration files
│   ├── default.yaml               # Default settings
│   ├── development.yaml           # Override for dev
│   ├── production.yaml            # Override for prod
│   ├── logging.yaml               # Logging config
│   ├── llm.yaml                   # 🆕 LLM/Brain models config
│   ├── memory.yaml                # Memory system config
│   ├── voice.yaml                 # 🆕 Voice/STT config
│   ├── kafka.yaml                 # Kafka/Redpanda config
│   └── redis.yaml                 # Redis config
│
├── Docs/                           # 📁 Documentation
│   ├── README.md                  # Documentation index
│   ├── architecture.md
│   ├── extensibility-architecture.md
│   └── ...                        # Other documentation
│
├── src/                            # 📁 Source code
│   └── aria/                      # Main package
│       ├── __init__.py
│       ├── __main__.py            # Entry point: python -m aria
│       ├── version.py             # Version info
│       │
│       ├── core/                  # 📁 Core components (domain-agnostic)
│       │   ├── __init__.py
│       │   ├── brain/             # Planning & reasoning
│       │   ├── memory/            # Unified memory system (+ embedder.py)
│       │   ├── voice/             # 🆕 Voice/STT (Persian: whisper-persian-v4)
│       │   ├── eye/               # Visual perception (VLM)
│       │   ├── hand/              # Execution adapters
│       │   ├── router/            # Task routing
│       │   ├── events/            # Event bus
│       │   ├── safety/            # Safety policies
│       │   └── schemas/           # Shared data models
│       │
│       ├── plugins/               # 📁 Domain plugins
│       │   ├── __init__.py        # Plugin registry
│       │   ├── base.py            # DomainPlugin interface
│       │   ├── job_apply/         # Job Apply domain
│       │   ├── cursor/            # Cursor domain
│       │   └── desktop/           # Desktop domain
│       │
│       ├── adapters/              # 📁 External tool adapters
│       │   ├── __init__.py
│       │   ├── playwright/        # Browser automation
│       │   ├── ollama/            # LLM integration
│       │   ├── pyautogui/         # Desktop automation
│       │   ├── kafka/             # Event bus (Kafka/Redpanda)
│       │   └── redis/             # Cache/state store
│       │
│       ├── api/                   # 📁 External interfaces
│       │   ├── __init__.py
│       │   ├── rest/              # REST API (FastAPI)
│       │   ├── websocket/         # WebSocket for UI streaming
│       │   └── cli/               # CLI interface
│       │
│       ├── ui/                    # 📁 User Interface
│       │   ├── __init__.py
│       │   ├── app.py             # Main Streamlit/Gradio app (MVP)
│       │   ├── components/        # UI components
│       │   │   ├── live_view.py   # Live browser screenshot
│       │   │   ├── activity_log.py# Execution log
│       │   │   ├── hitl_panel.py  # Human intervention panel
│       │   │   ├── chat_panel.py  # Chat/command interface
│       │   │   └── status_bar.py  # Header status
│       │   ├── pages/             # UI pages
│       │   │   ├── dashboard.py   # Main dashboard
│       │   │   ├── history.py     # Session history
│       │   │   ├── analytics.py   # Analytics dashboard
│       │   │   └── settings.py    # Settings page
│       │   ├── styles/            # CSS styles
│       │   │   ├── main.css
│       │   │   └── rtl.css        # Persian RTL support
│       │   └── locales/           # Translations
│       │       ├── en.json
│       │       └── fa.json        # Persian
│       │
│       └── utils/                 # 📁 Utilities
│           ├── __init__.py
│           ├── config.py          # Config loading
│           ├── logging.py         # Logging setup
│           └── helpers.py         # Misc helpers
│
├── tests/                          # 📁 Tests
│   ├── __init__.py
│   ├── conftest.py                # Shared fixtures
│   ├── unit/                      # Unit tests
│   │   ├── core/
│   │   └── plugins/
│   ├── integration/               # Integration tests
│   └── e2e/                       # End-to-end tests
│
├── vendor/                         # 📁 Vendored/Forked third-party projects
│   ├── README.md                  # Explanation of each vendor and fork reason
│   ├── aihawk/                    # Fork from AIHawk — LinkedIn job apply
│   ├── skyvern/                   # Fork from Skyvern — Form filling with vision
│   ├── browser-use/               # Fork from browser-use — Browser automation
│   └── openadapt/                 # Fork from OpenAdapt — Desktop learn-by-demo
│
├── artifacts/                      # 📁 Runtime artifacts (gitignored except examples)
│   ├── .gitkeep
│   ├── skills/
│   ├── policies/
│   ├── ui_refs/
│   └── snapshots/
│
├── data/                           # 📁 User data (gitignored)
│   ├── .gitkeep
│   ├── profiles/                  # User profiles
│   └── resumes/                   # Resume files
│
├── logs/                           # 📁 Log files (gitignored)
│   └── .gitkeep
│
└── scripts/                        # 📁 Utility scripts
    ├── setup_dev.sh               # Development setup
    ├── pull_models.sh             # Pull Ollama models
    └── migrate_db.py              # Database migrations
```

---

## 2) Core Components (`src/aria/core/`)

### 2.1 Brain (`core/brain/`)

```
core/brain/
├── __init__.py
├── brain.py                # Main Brain class
├── planner.py             # Plan generation
├── reasoner.py            # LLM reasoning
├── policy_engine.py       # Policy evaluation
├── state_manager.py       # ExecutionState management
└── prompts/               # Prompt templates
    ├── planning.yaml
    ├── reasoning.yaml
    └── decision.yaml
```

### 2.2 Memory (`core/memory/`)

```
core/memory/
├── __init__.py
├── unified.py             # UnifiedMemory class
├── working.py             # Working memory (Redis)
├── episodic.py            # Episodic memory (DB)
├── semantic.py            # Semantic memory (Vector)
├── consolidator.py        # Memory consolidation
├── transfer.py            # Cross-domain transfer
└── embedder.py            # Text embedding
```

### 2.3 Router (`core/router/`)

```
core/router/
├── __init__.py
├── router.py              # TaskRouter class
├── intent_classifier.py   # Intent classification
└── multi_domain.py        # Multi-domain task handling
```

### 2.4 Events (`core/events/`)

```
core/events/
├── __init__.py
├── bus.py                 # Event bus interface
├── kafka.py               # Kafka implementation
├── memory_bus.py          # In-memory implementation (MVP)
├── schemas.py             # Event schemas
└── handlers/              # Event handlers
    ├── logging_handler.py
    └── learning_handler.py
```

### 2.5 Safety (`core/safety/`)

```
core/safety/
├── __init__.py
├── policy_loader.py       # Load safety policies
├── guardrails.py          # Guardrail checks
├── domain_filter.py       # Domain allowlist/denylist
└── pii_detector.py        # PII detection
```

### 2.6 Schemas (`core/schemas/`)

```
core/schemas/
├── __init__.py
├── base.py                # Base classes
├── uiref.py               # UIRef schema
├── skill.py               # Skill schema
├── policy.py              # Policy schema
├── execution.py           # ExecutionState, CapabilityCall, ExecutionResult
├── events.py              # Event schemas
├── memory.py              # Memory entry schemas
└── user.py                # User/Profile schemas
```

---

## 3) Plugin Structure (`src/aria/plugins/`)

### 3.1 Base Plugin

```
plugins/
├── __init__.py            # PluginRegistry
├── base.py                # DomainPlugin ABC
```

### 3.2 Job Apply Plugin

```
plugins/job_apply/
├── __init__.py
├── plugin.py              # JobApplyPlugin class
├── config.yaml            # Domain config
│
├── capabilities/          # Capability implementations
│   ├── __init__.py
│   ├── web.py            # web.* capabilities
│   ├── profile.py        # profile.* capabilities
│   ├── matching.py       # ml.* capabilities
│   └── agent.py          # agent.* capabilities
│
├── hand/                  # Domain-specific Hand
│   ├── __init__.py
│   ├── executor.py       # Capability executor
│   └── uiref_resolver.py # UIRef resolution
│
├── skills/                # Domain-specific skills
│   └── greenhouse_apply.yaml
│
├── policies/              # Domain-specific policies
│   └── captcha_human.yaml
│
└── ui_refs/               # Domain-specific UI refs
    └── greenhouse/
        └── apply_button.yaml
```

### 3.3 Cursor Plugin

```
plugins/cursor/
├── __init__.py
├── plugin.py              # CursorPlugin class
├── config.yaml
│
├── capabilities/
│   ├── __init__.py
│   ├── editor.py         # cursor.editor.* capabilities
│   ├── terminal.py       # cursor.terminal.* capabilities
│   └── git.py            # cursor.git.* capabilities
│
├── bridge/                # Cursor Agent communication
│   ├── __init__.py
│   ├── mcp_client.py     # MCP protocol client
│   └── workspace.py      # Workspace management
│
└── prompts/
    └── code_review.yaml
```

### 3.4 Desktop Plugin

```
plugins/desktop/
├── __init__.py
├── plugin.py              # DesktopPlugin class
├── config.yaml
│
├── capabilities/
│   ├── __init__.py
│   ├── window.py         # desktop.window.* capabilities
│   ├── input.py          # desktop.input.* capabilities
│   ├── screen.py         # desktop.screen.* capabilities
│   └── apps/             # App-specific capabilities
│       ├── excel.py
│       └── file_explorer.py
│
├── adapters/              # Platform-specific adapters
│   ├── __init__.py
│   ├── windows.py        # Win32 API
│   └── macos.py          # AppleScript (future)
│
└── vision/                # Screen understanding
    ├── __init__.py
    └── screen_parser.py
```

---

## 4) Adapters (`src/aria/adapters/`)

```
adapters/
├── __init__.py
├── base.py                # Adapter interface

├── playwright/
│   ├── __init__.py
│   ├── adapter.py         # PlaywrightAdapter
│   ├── browser_pool.py    # Browser instance management
│   └── utils.py

├── ollama/
│   ├── __init__.py
│   ├── adapter.py         # OllamaAdapter
│   ├── model_manager.py   # Model loading/unloading
│   └── prompts.py

├── pyautogui/
│   ├── __init__.py
│   ├── adapter.py         # PyAutoGUIAdapter
│   └── screen.py

├── kafka/                  # Event Bus adapter
│   ├── __init__.py
│   ├── adapter.py         # KafkaAdapter (producer/consumer)
│   ├── schemas.py         # Event schemas
│   └── topics.py          # Topic definitions

├── redis/
│   ├── __init__.py
│   ├── adapter.py         # RedisAdapter
│   ├── state_store.py     # Session state
│   └── cache.py           # Caching layer

└── vector_db/
    ├── __init__.py
    ├── adapter.py         # VectorDBAdapter interface
    ├── qdrant.py          # Qdrant implementation
    └── sqlite_vss.py      # SQLite-VSS implementation (MVP)
```

---

## 5) API Layer (`src/aria/api/`)

### 5.1 REST API

```
api/rest/
├── __init__.py
├── app.py                 # FastAPI app
├── routes/
│   ├── __init__.py
│   ├── tasks.py          # Task endpoints
│   ├── plugins.py        # Plugin management
│   ├── memory.py         # Memory queries
│   └── health.py         # Health checks
├── middleware/
│   ├── __init__.py
│   ├── auth.py           # Authentication (future)
│   └── logging.py        # Request logging
└── schemas/               # API schemas (Pydantic)
    ├── __init__.py
    ├── requests.py
    └── responses.py
```

### 5.2 CLI

```
api/cli/
├── __init__.py
├── main.py                # CLI entry point (Typer)
├── commands/
│   ├── __init__.py
│   ├── run.py            # aria run "..."
│   ├── plugin.py         # aria plugin list/enable/disable
│   ├── config.py         # aria config show/set
│   └── memory.py         # aria memory search/clear
└── formatters/
    ├── __init__.py
    └── rich.py           # Rich output formatting
```

### 5.3 WebSocket API

```
api/websocket/
├── __init__.py
├── server.py              # WebSocket server for UI
├── handlers.py            # Message handlers
├── streaming.py           # Event streaming from Kafka
└── schemas.py             # WebSocket message schemas
```

---

## 6) UI Layer (`src/aria/ui/`)

User interface for HITL, transparency, and control.

**Full details:** [UI Design](ui-design.md)

```
ui/
├── __init__.py
├── app.py                 # Main Streamlit/Gradio app (MVP)
│
├── components/            # Reusable UI components
│   ├── __init__.py
│   ├── live_view.py       # Live browser screenshot streaming
│   ├── activity_log.py    # Execution log (from Kafka events)
│   ├── hitl_panel.py      # Human intervention panel
│   ├── chat_panel.py      # Chat/command interface
│   ├── step_panel.py      # Current step display
│   └── status_bar.py      # Header status
│
├── pages/                 # UI pages/views
│   ├── __init__.py
│   ├── dashboard.py       # Main dashboard (active session)
│   ├── history.py         # Session history
│   ├── analytics.py       # Analytics dashboard
│   └── settings.py        # Settings page
│
├── websocket/             # WebSocket client for streaming
│   ├── __init__.py
│   ├── client.py          # Connect to backend WebSocket
│   └── handlers.py        # Handle incoming messages
│
├── styles/                # CSS styles
│   ├── main.css
│   └── rtl.css            # Persian RTL support
│
└── locales/               # i18n translations
    ├── en.json
    └── fa.json            # Persian
```

**Technology Stack (MVP):**
- **Frontend:** Streamlit or Gradio (Python-native, fast for prototyping)
- **Real-time:** WebSocket via FastAPI
- **Styling:** Built-in components + custom CSS

**Technology Stack (Production):**
- **Frontend:** React + TypeScript
- **State:** Zustand or Redux
- **Styling:** Tailwind CSS + shadcn/ui

---

## 7) Tests (`tests/`)

```
tests/
├── __init__.py
├── conftest.py            # Shared fixtures
├── factories.py           # Test data factories

├── unit/
│   ├── __init__.py
│   ├── core/
│   │   ├── test_brain.py
│   │   ├── test_memory.py
│   │   ├── test_router.py
│   │   └── test_policy.py
│   └── plugins/
│       ├── test_job_apply.py
│       └── test_cursor.py

├── integration/
│   ├── __init__.py
│   ├── test_brain_hand.py
│   ├── test_memory_persistence.py
│   └── test_ollama_integration.py

├── e2e/
│   ├── __init__.py
│   ├── test_job_apply_flow.py
│   └── test_multi_domain.py

└── fixtures/
    ├── mock_sites/        # Mock websites for testing
    ├── sample_resumes/
    └── golden_traces/
```

---

## 8) Import Conventions

### 8.1 Absolute Imports

Always use absolute imports:

```python
# ✅ Good
from aria.core.brain import Brain
from aria.plugins.job_apply.capabilities import web
from aria.core.schemas.execution import ExecutionState

# ❌ Bad
from ..brain import Brain
from .capabilities import web
```

### 8.2 `__init__.py` Exports

Each folder should export its public API in `__init__.py`:

```python
# aria/core/brain/__init__.py
from aria.core.brain.brain import Brain
from aria.core.brain.planner import Planner
from aria.core.brain.policy_engine import PolicyEngine

__all__ = ["Brain", "Planner", "PolicyEngine"]
```

### 8.3 Type Hints

Always use type hints:

```python
# ✅ Good
async def execute(self, call: CapabilityCall) -> ExecutionResult:
    ...

# ❌ Bad
async def execute(self, call):
    ...
```

---

## 9) Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| **Package/Module** | lowercase_underscore | `job_apply`, `policy_engine.py` |
| **Class** | PascalCase | `JobApplyPlugin`, `ExecutionState` |
| **Function/Method** | lowercase_underscore | `generate_plan`, `load_skills` |
| **Constant** | UPPERCASE_UNDERSCORE | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| **Private** | _leading_underscore | `_internal_method` |
| **Type Alias** | PascalCase | `CapabilityCall`, `UIRefId` |

---

## 10) File Size Guidelines

| File Type | Max Lines | Action if Exceeded |
|-----------|-----------|-------------------|
| Module (`.py`) | ~300 | Split into submodules |
| Class | ~200 | Extract helpers/mixins |
| Function | ~50 | Extract sub-functions |
| Test file | ~500 | Split by feature |

---

## 11) Dependency Injection

Use dependency injection for loose coupling:

```python
# ✅ Good - Injectable dependencies
class Brain:
    def __init__(
        self,
        llm: LLMAdapter,
        memory: UnifiedMemory,
        policy_engine: PolicyEngine,
    ):
        self.llm = llm
        self.memory = memory
        self.policy_engine = policy_engine

# Usage
brain = Brain(
    llm=OllamaAdapter(config),
    memory=UnifiedMemory(config),
    policy_engine=PolicyEngine(config),
)

# ❌ Bad - Hard-coded dependencies
class Brain:
    def __init__(self):
        self.llm = OllamaAdapter()  # Hard-coded
        self.memory = UnifiedMemory()  # Hard-coded
```

---

## 12) Configuration Loading

```python
# aria/utils/config.py
from pathlib import Path
import yaml

class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance
    
    def _load(self):
        # Load layers
        self.data = self._load_yaml("config/default.yaml")
        
        env = os.getenv("ARIA_ENV", "development")
        env_config = self._load_yaml(f"config/{env}.yaml")
        self._merge(self.data, env_config)
        
        # Override with env vars
        self._apply_env_vars()

# Global access
config = Config()
```

---

## 13) Makefile

```makefile
# Makefile
.PHONY: install test lint format run clean

install:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

lint:
	ruff check src/ tests/
	mypy src/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

run:
	python -m aria

run-api:
	uvicorn aria.api.rest.app:app --reload

clean:
	rm -rf .pytest_cache __pycache__ .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
```

---

## 14) Third-Party Dependencies and Vendor Strategy

### 14.1 Two Types of Open Source Usage

| Type | Description | Location |
|------|-------------|----------|
| **Dependency (pip)** | Install from PyPI, no changes | `requirements.txt` or `pyproject.toml` |
| **Vendored/Forked** | Cloned and customized | `vendor/` folder |

### 14.2 Dependency Projects (pip install only)

We **do not clone** these projects — only install them:

```toml
# pyproject.toml
[project]
dependencies = [
    # Orchestration
    "langgraph>=0.2.0",           # Brain orchestration
    
    # Memory
    "mem0ai>=0.1.0",              # Unified memory system
    
    # Browser automation
    "playwright>=1.40.0",
    
    # Desktop automation
    "pyautogui>=0.9.54",
    "pywinauto>=0.6.8",
    
    # MCP Protocol
    "mcp>=1.0.0",                 # Model Context Protocol SDK
    
    # Event streaming
    "aiokafka>=0.9.0",
    "redis>=5.0.0",
    
    # LLM
    "ollama>=0.3.0",
    
    # API
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    
    # UI
    "streamlit>=1.30.0",
]
```

### 14.3 Vendored Projects (Clone and Customize)

We **clone** these projects because they require customization:

```
vendor/
├── README.md                      # Explanation of each vendor
│
├── aihawk/                        # 🔗 Fork from github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk
│   ├── README.md                  # Why we forked (LinkedIn adapter)
│   ├── UPSTREAM_VERSION.md        # Upstream version
│   └── src/                       # Original code with our changes
│       ├── ai_hawk/
│       └── aria_extensions/       # 🆕 Our extensions
│           ├── event_emitter.py   # Kafka event emission
│           └── hitl_hooks.py      # HITL integration
│
├── skyvern/                       # 🔗 Fork from github.com/Skyvern-AI/skyvern
│   ├── README.md                  # Why we forked (vision form filling)
│   ├── UPSTREAM_VERSION.md        # Upstream version
│   └── skyvern/                   # Original code with our changes
│       ├── forge/
│       └── aria_extensions/       # 🆕 Our extensions
│           └── form_filler.py     # Custom form filling for job apply
│
├── browser-use/                   # 🔗 Fork from github.com/browser-use/browser-use
│   ├── README.md                  # Why we forked
│   ├── UPSTREAM_VERSION.md        # Upstream version: v0.5.2
│   └── browser_use/               # Original code with our changes
│       ├── agent/
│       ├── browser/
│       └── aria_extensions/       # 🆕 Our extensions
│           ├── hitl_hooks.py      # HITL integration
│           └── event_emitter.py   # Kafka event emission
│
└── openadapt/                     # 🔗 Fork from github.com/OpenAdaptAI/OpenAdapt
    ├── README.md                  # Why we forked
    ├── UPSTREAM_VERSION.md        # Upstream version: v0.8.0
    └── openadapt/                 # Original code with our changes
        ├── capture/
        ├── replay/
        └── aria_extensions/       # 🆕 Our extensions
            └── skill_extractor.py # Convert recording to Skill
```

### 14.4 Why Vendor (not pip)?

| Project | Reason for Vendoring | Stars |
|---------|---------------------|-------|
| **AIHawk** ⭐ | LinkedIn job apply logic, job matching, needs HITL/Kafka | 29k |
| **Skyvern** ⭐ | Vision-based form filling, needs custom form filler | 20k |
| **browser-use** | Needs HITL hooks, Kafka event emission, custom retry logic | 77k |
| **OpenAdapt** | Needs Skill extraction, integration with Learning Engine | 1.5k |

### 14.5 Vendor Workflow

```bash
# 1. Clone to vendor/
git clone https://github.com/browser-use/browser-use vendor/browser-use
cd vendor/browser-use
git checkout v0.5.2  # Pin to specific version

# 2. Record version
echo "v0.5.2" > UPSTREAM_VERSION.md

# 3. Add our extensions
mkdir -p browser_use/aria_extensions
touch browser_use/aria_extensions/__init__.py

# 4. Import in ARIA code
# src/aria/plugins/job_apply/browser.py
from vendor.browser_use.browser_use import Agent
from vendor.browser_use.browser_use.aria_extensions import hitl_hooks
```

### 14.6 Sync with Upstream

```bash
# vendor/browser-use/sync_upstream.sh
#!/bin/bash
# Sync with upstream while preserving our changes

UPSTREAM_VERSION=$(cat UPSTREAM_VERSION.md)
NEW_VERSION=$1

# 1. Fetch upstream
git fetch upstream
git checkout upstream/main

# 2. Check diff
git diff $UPSTREAM_VERSION $NEW_VERSION -- browser_use/

# 3. Merge (manual review required)
git checkout main
git merge upstream/main --no-commit

# 4. Resolve conflicts in aria_extensions/
# 5. Update UPSTREAM_VERSION.md
echo $NEW_VERSION > UPSTREAM_VERSION.md
```

### 14.7 pyproject.toml with Vendor

```toml
# pyproject.toml
[tool.setuptools.packages.find]
where = ["src", "vendor"]  # Include vendor in package discovery

[project.optional-dependencies]
vendor = [
    # vendor/browser-use dependencies
    "playwright>=1.40.0",
    "langchain>=0.1.0",
    
    # vendor/openadapt dependencies  
    "pynput>=1.7.6",
    "pillow>=10.0.0",
]
```

### 14.8 .gitignore for Vendor

```gitignore
# We commit vendor/ (because it's customized)
# But not caches and __pycache__

vendor/**/__pycache__/
vendor/**/*.pyc
vendor/**/.git/         # Remove nested .git
```

---

## 15) Related Documents

- **Code Standards:** [code-standards.md](code-standards.md) — code quality
- **Extensibility:** [extensibility-architecture.md](extensibility-architecture.md) — plugin structure
- **References & Tools:** [references-and-tools.md](references-and-tools.md) — Clone vs Idea decision
- **Deployment:** [deployment-guide.md](deployment-guide.md) — production setup

---

**Summary:**

> **core/** for domain-agnostic, **plugins/** for domain-specific, **adapters/** for external tools, **vendor/** for forked projects (browser-use, OpenAdapt). Regular dependencies from pip; projects requiring customization in vendor/. Each folder has one responsibility. Dependency injection for loose coupling.
