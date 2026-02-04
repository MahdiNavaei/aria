"""Screenshot capture utilities for Eye."""

from __future__ import annotations

import asyncio
import base64
import io
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import pyautogui
from PIL import Image

from aria.config import get_settings
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class Screenshot:
    """Screenshot data container."""

    def __init__(  # noqa: PLR0913
        self,
        image_bytes: bytes,
        width: int,
        height: int,
        source: Literal["browser", "desktop", "unknown"],
        *,
        timestamp: datetime | None = None,
        metadata: dict[str, Any] | None = None,
        image_format: str = "png",
    ) -> None:
        """Initialize screenshot with image data and metadata."""
        self.image_bytes = image_bytes
        self.width = width
        self.height = height
        self.source = source
        self.timestamp = timestamp or datetime.now(UTC)
        self.metadata = metadata or {}
        self.image_format = image_format
        self._ref: str | None = None

    @property
    def base64(self) -> str:
        """Return base64 encoded image for VLM."""
        return base64.b64encode(self.image_bytes).decode("utf-8")

    @property
    def ref(self) -> str:
        """Return storage reference for this screenshot."""
        if self._ref is None:
            stamp = self.timestamp.strftime("%Y%m%d_%H%M%S_%f")
            self._ref = f"screenshot_{stamp}"
        return self._ref

    def save(self, path: Path) -> Path:
        """Save screenshot to disk and return the filepath."""
        extension = _extension_for_format(self.image_format)
        filepath = path / f"{self.ref}.{extension}"
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_bytes(self.image_bytes)
        return filepath


class ScreenshotService:
    """Service for capturing screenshots from browser and desktop."""

    def __init__(self, storage_dir: Path | None = None) -> None:
        """Initialize screenshot service with storage directory."""
        settings = get_settings().eye.screenshot
        self._settings = settings
        self._format = _normalize_format(settings.format)
        self.storage_dir = Path(storage_dir or settings.dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._browser_page: Any | None = None

    def set_browser_page(self, page: Any) -> None:  # noqa: ANN401
        """Set Playwright page for browser screenshots."""
        self._browser_page = page

    async def capture_browser(self, *, full_page: bool = False) -> Screenshot:
        """Capture a screenshot from Playwright."""
        if self._browser_page is None:
            error_msg = "Browser page not set"
            raise RuntimeError(error_msg)

        options: dict[str, Any] = {"type": self._format, "full_page": full_page}
        if self._format == "jpeg":
            options["quality"] = self._settings.quality

        screenshot_bytes = await self._browser_page.screenshot(**options)

        viewport = getattr(self._browser_page, "viewport_size", None)
        width, height = _resolve_dimensions(screenshot_bytes, viewport)

        metadata = {
            "url": getattr(self._browser_page, "url", None),
            "title": await self._browser_page.title(),
        }

        screenshot = Screenshot(
            image_bytes=screenshot_bytes,
            width=width,
            height=height,
            source="browser",
            metadata=metadata,
            image_format=self._format,
        )

        await self._persist(screenshot)

        logger.debug(
            "Browser screenshot captured",
            ref=screenshot.ref,
            url=metadata.get("url"),
        )

        return screenshot

    async def capture_desktop(self, region: tuple[int, int, int, int] | None = None) -> Screenshot:
        """Capture a screenshot from the desktop."""
        if region:
            pil_image = await asyncio.to_thread(pyautogui.screenshot, region=region)
        else:
            pil_image = await asyncio.to_thread(pyautogui.screenshot)

        buffer = io.BytesIO()
        save_kwargs: dict[str, Any] = {}
        if self._format == "jpeg":
            save_kwargs["quality"] = self._settings.quality
        pil_image.save(buffer, format=_pil_format(self._format), **save_kwargs)
        screenshot_bytes = buffer.getvalue()

        screenshot = Screenshot(
            image_bytes=screenshot_bytes,
            width=pil_image.width,
            height=pil_image.height,
            source="desktop",
            metadata={"region": region},
            image_format=self._format,
        )

        await self._persist(screenshot)

        logger.debug(
            "Desktop screenshot captured",
            ref=screenshot.ref,
            size=(pil_image.width, pil_image.height),
        )

        return screenshot

    async def capture(
        self,
        source: Literal["browser", "desktop"] = "browser",
        **kwargs: Any,  # noqa: ANN401
    ) -> Screenshot:
        """Capture screenshot from the requested source."""
        if source == "browser":
            return await self.capture_browser(**kwargs)
        return await self.capture_desktop(**kwargs)

    def get_screenshot(self, ref: str) -> Screenshot | None:
        """Load screenshot by reference."""
        for extension in ("png", "jpg", "jpeg"):
            filepath = self.storage_dir / f"{ref}.{extension}"
            if filepath.exists():
                image_bytes = filepath.read_bytes()
                width, height = _resolve_dimensions(image_bytes, None)
                return Screenshot(
                    image_bytes=image_bytes,
                    width=width,
                    height=height,
                    source="unknown",
                    image_format=_normalize_format(extension),
                )
        return None

    async def _persist(self, screenshot: Screenshot) -> None:
        await asyncio.to_thread(screenshot.save, self.storage_dir)
        await asyncio.to_thread(self._enforce_storage_limit)

    def _enforce_storage_limit(self) -> None:
        max_mb = self._settings.max_storage_mb
        if max_mb <= 0:
            return

        files = [path for path in self.storage_dir.glob("*") if path.is_file()]
        if not files:
            return

        entries = []
        total_bytes = 0
        for path in files:
            try:
                stat = path.stat()
            except FileNotFoundError:
                continue
            entries.append((path, stat.st_size, stat.st_mtime))
            total_bytes += stat.st_size

        limit_bytes = max_mb * 1024 * 1024
        if total_bytes <= limit_bytes:
            return

        entries.sort(key=lambda item: item[2])
        for path, size, _ in entries:
            if total_bytes <= limit_bytes:
                break
            try:
                path.unlink()
                total_bytes -= size
                logger.debug("Old screenshot removed", path=str(path))
            except OSError as exc:
                logger.warning("Failed to remove screenshot", path=str(path), error=str(exc))


def _normalize_format(image_format: str) -> str:
    fmt = image_format.lower()
    if fmt == "jpg":
        return "jpeg"
    return fmt


def _extension_for_format(image_format: str) -> str:
    fmt = _normalize_format(image_format)
    if fmt == "jpeg":
        return "jpg"
    return fmt


def _pil_format(image_format: str) -> str:
    fmt = _normalize_format(image_format)
    if fmt == "jpeg":
        return "JPEG"
    return fmt.upper()


def _resolve_dimensions(
    image_bytes: bytes,
    viewport: dict[str, int] | None,
) -> tuple[int, int]:
    if viewport and "width" in viewport and "height" in viewport:
        return viewport["width"], viewport["height"]
    with Image.open(io.BytesIO(image_bytes)) as img:
        return img.width, img.height


_screenshot_service: ScreenshotService | None = None


def get_screenshot_service() -> ScreenshotService:
    """Return singleton ScreenshotService instance."""
    global _screenshot_service  # noqa: PLW0603
    if _screenshot_service is None:
        _screenshot_service = ScreenshotService()
    return _screenshot_service
