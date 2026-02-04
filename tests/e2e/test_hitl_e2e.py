import pytest

import aria.core.brain.nodes.hitl as hitl_module
from aria.core.brain.nodes.hitl import HITLNode
from aria.core.brain.state import HITLRequest, TaskStatus, create_initial_state


class FakeStateStore:
    def __init__(self) -> None:
        self.data = {}

    async def set_session_state(self, key: str, state: dict) -> None:
        self.data[key] = state

    async def get_session_state(self, key: str):
        current = self.data.get(key)
        if current and current.get("status") == "pending":
            return {"status": "responded", "response": {"action": "approve"}}
        return current


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_hitl_flow_returns_execution(
    monkeypatch: pytest.MonkeyPatch,
    docker_services,
) -> None:
    store = FakeStateStore()

    async def fake_get_state_store():
        return store

    monkeypatch.setattr(hitl_module, "get_state_store", fake_get_state_store)

    state = create_initial_state(
        session_id="sess-1",
        user_id="user-1",
        goal="Test",
        domain="job_apply",
    )
    state["task_status"] = TaskStatus.WAITING_HUMAN
    state["hitl_request"] = HITLRequest(
        request_id="req-1",
        reason="captcha",
        context={"url": "https://example.com"},
        options=["approve", "reject"],
    )

    node = HITLNode(poll_interval=0.1)
    update = await node(state)

    assert update["task_status"] == TaskStatus.EXECUTING
    assert update["hitl_request"] is None
