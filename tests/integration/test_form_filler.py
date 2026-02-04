import pytest

from aria.adapters.browser.form_filler import FormFiller
from aria.core.eye.models import Element, ElementType, Location, Observation, PageState


class FakePage:
    def __init__(self) -> None:
        self.filled = []

    async def fill(self, selector, value):
        self.filled.append((selector, value))

    class _Mouse:
        async def click(self, x, y):
            _ = x
            _ = y

    class _Keyboard:
        async def type(self, value):
            _ = value

    @property
    def mouse(self):
        return self._Mouse()

    @property
    def keyboard(self):
        return self._Keyboard()


class FakeBrowserAdapter:
    def __init__(self) -> None:
        self.page = FakePage()


class FakeEye:
    async def observe(self, domain, source):
        _ = domain
        _ = source
        return Observation(
            observation_id="obs-1",
            source="browser",
            screenshot_ref="s1",
            state=PageState.READY,
            elements=[
                Element(
                    element_id="first-name",
                    type=ElementType.INPUT,
                    text="First Name",
                    location=Location(x=10, y=10, width=100, height=20),
                    attributes={"id": "first-name"},
                ),
            ],
            vlm_analysis={"elements": []},
        )

    async def locate_element(self, description):
        _ = description
        return Element(
            element_id="fallback",
            type=ElementType.INPUT,
            text="Email",
            location=Location(x=50, y=50, width=120, height=20),
        )


@pytest.mark.asyncio
async def test_fill_form_with_selector(monkeypatch) -> None:
    fake_eye = FakeEye()
    async def fake_get_eye():
        return fake_eye

    monkeypatch.setattr("aria.adapters.browser.form_filler.get_eye", fake_get_eye)

    filler = FormFiller(FakeBrowserAdapter())
    result = await filler.fill_form({"First Name": "Alice"})

    assert result.success
    assert "First Name" in result.data["filled"]


@pytest.mark.asyncio
async def test_fill_with_vision(monkeypatch) -> None:
    fake_eye = FakeEye()
    async def fake_get_eye():
        return fake_eye

    monkeypatch.setattr("aria.adapters.browser.form_filler.get_eye", fake_get_eye)

    filler = FormFiller(FakeBrowserAdapter())
    result = await filler.fill_with_vision("Email", "a@example.com")

    assert result.success
