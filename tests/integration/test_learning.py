import asyncio
import json
from typing import Any

import pytest

from aria.config import get_settings
from aria.config.learning import LearningConfig, SkillExtractionConfig
from aria.core.eye.uiref import Locator, LocatorType, UIRef
from aria.core.learning import setup_learning
from aria.core.learning.policy_learner import PolicyLearner
from aria.core.learning.skill_extractor import SkillExtractor
from aria.core.learning.uiref_refiner import UIRefRefiner
from aria.core.llm import LLMResponse, ModelRole
from aria.models.events import EventEnvelope, EventType


class FakeEventBus:
    def __init__(self) -> None:
        self.subscribe_called = asyncio.Event()

    async def subscribe(self, topics, handler, group_id=None):
        self.subscribe_called.set()
        await asyncio.Event().wait()


class FakeLLM:
    async def generate(
        self,
        messages,
        role: ModelRole = ModelRole.BRAIN,
        temperature: float = 0.3,
        max_tokens: int = 1200,
        **kwargs: Any,
    ) -> LLMResponse:
        payload = {
            "skill_id": "web.apply",
            "name": "Apply for job",
            "description": "Automate job application flow.",
            "domain": "job_apply",
            "trigger": "When user wants to apply",
            "steps": [
                {
                    "capability": "web.navigate",
                    "parameters_template": {"url": "${url}"},
                },
            ],
            "parameters": ["url"],
        }
        return LLMResponse(content=json.dumps(payload), model="fake", tokens_used=10)


class FakeSemanticMemory:
    def __init__(self) -> None:
        self.skills: dict[str, dict[str, Any]] = {}
        self.policies: dict[str, dict[str, Any]] = {}
        self.uirefs: dict[str, dict[str, Any]] = {}

    async def add_skill(self, skill_id: str, skill_def: dict[str, Any], description: str) -> None:
        self.skills[skill_id] = skill_def

    async def add_policy(
        self,
        policy_id: str,
        policy_def: dict[str, Any],
        description: str,
    ) -> None:
        self.policies[policy_id] = policy_def

    async def find_policies(self, context: str, limit: int = 3):
        policies = list(self.policies.values())
        return [{"definition": p} for p in policies[:limit]]

    async def add_uiref(self, uiref_id: str, uiref_def: dict[str, Any], description: str) -> None:
        self.uirefs[uiref_id] = uiref_def

    async def get_uiref(self, uiref_id: str):
        return self.uirefs.get(uiref_id)


@pytest.mark.asyncio
async def test_learning_engine_start_stop(monkeypatch: pytest.MonkeyPatch) -> None:
    if not get_settings().learning.enabled:
        pytest.skip("Learning is disabled in configuration")
    import aria.core.learning.engine as engine_module  # noqa: PLC0415

    engine_module._learning_engine = None
    fake_bus = FakeEventBus()

    async def fake_get_event_bus():
        return fake_bus

    monkeypatch.setattr(engine_module, "get_event_bus", fake_get_event_bus)

    engine = await setup_learning()
    assert engine._running

    await asyncio.wait_for(fake_bus.subscribe_called.wait(), timeout=1.0)
    await engine.stop()

    engine_module._learning_engine = None


@pytest.mark.asyncio
async def test_skill_extraction_from_trace() -> None:
    fake_memory = FakeSemanticMemory()
    settings = LearningConfig(skill_extraction=SkillExtractionConfig(min_steps=2))
    extractor = SkillExtractor(
        semantic_memory=fake_memory,
        llm_client=FakeLLM(),
        settings=settings,
    )

    session_id = "sess-1"
    trace_id = "trace-1"

    events = [
        EventEnvelope(
            event_type=EventType.BRAIN_PLAN_CREATED,
            session_id=session_id,
            trace_id=trace_id,
            payload={"goal": "Apply", "step_count": 2},
        ),
        EventEnvelope(
            event_type=EventType.HAND_EXECUTION_STARTED,
            session_id=session_id,
            trace_id=trace_id,
            payload={
                "capability": "web.navigate",
                "payload": {"parameters": {"url": "https://example.com"}},
                "step_id": "step_1",
            },
        ),
        EventEnvelope(
            event_type=EventType.HAND_EXECUTION_COMPLETED,
            session_id=session_id,
            trace_id=trace_id,
            payload={
                "capability": "web.navigate",
                "payload": {"success": True},
                "step_id": "step_1",
            },
        ),
        EventEnvelope(
            event_type=EventType.BRAIN_STEP_COMPLETED,
            session_id=session_id,
            trace_id=trace_id,
            payload={"step_id": "step_1", "success": True},
        ),
        EventEnvelope(
            event_type=EventType.HAND_EXECUTION_STARTED,
            session_id=session_id,
            trace_id=trace_id,
            payload={
                "capability": "web.click",
                "payload": {"parameters": {"selector": "#apply"}},
                "step_id": "step_2",
            },
        ),
        EventEnvelope(
            event_type=EventType.HAND_EXECUTION_COMPLETED,
            session_id=session_id,
            trace_id=trace_id,
            payload={
                "capability": "web.click",
                "payload": {"success": True},
                "step_id": "step_2",
            },
        ),
        EventEnvelope(
            event_type=EventType.BRAIN_STEP_COMPLETED,
            session_id=session_id,
            trace_id=trace_id,
            payload={"step_id": "step_2", "success": True},
        ),
    ]

    for event in events:
        await extractor.on_execution_event(event)

    assert "web.apply" in fake_memory.skills


@pytest.mark.asyncio
async def test_policy_learning_from_correction() -> None:
    fake_memory = FakeSemanticMemory()
    learner = PolicyLearner(semantic_memory=fake_memory)

    event = EventEnvelope(
        event_type=EventType.HUMAN_CORRECTION_RECEIVED,
        session_id="sess-2",
        trace_id="trace-2",
        payload={
            "type": "correction",
            "original_action": {"type": "web.click"},
            "corrected_action": {"type": "web.fill"},
            "context": {"domain": "job_apply", "page_type": "form"},
        },
    )

    await learner.on_human_feedback(event)

    assert fake_memory.policies


@pytest.mark.asyncio
async def test_uiref_refiner_updates_locator() -> None:
    fake_memory = FakeSemanticMemory()
    uiref = UIRef(
        uiref_id="job.apply",
        description="Apply button",
        domain="job_apply",
        page_pattern="example",
        locators=[Locator(type=LocatorType.CSS, value="#apply", confidence=0.5)],
    )
    fake_memory.uirefs[uiref.uiref_id] = uiref.model_dump()

    refiner = UIRefRefiner(semantic_memory=fake_memory)

    event = EventEnvelope(
        event_type=EventType.HAND_EXECUTION_FAILED,
        session_id="sess-3",
        trace_id="trace-3",
        payload={
            "capability": "web.click",
            "payload": {"success": False},
            "uiref_id": "job.apply",
            "locator_type": "css",
            "element_info": {"id": "apply-btn", "text": "Apply"},
        },
    )

    await refiner.on_execution_result(event)

    updated = fake_memory.uirefs["job.apply"]
    locators = updated["locators"]
    assert len(locators) >= 1
    original = next(loc for loc in locators if loc["value"] == "#apply")
    assert original["confidence"] <= 0.5
