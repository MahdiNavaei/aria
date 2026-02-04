---
title: "Testing Strategy"
version: v1
date: "2026-02-02"
---

# Testing Strategy

This document defines the testing strategy for the ARIA project: test levels, tools, coverage targets, and best practices.

---

## 1) Test Pyramid

```
                    ┌─────────┐
                    │   E2E   │  ← Fewest, slowest, highest confidence
                    │  Tests  │     5-10 tests
                    ├─────────┤
                    │         │
                    │ Integra-│  ← Medium
                    │  tion   │     50-100 tests
                    │         │
                    ├─────────┤
                    │         │
                    │         │
                    │  Unit   │  ← Most, fastest
                    │  Tests  │     500+ tests
                    │         │
                    └─────────┘
```

| Level | Target Count | Execution Time | Purpose |
|-------|-------------|----------------|---------|
| **Unit** | 500+ | < 2 min | Logic works correctly |
| **Integration** | 50-100 | < 10 min | Components work together |
| **E2E** | 5-10 | < 30 min | Full system works |
| **Regression** | 15-30 golden | < 1 hour | Changes didn't break anything |

---

## 2) Unit Tests

### 2.1 Scope

| Component | What is Tested |
|-----------|----------------|
| **Brain** | Plan generation, Policy evaluation, Skill expansion, State management |
| **Hand** | UIRef resolution, Capability routing, Error handling |
| **Matching** | Score calculation, Hard filters, LLM prompt generation |
| **Schemas** | Validation, Serialization/Deserialization |
| **Utils** | Helpers, Parsers, Formatters |

### 2.2 Example Unit Tests

```python
# tests/unit/test_brain_policy.py
import pytest
from aria.core.brain.policy import PolicyEngine, Policy, PolicyCondition

class TestPolicyEvaluation:
    
    def test_captcha_policy_triggers_on_blocker(self):
        """Policy captcha_requires_human should trigger when blocker=captcha"""
        policy = Policy(
            policy_id="policy_captcha_requires_human",
            conditions=[PolicyCondition(type="blocker_detected", value="captcha")],
            actions=[{"type": "require_human"}]
        )
        engine = PolicyEngine(policies=[policy])
        
        context = {"blockers": ["captcha"]}
        actions = engine.evaluate(context)
        
        assert len(actions) == 1
        assert actions[0]["type"] == "require_human"
    
    def test_no_trigger_without_blocker(self):
        """Without blocker, policy should not trigger"""
        policy = Policy(
            policy_id="policy_captcha_requires_human",
            conditions=[PolicyCondition(type="blocker_detected", value="captcha")],
            actions=[{"type": "require_human"}]
        )
        engine = PolicyEngine(policies=[policy])
        
        context = {"blockers": []}
        actions = engine.evaluate(context)
        
        assert len(actions) == 0


# tests/unit/test_matching_score.py
from aria.plugins.job_apply.matching.scorer import SkillsScorer

class TestSkillsScoring:
    
    def test_exact_match_full_score(self):
        """If all skills match, score should be 100"""
        scorer = SkillsScorer()
        job_skills = ["Python", "Django", "PostgreSQL"]
        candidate_skills = ["Python", "Django", "PostgreSQL", "Redis"]
        
        score, evidence = scorer.calculate(job_skills, candidate_skills)
        
        assert score == 100
        assert len(evidence["missing_skills"]) == 0
    
    def test_partial_match_proportional_score(self):
        """If 2 of 4 skills match, score should be around 50"""
        scorer = SkillsScorer()
        job_skills = ["Python", "Django", "Kubernetes", "GraphQL"]
        candidate_skills = ["Python", "Django"]
        
        score, evidence = scorer.calculate(job_skills, candidate_skills)
        
        assert score == 50
        assert evidence["missing_skills"] == ["Kubernetes", "GraphQL"]
    
    def test_semantic_match_counts(self):
        """FastAPI should have semantic match with Django (web framework)"""
        scorer = SkillsScorer(enable_semantic=True)
        job_skills = ["Django"]
        candidate_skills = ["FastAPI"]
        
        score, evidence = scorer.calculate(job_skills, candidate_skills)
        
        assert score > 50  # Semantic match should give partial credit
        assert "FastAPI" in evidence["semantic_matches"]


# tests/unit/test_uiref_resolution.py
from aria.core.hand.uiref import UIRefResolver, UIRef, Locator

class TestUIRefResolution:
    
    def test_resolves_by_priority(self):
        """Locator with higher confidence should be tried first"""
        ui_ref = UIRef(
            ui_ref_id="test",
            locators=[
                Locator(type="xpath", value="//old", confidence=0.5),
                Locator(type="css", value=".new-button", confidence=0.9),
            ]
        )
        resolver = UIRefResolver()
        
        order = resolver.get_locator_order(ui_ref)
        
        assert order[0].type == "css"
        assert order[1].type == "xpath"
```

