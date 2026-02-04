"""Event emission hooks for browser-use."""

from __future__ import annotations

from typing import Any

from aria.models.events import EventType
from aria.utils.events import EventEmitter
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class BrowserEventEmitter:
    """Emit hand-related events for browser-use actions."""

    async def emit(self, status: str, payload: dict[str, Any]) -> None:
        """Emit a hand.execution event with status metadata."""
        try:
            await EventEmitter.emit(
                EventType.HAND_EXECUTION,
                {"status": status, **payload},
            )
        except RuntimeError as exc:
            logger.debug("Event context not initialized", error=str(exc))
