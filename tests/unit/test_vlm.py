import pytest

from aria.core.eye.vlm import VLMAnalyzer
from aria.core.llm.base import LLMResponse


class FakeLLM:
    def __init__(self, content: str) -> None:
        self._content = content

    async def generate(self, messages, **kwargs):
        return LLMResponse(content=self._content, model="fake", tokens_used=1)


class FakeScreenshot:
    def __init__(self) -> None:
        self.base64 = "fake"


@pytest.mark.asyncio
async def test_vlm_analyze(monkeypatch) -> None:
    response = """
    Here is the analysis:
    {
        "page_type": "form",
        "title": "Test",
        "elements": [{"type": "button", "text": "Submit"}],
        "state": "ready",
        "blockers": []
    }
    """
    fake_llm = FakeLLM(response)
    monkeypatch.setattr("aria.core.eye.vlm.get_llm_client", lambda: fake_llm)

    analyzer = VLMAnalyzer()
    analysis = await analyzer.analyze(FakeScreenshot())

    assert analysis["page_type"] == "form"
    assert len(analysis["elements"]) == 1


@pytest.mark.asyncio
async def test_vlm_locate_element_found(monkeypatch) -> None:
    response = """
    {
        "found": true,
        "element": {"type": "button", "text": "Submit", "confidence": 0.9}
    }
    """
    fake_llm = FakeLLM(response)
    monkeypatch.setattr("aria.core.eye.vlm.get_llm_client", lambda: fake_llm)

    analyzer = VLMAnalyzer()
    element = await analyzer.locate_element(FakeScreenshot(), "Submit button")

    assert element is not None
    assert element["text"] == "Submit"


@pytest.mark.asyncio
async def test_vlm_locate_element_not_found(monkeypatch) -> None:
    response = '{"found": false, "reason": "not visible"}'
    fake_llm = FakeLLM(response)
    monkeypatch.setattr("aria.core.eye.vlm.get_llm_client", lambda: fake_llm)

    analyzer = VLMAnalyzer()
    element = await analyzer.locate_element(FakeScreenshot(), "Submit button")

    assert element is None
