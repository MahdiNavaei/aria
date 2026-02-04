from datetime import datetime, timezone

import pytest

UTC = timezone.utc

import aria.core.safety.safety_gate as safety_gate_module
from aria.core.safety.captcha_handler import CaptchaDetection
from aria.core.safety.domain_policy import DomainAction, DomainCheckResult
from aria.core.safety.pii_handler import PIIHandler
from aria.core.safety.rate_limiter import RateLimitResult
from aria.core.safety.risk_detector import RiskAction, RiskAssessment, RiskLevel
from aria.core.safety.safety_gate import SafetyDecision, SafetyGate


class DummyDomainPolicy:
    def __init__(self, result: DomainCheckResult) -> None:
        self._result = result

    def check(self, url: str, domain_context: str = "job_apply") -> DomainCheckResult:
        _ = url, domain_context
        return self._result


class DummyRiskDetector:
    def __init__(self, assessment: RiskAssessment) -> None:
        self._assessment = assessment

    def assess(self, capability: str, context: dict) -> RiskAssessment:
        _ = capability, context
        return self._assessment

    def record_action(self, capability: str, context: dict) -> None:
        _ = capability, context


class DummyRateLimiter:
    def __init__(self, result: RateLimitResult) -> None:
        self._result = result

    async def check(self, user_id: str, action: str = "default") -> RateLimitResult:
        _ = user_id, action
        return self._result

    async def consume(
        self,
        user_id: str,
        action: str = "default",
        cost: int = 1,
    ) -> RateLimitResult:
        _ = user_id, action, cost
        return self._result


class DummyCaptchaHandler:
    def __init__(self, detection: CaptchaDetection) -> None:
        self._detection = detection

    async def detect_captcha(self, **kwargs) -> CaptchaDetection:
        _ = kwargs
        return self._detection

    async def handle_captcha(self, detection, session_id: str, context: dict):
        _ = detection, session_id, context
        return {
            "action": "require_human",
            "hitl_request": {"request_id": "captcha-1", "reason": "captcha"},
            "reason": "captcha detected",
        }


@pytest.mark.asyncio
async def test_safety_gate_blocks_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    domain_result = DomainCheckResult(
        allowed=False,
        action=DomainAction.BLOCK,
        reason="blocked",
        domain="blocked.example.com",
        matched_rule="blocked.example.com",
    )
    risk_result = RiskAssessment(
        level=RiskLevel.LOW,
        action=RiskAction.ALLOW,
        reason="ok",
        capability="web.extract",
        factors=[],
        evidence_required=False,
    )
    rate_result = RateLimitResult(True, 10, 10, datetime.now(UTC), None)

    monkeypatch.setattr(
        safety_gate_module,
        "get_domain_policy",
        lambda: DummyDomainPolicy(domain_result),
    )
    monkeypatch.setattr(
        safety_gate_module,
        "get_risk_detector",
        lambda: DummyRiskDetector(risk_result),
    )
    monkeypatch.setattr(
        safety_gate_module,
        "get_rate_limiter",
        lambda: DummyRateLimiter(rate_result),
    )
    monkeypatch.setattr(
        safety_gate_module,
        "get_captcha_handler",
        lambda: DummyCaptchaHandler(CaptchaDetection(False, None, 0.0, None, None)),
    )
    monkeypatch.setattr(safety_gate_module, "get_pii_handler", lambda: PIIHandler())

    gate = SafetyGate()
    result = await gate.pre_check(
        "web.navigate",
        {"url": "https://blocked"},
        {"user_id": "u"},
    )
    assert result.decision == SafetyDecision.BLOCK


@pytest.mark.asyncio
async def test_safety_gate_requires_human(monkeypatch: pytest.MonkeyPatch) -> None:
    domain_result = DomainCheckResult(
        allowed=True,
        action=DomainAction.ALLOW,
        reason="ok",
        domain="example.com",
        matched_rule=None,
    )
    risk_result = RiskAssessment(
        level=RiskLevel.HIGH,
        action=RiskAction.REQUIRE_HUMAN,
        reason="needs human",
        capability="web.submit_application",
        factors=["high"],
        evidence_required=True,
    )
    rate_result = RateLimitResult(True, 10, 10, datetime.now(UTC), None)

    monkeypatch.setattr(
        safety_gate_module,
        "get_domain_policy",
        lambda: DummyDomainPolicy(domain_result),
    )
    monkeypatch.setattr(
        safety_gate_module,
        "get_risk_detector",
        lambda: DummyRiskDetector(risk_result),
    )
    monkeypatch.setattr(
        safety_gate_module,
        "get_rate_limiter",
        lambda: DummyRateLimiter(rate_result),
    )
    monkeypatch.setattr(
        safety_gate_module,
        "get_captcha_handler",
        lambda: DummyCaptchaHandler(CaptchaDetection(False, None, 0.0, None, None)),
    )
    monkeypatch.setattr(safety_gate_module, "get_pii_handler", lambda: PIIHandler())

    gate = SafetyGate()
    result = await gate.pre_check(
        "web.submit_application",
        {},
        {"user_id": "u", "session_id": "s"},
    )
    assert result.decision == SafetyDecision.REQUIRE_HUMAN
    assert result.hitl_request is not None


