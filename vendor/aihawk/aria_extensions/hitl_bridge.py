"""HITL bridge for AIHawk workflows."""

from __future__ import annotations

from typing import Any

from aria.utils.logging import get_logger

logger = get_logger(__name__)


class AIHawkHITL:
    """Bridge for human-in-the-loop steps."""

    async def request_login(self, reason: str, context: dict[str, Any] | None = None) -> None:
        """Request human login intervention."""
        logger.info("HITL login requested", reason=reason, context=context or {})

    async def request_captcha(self, context: dict[str, Any] | None = None) -> None:
        """Request human captcha solving."""
        logger.info("HITL captcha requested", context=context or {})

    async def resume(self) -> None:
        """Signal workflow to resume after human action."""
        logger.info("HITL resume signaled")
