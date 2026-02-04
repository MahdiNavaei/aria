"""Bridge for starting/stopping OpenAdapt recordings."""

from __future__ import annotations

from typing import Any

from aria.models.events import EventType
from aria.utils.events import EventEmitter
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class RecordingBridge:
    """Bridge to OpenAdapt recording functionality."""

    def __init__(self) -> None:
        """Initialize recording bridge."""
        self._recording = False
        self._current_recording: dict[str, Any] | None = None

    async def start_recording(self, name: str) -> None:
        """Start a new recording session."""
        self._recording = True
        self._current_recording = {"name": name, "actions": []}

        await self._emit_event(
            EventType.HUMAN_ACTION_RECEIVED,
            {"type": "recording_started", "name": name},
        )

    async def stop_recording(self) -> dict[str, Any] | None:
        """Stop recording and return recording data."""
        if not self._recording:
            return None

        self._recording = False
        recording = self._current_recording
        self._current_recording = None

        await self._emit_event(
            EventType.HUMAN_ACTION_RECEIVED,
            {
                "type": "recording_stopped",
                "actions": len(recording.get("actions", [])) if recording else 0,
            },
        )

        return recording

    @property
    def is_recording(self) -> bool:
        """Return whether recording is in progress."""
        return self._recording

    async def _emit_event(self, event_type: EventType, payload: dict[str, Any]) -> None:
        """Emit event with error handling."""
        try:
            await EventEmitter.emit(event_type, payload)
        except RuntimeError as exc:
            logger.debug("Event context not initialized", error=str(exc))