### 2.3 Coverage Target

| Component | Target |
|-----------|--------|
| Brain | 90% |
| Hand | 85% |
| Matching | 95% |
| Schemas | 100% |
| Overall | 85% |

---

## 3) Integration Tests

### 3.1 Scope

| Integration | What is Tested |
|-------------|----------------|
| **Brain ↔ Hand** | CapabilityCall/ExecutionResult contract |
| **Hand ↔ Playwright** | Page actually opens and clicks work |
| **Brain ↔ Ollama** | Model responds and is parsed correctly |
| **Event ↔ Kafka** | Events are published/consumed |
| **Artifact ↔ FileSystem** | Files are read/written correctly |

### 3.2 Test Infrastructure

```yaml
# docker-compose.test.yml
services:
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ./models:/root/.ollama/models
    ports:
      - "11434:11434"
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  redpanda:
    image: redpandadata/redpanda:latest
    command: redpanda start --mode dev-container
    ports:
      - "9092:9092"
  
  test-site:
    image: nginx:alpine
    volumes:
      - ./tests/fixtures/mock-sites:/usr/share/nginx/html
    ports:
      - "8080:80"
```

### 3.3 Example Integration Tests

```python
# tests/integration/test_brain_hand_contract.py
import pytest
from aria.core.brain import Brain
from aria.core.hand import Hand

@pytest.fixture
async def brain_hand():
    hand = Hand(adapters=["playwright"])
    brain = Brain(hand=hand)
    yield brain, hand
    await hand.cleanup()

class TestBrainHandContract:
    
    @pytest.mark.asyncio
    async def test_capability_call_returns_execution_result(self, brain_hand):
        """Brain calls, Hand returns result"""
        brain, hand = brain_hand
        
        call = CapabilityCall(
            call_id="test_001",
            capability="web.open_page",
            parameters={"url": "http://localhost:8080/simple.html"}
        )
        
        result = await hand.execute(call)
        
        assert result.call_id == "test_001"
        assert result.success == True
        assert result.observation is not None
    
    @pytest.mark.asyncio
    async def test_failure_returns_recoverable_error(self, brain_hand):
        """When element not found, error should be recoverable"""
        brain, hand = brain_hand
        
        call = CapabilityCall(
            call_id="test_002",
            capability="web.detect_apply_entry",
            parameters={"ui_ref_hint": "nonexistent_button"}
        )
        
        result = await hand.execute(call)
        
        assert result.success == False
        assert result.error.code == "UI_NOT_FOUND"
        assert result.error.recoverable == True


# tests/integration/test_ollama_integration.py
@pytest.mark.asyncio
async def test_brain_generates_plan_with_ollama():
    """Brain should generate plan with Ollama"""
    brain = Brain(model="aria-brain")  # qwen3-7b-instruct
    
    plan = await brain.generate_plan(
        goal="Apply to job at https://example.com/job/123"
    )
    
    assert plan is not None
    assert len(plan.steps) > 0
    assert plan.steps[0].capability.startswith("web.")


# tests/integration/test_event_publishing.py
@pytest.mark.asyncio
async def test_hand_publishes_execution_event(kafka_consumer):
    """Hand should publish event after execute"""
    hand = Hand(event_bus=KafkaEventBus())
    
    await hand.execute(CapabilityCall(...))
    
    # Wait for event
    events = await kafka_consumer.consume("hand.execution.v1", timeout=5)
    
    assert len(events) == 1
    assert events[0]["success"] in [True, False]
```

---

## 4) E2E Tests

### 4.1 Scope

