from datetime import UTC, datetime

import pytest

from aria.core.hand import Hand
from aria.core.hand.capability import Capability, CapabilityResult
from aria.core.safety.rate_limiter import RateLimitResult
from aria.core.safety.safety_gate import get_safety_gate


class _AllowingRateLimiter:
    async def check(self, user_id, action="default"):
        _ = user_id
        _ = action

        return RateLimitResult(
            allowed=True,
            limit=100,
            remaining=99,
            reset_at=datetime.now(UTC),
            retry_after=None,
        )

    async def consume(self, user_id, action="default", cost=1):
        _ = cost
        return await self.check(user_id, action)


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
    get_safety_gate().rate_limiter = _AllowingRateLimiter()

    result = await hand.execute(
        "ml.extract_job_info",
        {"text": "Software Engineer at Example."},
        {
            "session_id": "test",
            "domain": "job_apply",
            "has_observation": True,
            "user_preferences": {"auto_approve": True},
        },
    )

    assert result.success
    assert "title" in result.data
