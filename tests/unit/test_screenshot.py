import io

import pytest
from PIL import Image

from aria.core.eye.screenshot import ScreenshotService


class FakePage:
    def __init__(self) -> None:
        self.url = "https://example.com"
        self.viewport_size = {"width": 640, "height": 480}

    async def screenshot(self, **kwargs):
        image = Image.new("RGB", (640, 480), color="white")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    async def title(self):
        return "Example Domain"


@pytest.mark.asyncio
async def test_capture_browser(tmp_path) -> None:
    service = ScreenshotService(storage_dir=tmp_path)
    service.set_browser_page(FakePage())

    screenshot = await service.capture_browser()

    assert screenshot.source == "browser"
    assert screenshot.width == 640
    assert screenshot.height == 480
    assert (tmp_path / f"{screenshot.ref}.png").exists()


@pytest.mark.asyncio
async def test_capture_desktop(tmp_path, monkeypatch) -> None:
    def fake_screenshot(region=None):
        return Image.new("RGB", (320, 200), color="blue")

    monkeypatch.setattr("aria.core.eye.screenshot.pyautogui.screenshot", fake_screenshot)

    service = ScreenshotService(storage_dir=tmp_path)
    screenshot = await service.capture_desktop()

    assert screenshot.source == "desktop"
    assert screenshot.width == 320
    assert screenshot.height == 200
    assert (tmp_path / f"{screenshot.ref}.png").exists()


def test_get_screenshot(tmp_path) -> None:
    service = ScreenshotService(storage_dir=tmp_path)
    image = Image.new("RGB", (100, 50), color="green")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    file_path = tmp_path / "screenshot_test.png"
    file_path.write_bytes(buffer.getvalue())

    loaded = service.get_screenshot("screenshot_test")

    assert loaded is not None
    assert loaded.width == 100
    assert loaded.height == 50
