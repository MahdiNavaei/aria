import pytest

import aria.core.brain.nodes.executor as executor_module
from aria.core.brain.nodes.executor import ExecutorNode
from aria.core.brain.state import Plan, Step, TaskStatus
from aria.core.hand import CapabilityResult


class FakeHand:
    def __init__(self, result: CapabilityResult) -> None:
        self._result = result

    async def execute(self, capability: str, parameters: dict, context: dict):
        _ = capability
        _ = parameters
        _ = context
        return self._result


@pytest.mark.asyncio
async def test_executor_success(monkeypatch: pytest.MonkeyPatch) -> None:
    result = CapabilityResult(success=True, data={"ok": True})
    async def fake_get_hand():
        return FakeHand(result)

    monkeypatch.setattr(executor_module, "get_hand", fake_get_hand)

    plan = Plan(
        plan_id="plan-1",
        goal="goal",
        steps=[
            Step(
                step_id="step-1",
                action="do",
                capability="web.navigate",
                parameters={"url": "https://example.com"},
            ),
        ],
    )

    state = {
        "session_id": "sess-1",
        "user_id": "user-1",
        "domain": "job_apply",
        "goal": "goal",
        "task_status": TaskStatus.EXECUTING,
        "plan": plan,
        "current_observation": None,
        "observations_history": [],
        "memory_context": None,
        "hitl_request": None,
        "hitl_response": None,
        "last_action": None,
        "last_result": None,
        "error": None,
        "retry_count": 0,
        "start_time": plan.created_at,
        "last_update": plan.created_at,
    }

    update = await ExecutorNode()(state)

    assert update["task_status"] == TaskStatus.COMPLETED
    assert update["last_result"] == {"ok": True}


@pytest.mark.asyncio
async def test_executor_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    result = CapabilityResult(success=False, error="boom")
    async def fake_get_hand():
        return FakeHand(result)

    monkeypatch.setattr(executor_module, "get_hand", fake_get_hand)

    plan = Plan(
        plan_id="plan-2",
        goal="goal",
        steps=[
            Step(
                step_id="step-1",
                action="do",
                capability="web.navigate",
                parameters={"url": "https://example.com"},
                max_retries=1,
            ),
        ],
    )

    state = {
        "session_id": "sess-2",
        "user_id": "user-2",
        "domain": "job_apply",
        "goal": "goal",
        "task_status": TaskStatus.EXECUTING,
        "plan": plan,
        "current_observation": None,
        "observations_history": [],
        "memory_context": None,
        "hitl_request": None,
        "hitl_response": None,
        "last_action": None,
        "last_result": None,
        "error": None,
        "retry_count": 0,
        "start_time": plan.created_at,
        "last_update": plan.created_at,
    }

    update = await ExecutorNode()(state)

    assert update["task_status"] == TaskStatus.FAILED
    assert "failed" in update["error"]
