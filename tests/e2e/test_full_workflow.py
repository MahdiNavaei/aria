import pytest

import aria.core.brain.nodes.executor as executor_module
import aria.core.brain.nodes.observer as observer_module
import aria.core.brain.nodes.planner as planner_module
from aria.core.brain.graph import Brain
from aria.core.brain.state import TaskStatus
from aria.core.eye import Observation
from aria.core.hand import CapabilityResult
from aria.core.llm.base import LLMResponse, ModelRole


class FakeLLM:
    async def generate(self, messages, role=ModelRole.BRAIN, **kwargs):
        _ = messages
        _ = role
        _ = kwargs
        return LLMResponse(
            content=(
                '{"steps": ['
                '{"step_id": "step_1", "action": "Open", '
                '"capability": "web.navigate", '
                '"parameters": {"url": "https://example.com"}}'
                ']}'
            ),
            model="fake",
            tokens_used=10,
            finish_reason="stop",
        )


class FakeMemoryManager:
    def __init__(self, session_id: str, user_id: str, **kwargs) -> None:
        _ = session_id
        _ = user_id
        _ = kwargs

    async def build_context(self, goal: str, domain: str, max_tokens: int = 4000):
        _ = goal
        _ = domain
        _ = max_tokens
        return {"episodic": [], "skills": [], "policies": []}


class FakeHand:
    async def execute(self, capability: str, parameters: dict, context: dict):
        _ = capability
        _ = parameters
        _ = context
        return CapabilityResult(success=True, data={"ok": True})


class FakeEye:
    async def observe(self, domain: str, context: dict):
        _ = domain
        _ = context
        return Observation(observation_id="obs-1", source="browser", screenshot_ref="shot")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_end_to_end_brain_flow(
    monkeypatch: pytest.MonkeyPatch,
    docker_services,
) -> None:
    monkeypatch.setattr(planner_module, "get_llm_client", lambda: FakeLLM())
    monkeypatch.setattr(planner_module, "MemoryManager", FakeMemoryManager)

    async def fake_get_hand():
        return FakeHand()

    async def fake_get_eye():
        return FakeEye()

    monkeypatch.setattr(executor_module, "get_hand", fake_get_hand)
    monkeypatch.setattr(observer_module, "get_eye", fake_get_eye)

    brain = Brain()
    final_state = await brain.run(
        goal="Apply to job",
        domain="job_apply",
        session_id="e2e-sess",
        user_id="e2e-user",
    )

    assert final_state["task_status"] == TaskStatus.COMPLETED