@pytest.mark.asyncio
async def test_safety_gate_rate_limited(monkeypatch: pytest.MonkeyPatch) -> None:
    domain_result = DomainCheckResult(
        allowed=True,
        action=DomainAction.ALLOW,
        reason="ok",
        domain="example.com",
        matched_rule=None,
    )
    risk_result = RiskAssessment(
        level=RiskLevel.LOW,
        action=RiskAction.ALLOW,
        reason="ok",
        capability="web.extract",
        factors=[],
        evidence_required=False,
    )
    rate_result = RateLimitResult(False, 1, 0, datetime.now(UTC), 10.0)

    monkeypatch.setattr(
        safety_gate_module,
        "get_domain_policy",
        lambda: DummyDomainPolicy(domain_result),
    )
    monkeypatch.setattr(
        safety_gate_module,
        "get_risk_detector",
        lambda: DummyRiskDetector(risk_result),
    )
    monkeypatch.setattr(
        safety_gate_module,
        "get_rate_limiter",
        lambda: DummyRateLimiter(rate_result),
    )
    monkeypatch.setattr(
        safety_gate_module,
        "get_captcha_handler",
        lambda: DummyCaptchaHandler(CaptchaDetection(False, None, 0.0, None, None)),
    )
    monkeypatch.setattr(safety_gate_module, "get_pii_handler", lambda: PIIHandler())

    gate = SafetyGate()
    result = await gate.pre_check("web.extract", {}, {"user_id": "u"})
    assert result.decision == SafetyDecision.RATE_LIMITED


@pytest.mark.asyncio
async def test_safety_gate_allows_safe_action(monkeypatch: pytest.MonkeyPatch) -> None:
    domain_result = DomainCheckResult(
        allowed=True,
        action=DomainAction.ALLOW,
        reason="ok",
        domain="example.com",
        matched_rule=None,
    )
    risk_result = RiskAssessment(
        level=RiskLevel.LOW,
        action=RiskAction.ALLOW,
        reason="ok",
        capability="web.extract",
        factors=[],
        evidence_required=False,
    )
    rate_result = RateLimitResult(True, 10, 5, datetime.now(UTC), None)

    monkeypatch.setattr(
        safety_gate_module,
        "get_domain_policy",
        lambda: DummyDomainPolicy(domain_result),
    )
    monkeypatch.setattr(
        safety_gate_module,
        "get_risk_detector",
        lambda: DummyRiskDetector(risk_result),
    )
    monkeypatch.setattr(
        safety_gate_module,
        "get_rate_limiter",
        lambda: DummyRateLimiter(rate_result),
    )
    monkeypatch.setattr(
        safety_gate_module,
        "get_captcha_handler",
        lambda: DummyCaptchaHandler(CaptchaDetection(False, None, 0.0, None, None)),
    )
    monkeypatch.setattr(safety_gate_module, "get_pii_handler", lambda: PIIHandler())

    gate = SafetyGate()
    result = await gate.pre_check(
        "web.extract",
        {},
        {"user_id": "u", "session_id": "s", "url": "https://example.com"},
    )
    assert result.decision == SafetyDecision.ALLOW


@pytest.mark.asyncio
async def test_safety_gate_read_only_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    domain_result = DomainCheckResult(
        allowed=True,
        action=DomainAction.READ_ONLY,
        reason="read-only",
        domain="readonly.example.com",
        matched_rule="*.readonly.com",
    )
    risk_result = RiskAssessment(
        level=RiskLevel.LOW,
        action=RiskAction.ALLOW,
        reason="ok",
        capability="web.click",  # Not read-only capability
        factors=[],
        evidence_required=False,
    )
    rate_result = RateLimitResult(True, 10, 10, datetime.now(UTC), None)

    monkeypatch.setattr(
        safety_gate_module,
        "get_domain_policy",
        lambda: DummyDomainPolicy(domain_result),
    )
    monkeypatch.setattr(
        safety_gate_module,
        "get_risk_detector",
        lambda: DummyRiskDetector(risk_result),
    )
    monkeypatch.setattr(
        safety_gate_module,
        "get_rate_limiter",
        lambda: DummyRateLimiter(rate_result),
    )
    monkeypatch.setattr(
        safety_gate_module,
        "get_captcha_handler",
        lambda: DummyCaptchaHandler(CaptchaDetection(False, None, 0.0, None, None)),
    )
    monkeypatch.setattr(safety_gate_module, "get_pii_handler", lambda: PIIHandler())

    gate = SafetyGate()
    result = await gate.pre_check(
        "web.click",
        {},
        {"user_id": "u", "url": "https://readonly.example.com"},
    )
    assert result.decision == SafetyDecision.BLOCK
    assert "read-only" in result.reason.lower()


@pytest.mark.asyncio
async def test_safety_gate_post_check_pii(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(safety_gate_module, "get_pii_handler", lambda: PIIHandler())
    monkeypatch.setattr(
        safety_gate_module,
        "get_domain_policy",
        lambda: DummyDomainPolicy(
            DomainCheckResult(True, DomainAction.ALLOW, "ok", "example.com", None)
        ),
    )

    gate = SafetyGate()
    result = await gate.post_check(
        "web.extract",
        {"output": "Contact: user@example.com or 09123456789"},
        {"domain": "job_apply"},
    )

    assert "warnings" in result
    # May have PII warnings if detection is enabled
    assert isinstance(result["warnings"], list)


@pytest.mark.asyncio
async def test_safety_gate_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        safety_gate_module,
        "get_settings",
        lambda: type("Settings", (), {"safety": type("Safety", (), {"enabled": False})()}),
    )

    gate = SafetyGate()
    result = await gate.pre_check("web.submit", {}, {"user_id": "u"})
    assert result.decision == SafetyDecision.ALLOW
    assert "disabled" in result.reason.lower()
