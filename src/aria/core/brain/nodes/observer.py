"""Observer node for ARIA Brain."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from aria.core.brain.state import AgentState, HITLRequest, TaskStatus
from aria.core.eye import Observation, get_eye
from aria.models.events import EventType
from aria.utils.events import EventEmitter
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class ObserverNode:
    """Collect observations from Eye and update state."""

    async def __call__(self, state: AgentState) -> dict:
        """Collect observation from Eye and update state."""
        logger.debug("Getting observation", session_id=state["session_id"])

        try:
            eye = await get_eye()
            observation = await eye.observe(
                domain=state["domain"],
                context={
                    "goal": state["goal"],
                    "current_step": state["plan"].current_step if state["plan"] else None,
                },
            )

            await self._emit_event(
                EventType.EYE_PERCEPTION_COMPLETED,
                {
                    "page_type": observation.page_type,
                    "source": observation.source,
                    "elements_found": len(observation.elements),
                    "screenshot_ref": observation.screenshot_ref,
                },
            )

            observation_dict = {
                "source": observation.source,
                "page_type": observation.page_type,
                "state": observation.state.value,
                "timestamp": datetime.now(UTC).isoformat(),
                "screenshot_ref": observation.screenshot_ref,
                "page_title": observation.page_title,
                "page_url": observation.page_url,
                "elements": [element.model_dump() for element in observation.elements],
                "blockers": [blocker.model_dump() for blocker in observation.blockers],
                "has_captcha": observation.has_captcha,
                "requires_login": observation.requires_login,
                "text_content": (
                    observation.text_content[:1000] if observation.text_content else None
                ),
            }

            hitl_request = self._check_hitl_needed(observation)
            task_status = (
                TaskStatus.WAITING_HUMAN if hitl_request else state["task_status"]
            )

            observation_message = {
                "role": "system",
                "content": json.dumps(observation_dict),
            }

            return {
                "current_observation": observation_dict,
                "observations_history": [observation_message],
                "hitl_request": hitl_request,
                "task_status": task_status,
                "last_update": datetime.now(UTC),
            }

        except Exception as exc:
            logger.exception("Observation failed")
            return {
                "error": f"Observation failed: {exc}",
                "last_update": datetime.now(UTC),
            }

    def _check_hitl_needed(self, observation: Observation) -> HITLRequest | None:
        """Check if HITL is needed based on observation."""
        if observation.has_captcha:
            return HITLRequest(
                request_id=str(uuid4()),
                reason="captcha",
                context={
                    "screenshot_ref": observation.screenshot_ref,
                    "page_url": observation.page_url,
                },
            )

        if observation.requires_login:
            return HITLRequest(
                request_id=str(uuid4()),
                reason="login",
                context={
                    "screenshot_ref": observation.screenshot_ref,
                    "page_url": observation.page_url,
                    "login_form": observation.login_form_ref,
                },
            )

        return None

    async def _emit_event(self, event_type: EventType, payload: dict) -> None:
        """Emit event with error handling."""
        try:
            await EventEmitter.emit(event_type, payload)
        except RuntimeError as exc:
            logger.debug("Event context not initialized", error=str(exc))
