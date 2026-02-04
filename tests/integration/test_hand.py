import pytest

from aria.core.hand import Hand
from aria.core.hand.capability import Capability, CapabilityResult


@pytest.mark.asyncio
async def test_hand_initialization(monkeypatch) -> None:
    async def noop(self):
        return None

    monkeypatch.setattr("aria.adapters.browser.adapter.BrowserAdapter.initialize", noop)
    monkeypatch.setattr("aria.adapters.browser.adapter.BrowserAdapter.cleanup", noop)
    monkeypatch.setattr("aria.adapters.desktop.adapter.DesktopAdapter.initialize", noop)
    monkeypatch.setattr("aria.adapters.desktop.adapter.DesktopAdapter.cleanup", noop)
    monkeypatch.setattr("aria.adapters.ml.adapter.MLAdapter.__init__", lambda self: None)
    monkeypatch.setattr("aria.adapters.ml.adapter.MLAdapter.initialize", noop, raising=False)
    monkeypatch.setattr("aria.adapters.ml.adapter.MLAdapter.cleanup", noop, raising=False)

    hand = Hand()
    await hand.initialize()
    assert hand._initialized
    await hand.cleanup()


@pytest.mark.asyncio
async def test_capability_routing(monkeypatch) -> None:
    async def noop(self):
        return None

    monkeypatch.setattr("aria.adapters.browser.adapter.BrowserAdapter.initialize", noop)
    monkeypatch.setattr("aria.adapters.desktop.adapter.DesktopAdapter.initialize", noop)
    monkeypatch.setattr("aria.adapters.ml.adapter.MLAdapter.__init__", lambda self: None)
    monkeypatch.setattr("aria.adapters.ml.adapter.MLAdapter.initialize", noop, raising=False)

    hand = Hand()
    await hand.initialize()

    assert hand.get_adapter(Capability.WEB_NAVIGATE) is not None
    assert hand.get_adapter(Capability.ML_MATCH_JOB) is not None


@pytest.mark.asyncio
async def test_execute_ml(monkeypatch) -> None:
    async def noop(self):
        return None

    async def fake_execute(self, capability, parameters, context):
        _ = capability
        _ = parameters
        _ = context
        return CapabilityResult.ok({"title": "Software Engineer"})

    monkeypatch.setattr("aria.adapters.browser.adapter.BrowserAdapter.initialize", noop)
    monkeypatch.setattr("aria.adapters.desktop.adapter.DesktopAdapter.initialize", noop)
    monkeypatch.setattr("aria.adapters.ml.adapter.MLAdapter.__init__", lambda self: None)
    monkeypatch.setattr("aria.adapters.ml.adapter.MLAdapter.initialize", noop, raising=False)
    monkeypatch.setattr("aria.adapters.ml.adapter.MLAdapter.execute", fake_execute)

    hand = Hand()
    await hand.initialize()

    result = await hand.execute(
        "ml.extract_job_info",
        {"text": "Software Engineer at Example."},
        {"session_id": "test", "domain": "job_apply"},
    )

    assert result.success
    assert "title" in result.data