Full workflow testing from start to finish:

| Scenario | Description |
|----------|-------------|
| **Happy Path Apply** | open → extract → match → apply → submit |
| **Vision Fallback** | UI change → vision → success |
| **Human Intervention** | captcha → human → continue |
| **Skip Low Match** | extract → match low → skip |
| **Multi-step Form** | form with multiple pages |

### 4.2 E2E Test Structure

```python
# tests/e2e/test_full_apply_flow.py
import pytest
from aria import ARIAAgent

@pytest.fixture
async def agent():
    agent = ARIAAgent(
        config={
            "brain_model": "aria-brain",  # qwen3-7b-instruct
            "headless": True,
            "test_mode": True
        }
    )
    yield agent
    await agent.shutdown()

class TestFullApplyFlow:
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_happy_path_greenhouse_apply(self, agent):
        """Full apply flow to Greenhouse should work"""
        result = await agent.run(
            goal="Apply to Software Engineer at TestCorp",
            job_url="http://localhost:8080/mock-greenhouse/job/123",
            profile_ref="test_profile_001"
        )
        
        assert result.status == "completed"
        assert result.application_submitted == True
        assert result.metrics.human_interventions == 2  # confirms
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_skip_on_low_match(self, agent):
        """Job with low match should be skipped"""
        result = await agent.run(
            goal="Apply to Unrelated Job",
            job_url="http://localhost:8080/mock-job/unrelated",
            profile_ref="test_profile_001"
        )
        
        assert result.status == "completed"
        assert result.decision == "skip"
        assert result.application_submitted == False
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_recovers_from_ui_change(self, agent, mock_site):
        """When UI changed, vision should help"""
        # Change the apply button selector
        mock_site.modify_page("job/123", selector_change=True)
        
        result = await agent.run(
            goal="Apply despite UI change",
            job_url="http://localhost:8080/mock-job/123"
        )
        
        assert result.status == "completed"
        assert result.metrics.vision_fallbacks >= 1
```

### 4.3 Mock Sites

```
tests/
└── fixtures/
    └── mock-sites/
        ├── greenhouse/
        │   ├── job-list.html
        │   ├── job-detail.html
        │   └── apply-form.html
        ├── lever/
        │   └── ...
        └── custom/
            └── ...
```

---

## 5) Regression Tests

Details in [replay-and-regression.md](replay-and-regression.md).

**Summary:**
- Golden Traces from successful real executions
- Daily run on all goldens
- Diff and metrics tracking
- Auto-alert on regression

---

## 6) Test Tools & Frameworks

| Tool | Usage |
|------|-------|
| **pytest** | Test runner |
| **pytest-asyncio** | Async test support |
| **pytest-cov** | Coverage reporting |
| **pytest-xdist** | Parallel execution |
| **Playwright** | Browser automation for integration/E2E |
| **Faker** | Test data generation |
| **factory_boy** | Test fixtures |
| **responses** | HTTP mocking |
| **freezegun** | Time mocking |

### 6.1 pytest Configuration

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    regression: Regression tests
    slow: Slow tests (> 10s)
addopts = 
    --strict-markers
    -v
    --tb=short

