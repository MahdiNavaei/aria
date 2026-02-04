"""Executor node for ARIA Brain."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aria.core.brain.state import AgentState, HITLRequest, StepStatus, TaskStatus
from aria.core.hand import CapabilityResult, get_hand
from aria.models.events import EventType
from aria.utils.events import EventEmitter
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class ExecutorNode:
    """Send plan steps to Hand for execution."""

    async def __call__(self, state: AgentState) -> dict:
        """Execute current step in plan."""
        plan = state["plan"]
        if not plan or not plan.current_step:
            return {"error": "No step to execute"}

        step = plan.current_step
        logger.info("Executing step", step_id=step.step_id, capability=step.capability)

        await self._emit_event(
            EventType.BRAIN_STEP_STARTED,
            {
                "step_id": step.step_id,
                "capability": step.capability,
                "parameters": step.parameters,
            },
        )

        try:
            hand = await get_hand()
            observation = state.get("current_observation") or {}
            result = await hand.execute(
                capability=step.capability,
                parameters=step.parameters,
                context={
                    "session_id": state["session_id"],
                    "user_id": state["user_id"],
                    "domain": state["domain"],
                    "step_id": step.step_id,
                    "has_observation": bool(observation),
                    "elements": observation.get("elements"),
                    "page_source": observation.get("text_content"),
                    "screenshot_ref": observation.get("screenshot_ref"),
                    "page_url": observation.get("page_url"),
                    "expected_url": observation.get("page_url"),
                },
            )
            result = self._coerce_result(result)

            if not result.success and result.data:
                safety_decision = result.data.get("safety_decision")

                if safety_decision == "require_human":
                    hitl_payload = result.data.get("hitl_request") or {}
                    return {
                        "task_status": TaskStatus.WAITING_HUMAN,
                        "hitl_request": HITLRequest(
                            request_id=hitl_payload.get("request_id", str(uuid4())),
                            reason=hitl_payload.get("reason", "safety"),
                            context=hitl_payload.get("context", {}),
                            timeout_seconds=hitl_payload.get("timeout_seconds", 300),
                        ),
                        "last_result": result.data,
                        "last_update": datetime.now(UTC),
                    }

                if safety_decision == "block":
                    step.status = StepStatus.FAILED
                    step.error = result.error
                    return {
                        "plan": plan,
                        "task_status": TaskStatus.FAILED,
                        "error": result.error,
                        "last_update": datetime.now(UTC),
                    }

                if safety_decision == "rate_limited":
                    step.error = result.error
                    return {
                        "plan": plan,
                        "error": result.error,
                        "retry_after": result.data.get("retry_after"),
                        "last_update": datetime.now(UTC),
                    }

            if result.success:
                step.status = StepStatus.COMPLETED
                step.result = result.data

                await self._emit_event(
                    EventType.BRAIN_STEP_COMPLETED,
                    {
                        "step_id": step.step_id,
                        "success": True,
                        "result": result.data,
                    },
                )

                plan.current_step_index += 1

                update = {
                    "plan": plan,
                    "last_action": {
                        "capability": step.capability,
                        "params": step.parameters,
                    },
                    "last_result": result.data,
                    "last_update": datetime.now(UTC),
                }

                if plan.is_complete:
                    update["task_status"] = TaskStatus.COMPLETED

                return update

            step.retries += 1
            if step.retries >= step.max_retries:
                step.status = StepStatus.FAILED
                step.error = result.error

                await self._emit_event(
                    EventType.BRAIN_STEP_COMPLETED,
                    {
                        "step_id": step.step_id,
                        "success": False,
                        "error": result.error,
                    },
                )

                return {
                    "plan": plan,
                    "task_status": TaskStatus.FAILED,
                    "error": f"Step {step.step_id} failed: {result.error}",
                    "last_update": datetime.now(UTC),
                }

            logger.warning(
                "Step failed, will retry",
                step_id=step.step_id,
                retry=step.retries,
                error=result.error,
            )
            return {
                "plan": plan,
                "retry_count": state["retry_count"] + 1,
                "last_update": datetime.now(UTC),
            }

        except Exception as exc:
            logger.exception("Execution error", step_id=step.step_id)
            step.status = StepStatus.FAILED
            step.error = str(exc)
            return {
                "plan": plan,
                "task_status": TaskStatus.FAILED,
                "error": str(exc),
                "last_update": datetime.now(UTC),
            }

    async def _emit_event(self, event_type: EventType, payload: dict) -> None:
        """Emit event with error handling."""
        try:
            await EventEmitter.emit(event_type, payload)
        except RuntimeError as exc:
            logger.debug("Event context not initialized", error=str(exc))

    @staticmethod
    def _coerce_result(result: CapabilityResult | dict) -> CapabilityResult:
        """Coerce result to CapabilityResult."""
        if isinstance(result, CapabilityResult):
            return result
        return CapabilityResult(
            success=bool(result.get("success")),
            data=result.get("data"),
            error=result.get("error"),
        )
