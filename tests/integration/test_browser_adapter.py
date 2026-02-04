import io

import pytest
from PIL import Image

from aria.adapters.browser.adapter import BrowserAdapter
from aria.core.eye.screenshot import Screenshot
from aria.core.hand.capability import Capability, ExecutionContext


class FakePage:
    def __init__(self) -> None:
        self.url = "about:blank"

    async def goto(self, url, wait_until=None):
        _ = wait_until
        self.url = url

    async def title(self):
        return "Example Domain"

    async def click(self, selector, timeout=None):
        _ = selector
        _ = timeout

    def get_by_text(self, text):
        class _Handle:
            async def click(self, timeout=None):
                _ = timeout

        _ = text
        return _Handle()

    async def fill(self, selector, value):
        _ = selector
        _ = value

    async def select_option(self, selector, value):
        _ = selector
        _ = value

    async def query_selector(self, selector):
        _ = selector

        class _Element:
            async def inner_text(self):
                return "hello"

        return _Element()

    async def wait_for_selector(self, selector, timeout=None):
        _ = selector
        _ = timeout

    async def set_input_files(self, selector, file_path):
        _ = selector
        _ = file_path

    async def evaluate(self, script):
        _ = script


class FakeEye:
    def __init__(self) -> None:
        image = Image.new("RGB", (120, 80), color="white")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        self._screenshot = Screenshot(
            image_bytes=buffer.getvalue(),
            width=120,
            height=80,
            source="browser",
            metadata={},
            image_format="png",
        )
        self.screenshot_service = self

    async def capture_browser(self, full_page=False):
        _ = full_page
        return self._screenshot


@pytest.mark.asyncio
async def test_navigate_and_screenshot() -> None:
    adapter = BrowserAdapter()
    adapter._page = FakePage()
    adapter._eye = FakeEye()

    result = await adapter.execute(
        Capability.WEB_NAVIGATE,
        {"url": "https://example.com"},
        ExecutionContext(session_id="test", domain="test"),
    )

    assert result.success
    assert "example.com" in result.data["url"]

    shot = await adapter.execute(
        Capability.WEB_SCREENSHOT,
        {},
        ExecutionContext(session_id="test", domain="test"),
    )

    assert shot.success
    assert shot.screenshot_ref is not None
