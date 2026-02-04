"""Human-in-the-loop node for ARIA Brain."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from aria.adapters.redis import get_state_store
from aria.core.brain.state import AgentState, TaskStatus
from aria.models.events import EventType
from aria.utils.events import EventEmitter
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class HITLNode:
    """Handle human-in-the-loop requests and responses."""

    def __init__(self, poll_interval: float = 1.0) -> None:
        """Initialize HITL node with polling interval."""
        self.poll_interval = poll_interval

    async def __call__(self, state: AgentState) -> dict:
        """Handle HITL request and wait for response."""
        hitl_request = state.get("hitl_request")
        if not hitl_request:
            return {}

        logger.info(
            "HITL request initiated",
            request_id=hitl_request.request_id,
            reason=hitl_request.reason,
        )

        await self._emit_event(
            EventType.HUMAN_ACTION_RECEIVED,
            {
                "request_id": hitl_request.request_id,
                "reason": hitl_request.reason,
                "context": hitl_request.context,
                "options": hitl_request.options,
            },
        )

        store = await get_state_store()
        await store.set_session_state(
            f"hitl:{state['session_id']}",
            {
                "request": hitl_request.model_dump(),
                "status": "pending",
                "created_at": datetime.now(UTC).isoformat(),
            },
        )

        response = await self._wait_for_response(
            state["session_id"],
            hitl_request.request_id,
            hitl_request.timeout_seconds,
        )

        if response is None:
            logger.warning("HITL request timed out", request_id=hitl_request.request_id)
            return {
                "hitl_request": None,
                "hitl_response": {"status": "timeout"},
                "task_status": TaskStatus.FAILED,
                "error": "Human response timeout",
            }

        logger.info(
            "HITL response received",
            request_id=hitl_request.request_id,
            action=response.get("action"),
        )

        await self._emit_event(
            EventType.HUMAN_FEEDBACK_RECEIVED,
            {"request_id": hitl_request.request_id, "response": response},
        )

        action = response.get("action")
        base_update = {"hitl_request": None, "hitl_response": response}

        action_handlers = {
            "approve": TaskStatus.EXECUTING,
            "correct": TaskStatus.EXECUTING,
            "completed": TaskStatus.EXECUTING,
            "reject": TaskStatus.CANCELLED,
        }

        if action in action_handlers:
            base_update["task_status"] = action_handlers[action]
            if action == "reject":
                base_update["error"] = response.get("reason", "User rejected")
            return base_update

        return base_update

    async def _wait_for_response(
        self,
        session_id: str,
        request_id: str,  # noqa: ARG002
        timeout_seconds: int,
    ) -> dict | None:
        """Wait for human response with timeout using polling."""
        store = await get_state_store()
        key = f"hitl:{session_id}"

        elapsed = 0.0
        while elapsed < timeout_seconds:
            current = await store.get_session_state(key)
            if current and current.get("status") == "responded":
                return current.get("response")

            await asyncio.sleep(self.poll_interval)
            elapsed += self.poll_interval

        return None

    async def _emit_event(self, event_type: EventType, payload: dict) -> None:
        """Emit event with error handling."""
        try:
            await EventEmitter.emit(event_type, payload)
        except RuntimeError as exc:
            logger.debug("Event context not initialized", error=str(exc))


async def submit_hitl_response(session_id: str, response: dict) -> None:
    """Submit human response for a HITL request."""
    store = await get_state_store()
    key = f"hitl:{session_id}"
    current = await store.get_session_state(key)
    if current:
        current["status"] = "responded"
        current["response"] = response
        current["responded_at"] = datetime.now(UTC).isoformat()
        await store.set_session_state(key, current)