# Coverage
[coverage:run]
source = aria
branch = True
omit = 
    */tests/*
    */__pycache__/*

[coverage:report]
exclude_lines =
    pragma: no cover
    raise NotImplementedError
    if TYPE_CHECKING:
```

### 6.2 Test Commands

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=aria --cov-report=html

# Run integration tests
pytest tests/integration/ -v -m integration

# Run E2E tests
pytest tests/e2e/ -v -m e2e --headed  # with browser visible

# Run regression
pytest tests/regression/ -v -m regression

# Run all except slow
pytest -v -m "not slow"

# Parallel execution
pytest tests/unit/ -n auto
```

---

## 7) CI/CD Integration

### 7.1 Pipeline Stages

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Lint &    │ →  │    Unit     │ →  │ Integration │ →  │    E2E      │
│   Format    │    │   Tests     │    │   Tests     │    │   Tests     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      ↓                  ↓                  ↓                  ↓
   2 min             2 min              10 min             30 min
```

### 7.2 GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install ruff black mypy
      - run: ruff check .
      - run: black --check .
      - run: mypy aria/

  unit:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt -r requirements-test.txt
      - run: pytest tests/unit/ --cov=aria --cov-report=xml
      - uses: codecov/codecov-action@v4

  integration:
    runs-on: ubuntu-latest
    needs: unit
    services:
      redis:
        image: redis:7-alpine
        ports: [6379:6379]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt -r requirements-test.txt
      - run: pytest tests/integration/ -v

  e2e:
    runs-on: ubuntu-latest
    needs: integration
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt -r requirements-test.txt
      - run: npx playwright install chromium
      - run: docker-compose -f docker-compose.test.yml up -d
      - run: pytest tests/e2e/ -v --headed=false
      - run: docker-compose -f docker-compose.test.yml down
```

---

## 8) Test Data Management

### 8.1 Fixtures

```python
# tests/conftest.py
import pytest
from aria.core.schemas import CandidateProfile, UIRef

@pytest.fixture
def sample_profile():
    return CandidateProfile(
        profile_id="test_profile_001",
        name="John Doe",
        email="john@example.com",
        skills=[
            {"name": "Python", "level": "expert", "years": 5},
            {"name": "Django", "level": "advanced", "years": 3},
        ],
        experience={"total_years": 5},
        education={"highest_level": "masters", "field": "Computer Science"}
    )

@pytest.fixture
def sample_ui_ref():
    return UIRef(
        ui_ref_id="uiref_test_button",
        semantic_label="test_button",
        locators=[
            {"type": "css", "value": ".test-btn", "confidence": 0.9},
            {"type": "xpath", "value": "//button[@id='test']", "confidence": 0.8},
        ]
    )

@pytest.fixture
def mock_jd():
    return {
        "title": "Software Engineer",
        "skills": {"required": ["Python", "Django"], "preferred": ["AWS"]},
        "experience_required": {"min_years": 3, "max_years": 7}
    }
```

### 8.2 Factory Pattern

```python
# tests/factories.py
import factory
from aria.core.schemas import CandidateProfile, JobDescription

class CandidateProfileFactory(factory.Factory):
    class Meta:
        model = CandidateProfile
    
    profile_id = factory.Sequence(lambda n: f"profile_{n:04d}")
    name = factory.Faker("name")
    email = factory.Faker("email")
    skills = factory.LazyFunction(lambda: [
        {"name": "Python", "level": "advanced", "years": 3}
    ])

class JobDescriptionFactory(factory.Factory):
    class Meta:
        model = JobDescription
    
    jd_ref = factory.Sequence(lambda n: f"jd_{n:04d}")
    title = factory.Faker("job")
    company = factory.Faker("company")
```

---

## 9) Best Practices

### 9.1 Test Naming

```python
# Good
def test_policy_triggers_when_captcha_detected():
def test_skills_score_is_100_when_all_match():
def test_returns_error_when_element_not_found():

# Bad
def test_policy():
def test_1():
def test_it_works():
```

### 9.2 Arrange-Act-Assert

```python
def test_match_score_calculation():
    # Arrange
    scorer = MatchScorer()
    job = {"skills": ["Python", "Django"]}
    candidate = {"skills": ["Python"]}
    
    # Act
    result = scorer.calculate(job, candidate)
    
    # Assert
    assert result.score == 50
    assert result.missing == ["Django"]
```

### 9.3 Test Isolation

- Each test should be independent
- Avoid shared state
- Use fixtures for setup/teardown

### 9.4 Flaky Test Prevention

```python
# Bad - timing dependent
def test_async_operation():
    start_operation()
    time.sleep(5)
    assert operation_complete()

# Good - poll with timeout
async def test_async_operation():
    start_operation()
    await wait_for(operation_complete, timeout=10)
```

---

## 10) Related Documents

- **Replay & Regression:** [replay-and-regression.md](replay-and-regression.md)
- **Error Taxonomy:** [error-taxonomy.md](error-taxonomy.md) — error codes for testing
- **Contracts & Schemas:** [contracts-and-schemas.md](contracts-and-schemas.md) — schema validation tests

---

**Summary:**

> **Unit** for logic, **Integration** for connections, **E2E** for full flow, **Regression** for stability. Goal: **85%+ coverage**, fast execution in CI, and early problem detection.
