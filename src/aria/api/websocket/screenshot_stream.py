"""Screenshot streaming for UI clients."""

from __future__ import annotations

import asyncio
import base64
import contextlib
from io import BytesIO
from typing import TYPE_CHECKING

from PIL import Image

from aria.config import get_settings
from aria.core.eye import get_eye
from aria.utils.logging import get_logger

if TYPE_CHECKING:
    from aria.api.websocket.server import ConnectionManager

logger = get_logger(__name__)


def _get_manager() -> ConnectionManager:
    """Get the connection manager (lazy import to avoid circular dependency)."""
    from aria.api.websocket.server import manager  # noqa: PLC0415

    return manager


class ScreenshotStreamer:
    """Stream screenshots to connected WebSocket clients."""

    def __init__(self, *, interval: float = 1.0, quality: int = 50) -> None:
        """Initialize the screenshot streamer.

        Args:
            interval: Capture interval in seconds.
            quality: JPEG quality (0-100).

        """
        self.interval = interval
        self.quality = quality
        self._running = False
        self._task: asyncio.Task[None] | None = None

    async def start(self, session_id: str) -> None:
        """Start streaming for a session."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._stream_loop(session_id))
        logger.info("Screenshot streaming started", session_id=session_id)

    async def stop(self) -> None:
        """Stop streaming."""
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _stream_loop(self, session_id: str) -> None:
        """Run the main streaming loop."""
        eye = await get_eye()
        ui_settings = get_settings().ui.screenshot_streaming
        interval = max(0.2, ui_settings.interval_ms / 1000)

        while self._running:
            try:
                screenshot = await eye.screenshot_service.capture()
                compressed = self._compress_screenshot(
                    screenshot.image_bytes,
                    max_width=ui_settings.max_width,
                )
                manager = _get_manager()
                await manager.send_to_session(
                    session_id,
                    {
                        "type": "screenshot",
                        "session_id": session_id,
                        "data": compressed,
                        "width": screenshot.width,
                        "height": screenshot.height,
                        "timestamp": screenshot.timestamp.isoformat(),
                    },
                )
            except Exception as exc:  # noqa: BLE001
                logger.debug("Screenshot streaming error", error=str(exc))

            await asyncio.sleep(interval)

    def _compress_screenshot(self, image_bytes: bytes, *, max_width: int) -> str:
        """Compress and encode screenshot for streaming."""
        img = Image.open(BytesIO(image_bytes))

        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=self.quality)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")


_streamer: ScreenshotStreamer | None = None


def get_screenshot_streamer() -> ScreenshotStreamer:
    """Return singleton screenshot streamer."""
    global _streamer  # noqa: PLW0603
    if _streamer is None:
        settings = get_settings().ui.screenshot_streaming
        _streamer = ScreenshotStreamer(
            interval=settings.interval_ms / 1000,
            quality=settings.quality,
        )
    return _streamer
