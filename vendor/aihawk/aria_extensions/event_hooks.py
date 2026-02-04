"""Kafka event emission for AIHawk actions."""

from __future__ import annotations

from typing import Any

from aria.models.events import EventType
from aria.utils.events import EventEmitter
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class AIHawkEventHooks:
    """Hooks to emit events from AIHawk actions."""

    @staticmethod
    async def on_job_found(job_data: dict[str, Any]) -> None:
        """Emit event when a job is found."""
        await _emit_event(
            EventType.HAND_EXECUTION_COMPLETED,
            {
                "action": "job_found",
                "job_id": job_data.get("id"),
                "title": job_data.get("title"),
                "company": job_data.get("company"),
            },
        )

    @staticmethod
    async def on_application_started(job_id: str) -> None:
        """Emit event when application starts."""
        await _emit_event(
            EventType.HAND_EXECUTION_STARTED,
            {"action": "apply", "job_id": job_id},
        )

    @staticmethod
    async def on_application_completed(job_id: str, *, success: bool) -> None:
        """Emit event when application completes."""
        event_type = (
            EventType.HAND_EXECUTION_COMPLETED if success else EventType.HAND_EXECUTION_FAILED
        )
        await _emit_event(
            event_type,
            {"action": "apply", "job_id": job_id, "success": success},
        )


async def _emit_event(event_type: EventType, payload: dict[str, Any]) -> None:
    try:
        await EventEmitter.emit(event_type, payload)
    except RuntimeError as exc:
        logger.debug("Event context not initialized", error=str(exc))
