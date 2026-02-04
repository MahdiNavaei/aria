"""Browser automation adapter using Playwright."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from playwright.async_api import Browser, Page, async_playwright

from aria.adapters.browser.form_filler import FormFiller
from aria.config import get_settings
from aria.core.eye import get_eye
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


class BrowserAdapter(CapabilityAdapter):
    """Browser automation adapter using Playwright."""

    def __init__(self) -> None:
        """Initialize browser adapter with Playwright."""
        self._playwright = None
        self._browser: Browser | None = None
        self._page: Page | None = None
        self._eye = None
        self._form_filler: FormFiller | None = None

    @property
    def category(self) -> CapabilityCategory:
        """Return capability category."""
        return CapabilityCategory.WEB

    @property
    def capabilities(self) -> list[Capability]:
        """Return list of supported capabilities."""
        return [
            Capability.WEB_NAVIGATE,
            Capability.WEB_CLICK,
            Capability.WEB_FILL,
            Capability.WEB_SELECT,
            Capability.WEB_EXTRACT,
            Capability.WEB_SCREENSHOT,
            Capability.WEB_SCROLL,
            Capability.WEB_WAIT,
            Capability.WEB_UPLOAD,
        ]

    async def initialize(self) -> None:
        """Start browser and connect Eye."""
        settings = get_settings().hand.browser
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=settings.headless,
            slow_mo=settings.slow_mo,
        )
        self._page = await self._browser.new_page(
            viewport={"width": settings.viewport.width, "height": settings.viewport.height},
        )
        self._page.set_default_timeout(settings.timeout)

        self._eye = await get_eye()
        self._eye.set_browser_page(self._page)
        self._form_filler = FormFiller(self)

        logger.info("Browser adapter initialized", headless=settings.headless)

    async def cleanup(self) -> None:
        """Close browser resources."""
        if self._page:
            await self._page.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser adapter cleaned up")

    async def execute(
        self,
        capability: Capability,
        parameters: dict[str, Any],
        context: ExecutionContext,
    ) -> CapabilityResult:
        """Execute browser capability."""
        start_time = time.time()
        await self._emit_event(
            EventType.HAND_EXECUTION_STARTED,
            capability,
            {"parameters": parameters},
            context,
        )

        try:
            result = await self._execute_capability(capability, parameters, context)
            result.duration_ms = int((time.time() - start_time) * 1000)
            await self._emit_event(
                EventType.HAND_EXECUTION_COMPLETED,
                capability,
                {"success": result.success, "duration_ms": result.duration_ms},
                context,
            )
            return result
        except Exception as exc:
            logger.exception("Browser execution failed", capability=capability.value)
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

    async def _execute_capability(  # noqa: C901, PLR0911
        self,
        capability: Capability,
        parameters: dict[str, Any],
        context: ExecutionContext,  # noqa: ARG002
    ) -> CapabilityResult:
        """Execute a browser capability."""
        if self._page is None:
            return CapabilityResult.fail("Browser page not initialized")

        if capability == Capability.WEB_NAVIGATE:
            return await self._navigate(parameters)
        if capability == Capability.WEB_CLICK:
            return await self._click(parameters)
        if capability == Capability.WEB_FILL:
            return await self._fill(parameters)
        if capability == Capability.WEB_SELECT:
            return await self._select(parameters)
        if capability == Capability.WEB_EXTRACT:
            return await self._extract(parameters)
        if capability == Capability.WEB_SCREENSHOT:
            return await self._screenshot(parameters)
        if capability == Capability.WEB_SCROLL:
            return await self._scroll(parameters)
        if capability == Capability.WEB_WAIT:
            return await self._wait(parameters)
        if capability == Capability.WEB_UPLOAD:
            return await self._upload(parameters)

        return CapabilityResult.fail(f"Unknown capability: {capability}")

    async def _navigate(self, params: dict[str, Any]) -> CapabilityResult:
        url = params.get("url")
        if not url:
            return CapabilityResult.fail("URL required")

        await self._page.goto(url, wait_until="domcontentloaded")
        return CapabilityResult.ok(
            {"url": self._page.url, "title": await self._page.title()},
        )

    async def _click(self, params: dict[str, Any]) -> CapabilityResult:
        selector = params.get("selector")
        text = params.get("text")
        timeout = params.get("timeout", 5000)

        if selector:
            await self._page.click(selector, timeout=timeout)
            return CapabilityResult.ok({"clicked": selector})
        if text:
            await self._page.get_by_text(text).click(timeout=timeout)
            return CapabilityResult.ok({"clicked": text})
        return CapabilityResult.fail("selector or text required")

    async def _fill(self, params: dict[str, Any]) -> CapabilityResult:
        if self._form_filler and isinstance(params.get("form_data"), dict):
            return await self._form_filler.fill_form(params["form_data"], params.get("context"))

        selector = params.get("selector")
        value = params.get("value", "")
        if not selector:
            return CapabilityResult.fail("selector required")
        await self._page.fill(selector, str(value))
        return CapabilityResult.ok({"filled": selector, "value": value})

    async def _select(self, params: dict[str, Any]) -> CapabilityResult:
        selector = params.get("selector")
        value = params.get("value")
        if not selector or value is None:
            return CapabilityResult.fail("selector and value required")
        await self._page.select_option(selector, value)
        return CapabilityResult.ok({"selected": value})

    async def _extract(self, params: dict[str, Any]) -> CapabilityResult:
        selector = params.get("selector")
        if not selector:
            return CapabilityResult.fail("selector required")
        element = await self._page.query_selector(selector)
        if not element:
            return CapabilityResult.fail(f"Element not found: {selector}")
        text = await element.inner_text()
        return CapabilityResult.ok({"text": text})

    async def _screenshot(self, params: dict[str, Any]) -> CapabilityResult:
        if self._eye is None:
            self._eye = await get_eye()
        full_page = params.get("full_page", False)
        screenshot = await self._eye.screenshot_service.capture_browser(full_page=full_page)
        return CapabilityResult.ok(
            {"screenshot_ref": screenshot.ref},
            screenshot_ref=screenshot.ref,
        )

    async def _scroll(self, params: dict[str, Any]) -> CapabilityResult:
        direction = params.get("direction", "down")
        amount = params.get("amount", 300)
        if direction == "down":
            await self._page.evaluate("window.scrollBy(0, arguments[0])", amount)
        elif direction == "up":
            await self._page.evaluate("window.scrollBy(0, -arguments[0])", amount)
        return CapabilityResult.ok({"scrolled": direction, "amount": amount})

    async def _wait(self, params: dict[str, Any]) -> CapabilityResult:
        selector = params.get("selector")
        timeout = params.get("timeout", 5000)
        if selector:
            await self._page.wait_for_selector(selector, timeout=timeout)
            return CapabilityResult.ok({"waited_for": selector})
        await asyncio.sleep(timeout / 1000)
        return CapabilityResult.ok({"waited_ms": timeout})

    async def _upload(self, params: dict[str, Any]) -> CapabilityResult:
        selector = params.get("selector")
        file_path = params.get("file_path")
        if not selector or not file_path:
            return CapabilityResult.fail("selector and file_path required")
        await self._page.set_input_files(selector, file_path)
        return CapabilityResult.ok({"uploaded": file_path})

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

    @property
    def page(self) -> Page | None:
        """Return current Playwright page."""
        return self._page
