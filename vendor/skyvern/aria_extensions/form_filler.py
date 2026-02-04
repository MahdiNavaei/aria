"""ARIA form filler hooks for skyvern."""

from __future__ import annotations

from typing import Any

from aria.utils.logging import get_logger

logger = get_logger(__name__)


class SkyvernFormFiller:
    """Placeholder bridge for Skyvern form filling."""

    async def fill(self, form_data: dict[str, Any]) -> dict[str, Any]:
        """Return a placeholder response for form filling."""
        logger.info("Skyvern form filler invoked", fields=list(form_data.keys()))
        return {"filled": list(form_data.keys())}
