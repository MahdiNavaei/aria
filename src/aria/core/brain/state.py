"""Agent state definitions for ARIA Brain."""

from __future__ import annotations

from collections.abc import Sequence  # noqa: TC003
from datetime import UTC, datetime
from enum import Enum
from typing import Annotated, Any, TypedDict, cast

from langgraph.graph import add_messages
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING_HUMAN = "waiting_human"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Step execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Step(BaseModel):
    """Single step in an execution plan."""

    step_id: str
    action: str
    capability: str
    parameters: dict[str, Any]
    status: StepStatus = StepStatus.PENDING
    result: dict[str, Any] | None = None
    error: str | None = None
    retries: int = 0
    max_retries: int = 3


class Plan(BaseModel):
    """Execution plan with ordered steps."""

    plan_id: str
    goal: str
    steps: list[Step]
    current_step_index: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def current_step(self) -> Step | None:
        """Get current step in plan."""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    @property
    def is_complete(self) -> bool:
        """Check if all steps are completed or skipped."""
        return all(
            step.status in {StepStatus.COMPLETED, StepStatus.SKIPPED}
            for step in self.steps
        )

    @property
    def has_failed(self) -> bool:
        """Check if any step has failed permanently."""
        return any(
            step.status == StepStatus.FAILED and step.retries >= step.max_retries
            for step in self.steps
        )


class HITLRequest(BaseModel):
    """Request for human intervention."""

    request_id: str
    reason: str
    context: dict[str, Any]
    options: list[str] | None = None
    timeout_seconds: int = 300
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AgentState(TypedDict):
    """Main state for ARIA Brain."""

    session_id: str
    user_id: str
    domain: str

    goal: str
    task_status: TaskStatus

    plan: Plan | None

    current_observation: dict[str, Any] | None
    observations_history: Annotated[Sequence[dict[str, Any]], add_messages]

    memory_context: dict[str, Any] | None

    hitl_request: HITLRequest | None
    hitl_response: dict[str, Any] | None

    last_action: dict[str, Any] | None
    last_result: dict[str, Any] | None

    error: str | None
    retry_count: int

    start_time: datetime
    last_update: datetime


def create_initial_state(
    session_id: str,
    user_id: str,
    goal: str,
    domain: str,
) -> AgentState:
    """Create initial state for a new task."""
    now = datetime.now(UTC)
    return AgentState(
        session_id=session_id,
        user_id=user_id,
        domain=domain,
        goal=goal,
        task_status=TaskStatus.PENDING,
        plan=None,
        current_observation=None,
        observations_history=[],
        memory_context=None,
        hitl_request=None,
        hitl_response=None,
        last_action=None,
        last_result=None,
        error=None,
        retry_count=0,
        start_time=now,
        last_update=now,
    )


def serialize_state(state: AgentState) -> dict[str, Any]:
    """Serialize agent state to a JSON-friendly dict."""
    data: dict[str, Any] = dict(state)
    plan = data.get("plan")
    if isinstance(plan, Plan):
        data["plan"] = plan.model_dump()

    hitl = data.get("hitl_request")
    if isinstance(hitl, HITLRequest):
        data["hitl_request"] = hitl.model_dump()

    for key in ("start_time", "last_update"):
        value = data.get(key)
        if isinstance(value, datetime):
            data[key] = value.isoformat()

    return data


def deserialize_state(data: dict[str, Any]) -> AgentState:
    """Deserialize state dictionary into AgentState."""
    payload = dict(data)
    plan_data = payload.get("plan")
    if isinstance(plan_data, dict):
        payload["plan"] = Plan.model_validate(plan_data)

    hitl_data = payload.get("hitl_request")
    if isinstance(hitl_data, dict):
        payload["hitl_request"] = HITLRequest.model_validate(hitl_data)

    for key in ("start_time", "last_update"):
        value = payload.get(key)
        if isinstance(value, str):
            payload[key] = datetime.fromisoformat(value)

    return cast("AgentState", payload)
