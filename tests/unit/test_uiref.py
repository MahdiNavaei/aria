import pytest

from aria.core.eye.uiref import LocatorType, UIRefExtractor


class FakeElementHandle:
    def __init__(self) -> None:
        self._attrs = {
            "id": "submit-btn",
            "data-testid": "submit",
            "aria-label": "Submit",
            "role": "button",
            "name": "submit",
        }

    async def get_attribute(self, name: str):
        return self._attrs.get(name)

    async def inner_text(self):
        return "Submit"

    async def evaluate(self, script: str):
        return "/html/body/main/button"


class FakePage:
    url = "https://example.com/apply"


class FakeSemanticMemory:
    def __init__(self) -> None:
        self._data = {}

    async def add_uiref(self, uiref_id, uiref_def, description):
        self._data[uiref_id] = uiref_def

    async def get_uiref(self, uiref_id):
        return self._data.get(uiref_id)


@pytest.mark.asyncio
async def test_extract_uiref_and_save() -> None:
    memory = FakeSemanticMemory()
    extractor = UIRefExtractor(semantic_memory=memory)
    extractor.set_browser_page(FakePage())

    uiref = await extractor.extract_from_element(
        FakeElementHandle(),
        description="Submit button",
        domain="job_apply",
    )

    assert uiref.uiref_id.startswith("job_apply.")
    assert any(locator.type == LocatorType.CSS for locator in uiref.locators)

    await extractor.save_uiref(uiref)

    loaded = await extractor.get_uiref(uiref.uiref_id)
    assert loaded is not None
    assert loaded.uiref_id == uiref.uiref_id
