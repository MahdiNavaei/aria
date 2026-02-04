"""HITL hooks for browser-use integration."""

from __future__ import annotations

from typing import Any

from aria.utils.logging import get_logger

logger = get_logger(__name__)


class HITLHooks:
    """Hook points for human-in-the-loop workflows."""

    async def on_pause(self, reason: str, context: dict[str, Any] | None = None) -> None:
        """Called when automation pauses for human input."""
        logger.info("HITL pause requested", reason=reason, context=context or {})

    async def on_resume(self, context: dict[str, Any] | None = None) -> None:
        """Called when automation resumes after human input."""
        logger.info("HITL resume", context=context or {})
