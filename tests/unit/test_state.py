
from aria.core.brain.state import (
    Plan,
    Step,
    StepStatus,
    TaskStatus,
    create_initial_state,
    deserialize_state,
    serialize_state,
)


def test_create_initial_state() -> None:
    state = create_initial_state(
        session_id="sess-1",
        user_id="user-1",
        goal="test goal",
        domain="job_apply",
    )

    assert state["task_status"] == TaskStatus.PENDING
    assert state["plan"] is None
    assert state["current_observation"] is None


def test_plan_properties() -> None:
    plan = Plan(
        plan_id="plan-1",
        goal="goal",
        steps=[
            Step(
                step_id="step-1",
                action="do",
                capability="web.navigate",
                parameters={"url": "https://example.com"},
                status=StepStatus.COMPLETED,
            ),
            Step(
                step_id="step-2",
                action="do2",
                capability="web.click",
                parameters={},
                status=StepStatus.SKIPPED,
            ),
        ],
    )

    assert plan.current_step_index == 0
    assert plan.is_complete is True
    assert plan.has_failed is False


def test_state_serialize_roundtrip() -> None:
    state = create_initial_state(
        session_id="sess-2",
        user_id="user-2",
        goal="goal",
        domain="job_apply",
    )
    state["plan"] = Plan(
        plan_id="plan-2",
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

    payload = serialize_state(state)
    restored = deserialize_state(payload)

    assert restored["plan"] is not None
    assert restored["plan"].plan_id == "plan-2"
