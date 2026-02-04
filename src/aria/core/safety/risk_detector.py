"""Risk Detector for ARIA Safety."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, NamedTuple

from aria.utils.logging import get_logger

logger = get_logger(__name__)


class RiskLevel(str, Enum):
    """Risk level classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskAction(str, Enum):
    """Recommended action for risk level."""

    ALLOW = "allow"
    LOG = "log"
    CONFIRM = "confirm"
    REQUIRE_HUMAN = "require_human"
    BLOCK = "block"


class RiskAssessment(NamedTuple):
    """Result of risk assessment."""

    level: RiskLevel
    action: RiskAction
    reason: str
    capability: str
    factors: list[str]
    evidence_required: bool


class RiskDetector:
    """Detect and classify risk levels for capabilities."""

    HIGH_RISK_CAPABILITIES = {
        "web.submit_application",
        "web.click_submit",
        "web.final_submit",
        "web.upload_file",
        "web.upload_resume",
        "web.upload_cover_letter",
        "web.login",
        "web.enter_credentials",
        "web.enter_password",
        "desktop.run_command",
        "desktop.delete_file",
        "desktop.modify_system",
        "web.click_payment",
        "web.enter_card_info",
    }

    MEDIUM_RISK_CAPABILITIES = {
        "web.fill_form",
        "web.fill",
        "web.type",
        "web.select",
        "web.click",
        "desktop.click",
        "desktop.type",
        "desktop.hotkey",
        "web.navigate",
    }

    LOW_RISK_CAPABILITIES = {
        "web.extract",
        "web.screenshot",
        "web.get_text",
        "web.scroll",
        "web.wait",
        "desktop.screenshot",
        "desktop.read_screen",
        "ml.match_job",
        "ml.extract_job_info",
        "ml.generate_cover_letter",
    }

    RISK_INCREASING_FACTORS = {
        "contains_pii": 0.2,
        "financial_context": 0.3,
        "first_time_domain": 0.1,
        "unusual_time": 0.1,
        "rapid_succession": 0.15,
        "no_prior_observation": 0.1,
    }

    def __init__(
        self,
        high_risk: set[str] | None = None,
        medium_risk: set[str] | None = None,
        low_risk: set[str] | None = None,
    ) -> None:
        self._action_history: list[dict[str, Any]] = []
        self._high_risk = high_risk or set(self.HIGH_RISK_CAPABILITIES)
        self._medium_risk = medium_risk or set(self.MEDIUM_RISK_CAPABILITIES)
        self._low_risk = low_risk or set(self.LOW_RISK_CAPABILITIES)

    def assess(
        self,
        capability: str,
        context: dict[str, Any] | None = None,
    ) -> RiskAssessment:
        """Assess risk level for a capability."""
        context = context or {}
        factors: list[str] = []

        base_level = self._get_base_level(capability)
        adjusted_level, context_factors = self._adjust_for_context(
            base_level, capability, context
        )
        factors.extend(context_factors)

        action = self._determine_action(adjusted_level, context)
        evidence_required = adjusted_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}
        reason = self._build_reason(capability, adjusted_level, factors)

        assessment = RiskAssessment(
            level=adjusted_level,
            action=action,
            reason=reason,
            capability=capability,
            factors=factors,
            evidence_required=evidence_required,
        )

        logger.debug(
            "Risk assessment completed",
            capability=capability,
            level=adjusted_level,
            action=action,
        )

        return assessment

    def _get_base_level(self, capability: str) -> RiskLevel:
        """Get base risk level from classification."""
        if capability in self._high_risk:
            return RiskLevel.HIGH
        if capability in self._medium_risk:
            return RiskLevel.MEDIUM
        if capability in self._low_risk:
            return RiskLevel.LOW
        return RiskLevel.MEDIUM

    def _adjust_for_context(
        self,
        base_level: RiskLevel,
        capability: str,
        context: dict[str, Any],
    ) -> tuple[RiskLevel, list[str]]:
        """Adjust risk level based on context."""
        _ = capability
        factors: list[str] = []
        risk_score = {"low": 0, "medium": 1, "high": 2, "critical": 3}[base_level]

        params = context.get("parameters", {})
        if self._contains_pii(params):
            risk_score += 0.5
            factors.append("contains_pii")

        url = context.get("url", "")
        if any(word in url.lower() for word in ["payment", "checkout", "billing"]):
            risk_score += 0.5
            factors.append("financial_context")

        if context.get("first_visit", False):
            risk_score += 0.3
            factors.append("first_time_domain")

        if self._is_rapid_succession():
            risk_score += 0.3
            factors.append("rapid_succession")

        if not context.get("has_observation", True):
            risk_score += 0.2
            factors.append("no_prior_observation")

        if risk_score >= 3:
            return RiskLevel.CRITICAL, factors
        if risk_score >= 2:
            return RiskLevel.HIGH, factors
        if risk_score >= 1:
            return RiskLevel.MEDIUM, factors
        return RiskLevel.LOW, factors

    def _determine_action(
        self,
        level: RiskLevel,
        context: dict[str, Any],
    ) -> RiskAction:
        """Determine recommended action based on risk level."""
        auto_approve = context.get("user_preferences", {}).get("auto_approve", False)

        if level == RiskLevel.CRITICAL:
            return RiskAction.BLOCK
        if level == RiskLevel.HIGH:
            if auto_approve and context.get("domain") == "job_apply":
                return RiskAction.CONFIRM
            return RiskAction.REQUIRE_HUMAN
        if level == RiskLevel.MEDIUM:
            return RiskAction.LOG if auto_approve else RiskAction.CONFIRM
        return RiskAction.ALLOW

    def _contains_pii(self, params: dict[str, Any]) -> bool:
        """Check if parameters contain PII indicators."""
        pii_keywords = {
            "password",
            "ssn",
            "social_security",
            "credit_card",
            "card_number",
            "cvv",
            "pin",
            "national_id",
            "passport",
        }

        def check_value(value: Any) -> bool:  # noqa: ANN401
            if isinstance(value, str):
                return any(keyword in value.lower() for keyword in pii_keywords)
            if isinstance(value, dict):
                return any(check_value(val) for val in value.values())
            return False

        return any(
            key.lower() in pii_keywords or check_value(value)
            for key, value in params.items()
        )

    def _is_rapid_succession(self) -> bool:
        """Check if actions are happening too quickly."""
        if len(self._action_history) < 3:
            return False
        
        # Check last 3 actions - if they happened within 5 seconds, it's rapid
        recent_actions = self._action_history[-3:]
        now = datetime.now(UTC)
        
        for action_record in recent_actions:
            try:
                action_time = datetime.fromisoformat(action_record["timestamp"].replace("Z", "+00:00"))
                time_diff = (now - action_time.replace(tzinfo=UTC)).total_seconds()
                
                # If any action happened less than 5 seconds ago, consider it rapid
                if time_diff < 5.0:
                    return True
            except (ValueError, KeyError, TypeError):
                # Skip invalid timestamps
                continue
        
        return False

    def _build_reason(
        self,
        capability: str,
        level: RiskLevel,
        factors: list[str],
    ) -> str:
        """Build human-readable reason."""
        if level == RiskLevel.CRITICAL:
            return (
                f"Capability '{capability}' is blocked: "
                f"{', '.join(factors) or 'critical risk'}"
            )
        if level == RiskLevel.HIGH:
            return (
                f"High-risk action '{capability}' requires human confirmation: "
                f"{', '.join(factors) or 'irreversible action'}"
            )
        if level == RiskLevel.MEDIUM:
            return (
                f"Medium-risk action '{capability}': "
                f"{', '.join(factors) or 'may have side effects'}"
            )
        return f"Low-risk action '{capability}': safe to proceed"

    def record_action(self, capability: str, context: dict[str, Any]) -> None:
        """Record action for history tracking."""
        self._action_history.append(
            {
                "capability": capability,
                "context": context,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )
        if len(self._action_history) > 100:
            self._action_history = self._action_history[-100:]


_risk_detector: RiskDetector | None = None


def get_risk_detector() -> RiskDetector:
    """Get risk detector singleton."""
    global _risk_detector
    if _risk_detector is None:
        from aria.config import get_settings

        settings = get_settings()
        high_risk = set(settings.safety.risk_levels.high_risk_capabilities)
        medium_risk = set(settings.safety.risk_levels.medium_risk_capabilities)
        low_risk = set(settings.safety.risk_levels.low_risk_capabilities)
        _risk_detector = RiskDetector(
            high_risk=high_risk or None,
            medium_risk=medium_risk or None,
            low_risk=low_risk or None,
        )
    return _risk_detector
