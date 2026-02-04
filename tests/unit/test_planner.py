import pytest

import aria.core.brain.nodes.planner as planner_module
from aria.core.brain.nodes.planner import PlannerNode
from aria.core.brain.state import TaskStatus, create_initial_state
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


@pytest.mark.asyncio
async def test_planner_creates_plan(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(planner_module, "get_llm_client", lambda: FakeLLM())
    monkeypatch.setattr(planner_module, "MemoryManager", FakeMemoryManager)

    planner = PlannerNode()
    state = create_initial_state(
        session_id="sess-1",
        user_id="user-1",
        goal="Apply to job",
        domain="job_apply",
    )

    update = await planner(state)

    assert update["task_status"] == TaskStatus.EXECUTING
    assert update["plan"].steps[0].capability == "web.navigate"
