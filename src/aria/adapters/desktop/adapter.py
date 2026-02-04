"""Desktop automation adapter using pyautogui and pywinauto."""

from __future__ import annotations

import time
from typing import Any

import pyautogui

from aria.config import get_settings
from aria.core.hand.capability import (
    Capability,
    CapabilityAdapter,
    CapabilityCategory,
    CapabilityResult,
    ExecutionContext,
)
from aria.models.events import EventType
from aria.utils.events import EventEmitter
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class DesktopAdapter(CapabilityAdapter):
    """Desktop automation adapter."""

    def __init__(self) -> None:
        """Initialize desktop adapter."""
        self._current_app = None

    @property
    def category(self) -> CapabilityCategory:
        """Return capability category."""
        return CapabilityCategory.DESKTOP

    @property
    def capabilities(self) -> list[Capability]:
        """Return list of supported capabilities."""
        return [
            Capability.DESKTOP_CLICK,
            Capability.DESKTOP_TYPE,
            Capability.DESKTOP_HOTKEY,
            Capability.DESKTOP_SCREENSHOT,
            Capability.DESKTOP_FIND_WINDOW,
            Capability.DESKTOP_FOCUS_WINDOW,
        ]

    async def initialize(self) -> None:
        """Initialize desktop adapter."""
        settings = get_settings().hand.desktop
        pyautogui.FAILSAFE = settings.fail_safe
        pyautogui.PAUSE = settings.pause
        logger.info("Desktop adapter initialized", fail_safe=settings.fail_safe)

    async def cleanup(self) -> None:
        """Cleanup desktop adapter (no-op)."""
        return

    async def execute(
        self,
        capability: Capability,
        parameters: dict[str, Any],
        context: ExecutionContext,
    ) -> CapabilityResult:
        """Execute desktop capability."""
        start_time = time.time()
        await self._emit_event(
            EventType.HAND_EXECUTION_STARTED,
            capability,
            {"parameters": parameters},
            context,
        )

        try:
            result = await self._execute_capability(capability, parameters)
            result.duration_ms = int((time.time() - start_time) * 1000)
            await self._emit_event(
                EventType.HAND_EXECUTION_COMPLETED,
                capability,
                {"success": result.success, "duration_ms": result.duration_ms},
                context,
            )
            return result
        except Exception as exc:
            logger.exception("Desktop execution failed", capability=capability.value)
            duration_ms = int((time.time() - start_time) * 1000)
            await self._emit_event(
                EventType.HAND_EXECUTION_FAILED,
                capability,
                {"error": str(exc), "duration_ms": duration_ms},
                context,
            )
            return CapabilityResult.fail(str(exc), duration_ms=duration_ms)
        else:
            return result

    async def _execute_capability(  # noqa: PLR0911
        self,
        capability: Capability,
        parameters: dict[str, Any],
    ) -> CapabilityResult:
        if capability == Capability.DESKTOP_CLICK:
            return await self._click(parameters)
        if capability == Capability.DESKTOP_TYPE:
            return await self._type(parameters)
        if capability == Capability.DESKTOP_HOTKEY:
            return await self._hotkey(parameters)
        if capability == Capability.DESKTOP_SCREENSHOT:
            return await self._screenshot(parameters)
        if capability == Capability.DESKTOP_FIND_WINDOW:
            return await self._find_window(parameters)
        if capability == Capability.DESKTOP_FOCUS_WINDOW:
            return await self._focus_window(parameters)
        return CapabilityResult.fail(f"Unknown capability: {capability}")

    async def _click(self, params: dict[str, Any]) -> CapabilityResult:
        x = params.get("x")
        y = params.get("y")
        button = params.get("button", "left")
        clicks = params.get("clicks", 1)
        if x is None or y is None:
            return CapabilityResult.fail("x and y coordinates required")
        pyautogui.click(x, y, clicks=clicks, button=button)
        return CapabilityResult.ok({"clicked_at": (x, y)})

    async def _type(self, params: dict[str, Any]) -> CapabilityResult:
        text = params.get("text", "")
        interval = params.get("interval", 0.05)
        pyautogui.typewrite(text, interval=interval)
        return CapabilityResult.ok({"typed": text[:50]})

    async def _hotkey(self, params: dict[str, Any]) -> CapabilityResult:
        keys = params.get("keys", [])
        if not keys:
            return CapabilityResult.fail("keys list required")
        pyautogui.hotkey(*keys)
        return CapabilityResult.ok({"pressed": "+".join(keys)})

    async def _screenshot(self, params: dict[str, Any]) -> CapabilityResult:
        from aria.core.eye import get_eye  # noqa: PLC0415

        region = params.get("region")
        eye = await get_eye()
        screenshot = await eye.screenshot_service.capture_desktop(region=region)
        return CapabilityResult.ok(
            {"screenshot_ref": screenshot.ref},
            screenshot_ref=screenshot.ref,
        )

    async def _find_window(self, params: dict[str, Any]) -> CapabilityResult:
        title = params.get("title")
        if not title:
            return CapabilityResult.fail("title required")
        try:
            windows = pyautogui.getWindowsWithTitle(title)
            if windows:
                win = windows[0]
                return CapabilityResult.ok(
                    {
                        "found": True,
                        "title": win.title,
                        "position": (win.left, win.top),
                        "size": (win.width, win.height),
                    },
                )
            return CapabilityResult.ok({"found": False})
        except Exception as exc:  # noqa: BLE001
            return CapabilityResult.fail(str(exc))

    async def _focus_window(self, params: dict[str, Any]) -> CapabilityResult:
        title = params.get("title")
        if not title:
            return CapabilityResult.fail("title required")
        try:
            windows = pyautogui.getWindowsWithTitle(title)
            if windows:
                windows[0].activate()
                return CapabilityResult.ok({"focused": title})
            return CapabilityResult.fail(f"Window not found: {title}")
        except Exception as exc:  # noqa: BLE001
            return CapabilityResult.fail(str(exc))

    async def _emit_event(
        self,
        event_type: EventType,
        capability: Capability,
        payload: dict[str, Any],
        context: ExecutionContext,
    ) -> None:
        try:
            await EventEmitter.emit(
                event_type,
                {
                    "capability": capability.value,
                    "payload": payload,
                    "step_id": context.step_id,
                },
            )
        except RuntimeError as exc:
            logger.debug("Event context not initialized", error=str(exc))
