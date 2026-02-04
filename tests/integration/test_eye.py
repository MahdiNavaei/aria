import io

import pytest
from PIL import Image

from aria.core.eye.eye import Eye
from aria.core.eye.models import PageState
from aria.core.eye.screenshot import Screenshot


class FakeScreenshotService:
    def __init__(self) -> None:
        image = Image.new("RGB", (200, 120), color="white")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        self._screenshot = Screenshot(
            image_bytes=buffer.getvalue(),
            width=200,
            height=120,
            source="browser",
            metadata={"url": "https://example.com", "title": "Example"},
            image_format="png",
        )

    async def capture(self, source="browser", **kwargs):
        return self._screenshot

    def set_browser_page(self, page):
        return None


class FakeVLMAnalyzer:
    async def analyze(self, screenshot):
        return {
            "page_type": "form",
            "title": "Example",
            "elements": [
                {
                    "type": "button",
                    "text": "Submit",
                    "location": {"x": 10, "y": 10, "width": 100, "height": 40},
                },
            ],
            "state": "ready",
            "blockers": [],
            "observations": ["Ready for input"],
        }

    async def locate_element(self, screenshot, description):
        return {
            "type": "button",
            "text": "Submit",
            "location": {"x": 10, "y": 10, "width": 100, "height": 40},
            "confidence": 0.9,
        }


class FakeUIRefExtractor:
    def set_browser_page(self, page):
        return None

    async def extract_from_element(self, element_handle, description, domain):
        return None

    async def save_uiref(self, uiref):
        return None


@pytest.mark.asyncio
async def test_eye_observe(monkeypatch) -> None:
    fake_screenshot_service = FakeScreenshotService()
    fake_vlm = FakeVLMAnalyzer()
    fake_uiref = FakeUIRefExtractor()

    monkeypatch.setattr(
        "aria.core.eye.eye.get_screenshot_service", lambda: fake_screenshot_service,
    )
    monkeypatch.setattr("aria.core.eye.eye.get_vlm_analyzer", lambda: fake_vlm)
    monkeypatch.setattr(
        "aria.core.eye.eye.get_uiref_extractor", lambda: fake_uiref,
    )

    eye = Eye()
    observation = await eye.observe(domain="job_apply", source="browser")

    assert observation.observation_id is not None
    assert observation.page_url == "https://example.com"
    assert observation.state in {PageState.READY, PageState.BLOCKED}
    assert observation.elements


@pytest.mark.asyncio
async def test_eye_locate_element(monkeypatch) -> None:
    fake_screenshot_service = FakeScreenshotService()
    fake_vlm = FakeVLMAnalyzer()
    fake_uiref = FakeUIRefExtractor()

    monkeypatch.setattr(
        "aria.core.eye.eye.get_screenshot_service", lambda: fake_screenshot_service,
    )
    monkeypatch.setattr("aria.core.eye.eye.get_vlm_analyzer", lambda: fake_vlm)
    monkeypatch.setattr(
        "aria.core.eye.eye.get_uiref_extractor", lambda: fake_uiref,
    )

    eye = Eye()
    element = await eye.locate_element("Submit button")

    assert element is not None
    assert element.text == "Submit"
