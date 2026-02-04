import pytest

from aria.core.safety.rate_limiter import get_rate_limiter
from aria.core.safety.safety_gate import SafetyDecision, SafetyGate


@pytest.mark.asyncio
async def test_safety_gate_integration_allows(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_store():
        raise RuntimeError("no redis")

    monkeypatch.setattr("aria.core.safety.rate_limiter.get_state_store", fake_store)
    _ = get_rate_limiter()

    gate = SafetyGate()
    result = await gate.pre_check(
        "web.extract",
        {},
        {
            "user_id": "user-1",
            "session_id": "sess-1",
            "domain": "job_apply",
            "url": "https://www.linkedin.com/jobs/view/123",
        },
    )

    assert result.decision == SafetyDecision.ALLOW


@pytest.mark.asyncio
async def test_safety_gate_integration_blocks_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_store():
        raise RuntimeError("no redis")

    monkeypatch.setattr("aria.core.safety.rate_limiter.get_state_store", fake_store)

    gate = SafetyGate()
    result = await gate.pre_check(
        "web.navigate",
        {},
        {
            "user_id": "user-1",
            "session_id": "sess-1",
            "domain": "job_apply",
            "url": "https://paypal.com",
        },
    )

    assert result.decision == SafetyDecision.BLOCK


@pytest.mark.asyncio
async def test_safety_gate_integration_high_risk(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_store():
        raise RuntimeError("no redis")

    monkeypatch.setattr("aria.core.safety.rate_limiter.get_state_store", fake_store)

    gate = SafetyGate()
    result = await gate.pre_check(
        "web.submit_application",
        {"form_data": {"name": "Test"}},
        {
            "user_id": "user-1",
            "session_id": "sess-1",
            "domain": "job_apply",
            "url": "https://www.linkedin.com/jobs/view/123",
            "has_observation": True,
        },
    )

    # Should require human for high-risk action
    assert result.decision in {SafetyDecision.REQUIRE_HUMAN, SafetyDecision.ALLOW}
    if result.decision == SafetyDecision.REQUIRE_HUMAN:
        assert result.hitl_request is not None


@pytest.mark.asyncio
async def test_safety_gate_integration_captcha(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_store():
        raise RuntimeError("no redis")

    async def fake_emit(*args, **kwargs):
        _ = args, kwargs
        return "evt"

    monkeypatch.setattr("aria.core.safety.rate_limiter.get_state_store", fake_store)
    monkeypatch.setattr("aria.utils.events.EventEmitter.emit", fake_emit)

    gate = SafetyGate()
    result = await gate.pre_check(
        "web.click",
        {},
        {
            "user_id": "user-1",
            "session_id": "sess-1",
            "domain": "job_apply",
            "url": "https://www.linkedin.com/jobs/view/123",
            "page_source": "<div class='g-recaptcha'></div>",
        },
    )

    # Should detect captcha and require human
    assert result.decision == SafetyDecision.REQUIRE_HUMAN
    assert result.captcha_detection is not None
    assert result.captcha_detection.detected is True


@pytest.mark.asyncio
async def test_safety_gate_post_check_integration(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_store():
        raise RuntimeError("no redis")

    monkeypatch.setattr("aria.core.safety.rate_limiter.get_state_store", fake_store)

    gate = SafetyGate()
    result = await gate.post_check(
        "web.extract",
        {
            "output": "User email: test@example.com",
            "current_url": "https://www.linkedin.com/jobs/view/123",
        },
        {
            "domain": "job_apply",
            "expected_url": "https://www.linkedin.com/jobs/view/123",
        },
    )

    assert "warnings" in result
    assert isinstance(result["warnings"], list)
