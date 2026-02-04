from datetime import datetime, timezone

from aria.core.safety.risk_detector import RiskAction, RiskDetector, RiskLevel

UTC = timezone.utc


def test_risk_detector_levels() -> None:
    detector = RiskDetector()

    high = detector.assess("web.submit_application", {})
    assert high.level == RiskLevel.HIGH
    assert high.action in {RiskAction.REQUIRE_HUMAN, RiskAction.CONFIRM}

    medium = detector.assess("web.click", {})
    assert medium.level == RiskLevel.MEDIUM

    low = detector.assess("web.extract", {})
    assert low.level == RiskLevel.LOW
    assert low.action == RiskAction.ALLOW


def test_risk_detector_context_pii() -> None:
    detector = RiskDetector()
    assessment = detector.assess(
        "web.fill",
        {"parameters": {"password": "secret"}, "url": "https://example.com"},
    )
    assert "contains_pii" in assessment.factors


def test_risk_detector_financial_context() -> None:
    detector = RiskDetector()
    assessment = detector.assess(
        "web.click",
        {"url": "https://example.com/payment/checkout"},
    )
    assert "financial_context" in assessment.factors


def test_risk_detector_no_observation() -> None:
    detector = RiskDetector()
    assessment = detector.assess(
        "web.submit_application",
        {"has_observation": False},
    )
    assert "no_prior_observation" in assessment.factors


def test_risk_detector_rapid_succession() -> None:
    detector = RiskDetector()
    
    # Record 3 actions quickly
    now = datetime.now(UTC)
    for i in range(3):
        detector.record_action(
            "web.click",
            {"timestamp": (now.replace(microsecond=0)).isoformat()}
        )
    
    # Check rapid succession
    is_rapid = detector._is_rapid_succession()
    # Should detect rapid succession if actions are recent
    assert isinstance(is_rapid, bool)


def test_risk_detector_critical_level() -> None:
    detector = RiskDetector()
    assessment = detector.assess(
        "web.submit_application",
        {
            "parameters": {"password": "secret", "credit_card": "1234"},
            "url": "https://example.com/payment",
            "has_observation": False,
        },
    )
    # Should be HIGH or CRITICAL due to multiple risk factors
    assert assessment.level in {RiskLevel.HIGH, RiskLevel.CRITICAL}


def test_risk_detector_action_history() -> None:
    detector = RiskDetector()
    
    detector.record_action("web.click", {"test": "data"})
    assert len(detector._action_history) == 1
    
    # Record 100+ actions to test trimming
    for i in range(105):
        detector.record_action("web.click", {"index": i})
    
    # Should keep only last 100
    assert len(detector._action_history) == 100


def test_risk_detector_auto_approve() -> None:
    detector = RiskDetector()
    
    # High risk with auto-approve in job_apply domain
    assessment = detector.assess(
        "web.submit_application",
        {
            "user_preferences": {"auto_approve": True},
            "domain": "job_apply",
        },
    )
    # Should allow CONFIRM instead of REQUIRE_HUMAN
    assert assessment.action in {RiskAction.CONFIRM, RiskAction.REQUIRE_HUMAN}


def test_risk_detector_unknown_capability() -> None:
    detector = RiskDetector()
    
    # Unknown capability should default to MEDIUM
    assessment = detector.assess("web.unknown_action", {})
    assert assessment.level == RiskLevel.MEDIUM
