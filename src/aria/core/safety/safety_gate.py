"""Safety Gate for ARIA."""

from __future__ import annotations

from enum import Enum
from typing import Any, NamedTuple

from aria.config import get_settings
from aria.core.safety.captcha_handler import CaptchaDetection, get_captcha_handler
from aria.core.safety.domain_policy import DomainAction, DomainCheckResult, get_domain_policy
from aria.core.safety.pii_handler import get_pii_handler
from aria.core.safety.rate_limiter import RateLimitResult, get_rate_limiter
from aria.core.safety.risk_detector import RiskAction, RiskAssessment, get_risk_detector
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class SafetyDecision(str, Enum):
    """Final safety decision."""

    ALLOW = "allow"
    REQUIRE_HUMAN = "require_human"
    BLOCK = "block"
    RATE_LIMITED = "rate_limited"


class SafetyCheckResult(NamedTuple):
    """Result of complete safety check."""

    decision: SafetyDecision
    reason: str
    domain_check: DomainCheckResult | None
    risk_assessment: RiskAssessment | None
    rate_limit: RateLimitResult | None
    captcha_detection: CaptchaDetection | None
    hitl_request: dict | None


class SafetyGate:
    """Central safety gate for ARIA."""

    READ_ONLY_CAPABILITIES = {
        "web.extract",
        "web.screenshot",
        "web.get_text",
        "web.scroll",
        "web.wait",
    }

    def __init__(self) -> None:
        settings = get_settings()
        self.domain_policy = get_domain_policy()
        self.risk_detector = get_risk_detector()
        self.rate_limiter = get_rate_limiter()
        self.captcha_handler = get_captcha_handler()
        self.pii_handler = get_pii_handler()
        self._enabled = settings.safety.enabled

    async def pre_check(
        self,
        capability: str,
        parameters: dict[str, Any],
        context: dict[str, Any],
    ) -> SafetyCheckResult:
        """Perform all pre-execution safety checks."""
        if not self._enabled:
            return SafetyCheckResult(
                decision=SafetyDecision.ALLOW,
                reason="Safety checks disabled",
                domain_check=None,
                risk_assessment=None,
                rate_limit=None,
                captcha_detection=None,
                hitl_request=None,
            )

        user_id = context.get("user_id", "unknown")
        session_id = context.get("session_id", "unknown")
        url = context.get("url") or parameters.get("url")
        domain_context = context.get("domain", "job_apply")

        domain_check = None
        if url:
            domain_check = self.domain_policy.check(url, domain_context)

            if domain_check.action == DomainAction.REQUIRE_HUMAN:
                hitl_request = {
                    "request_id": f"domain_{session_id}",
                    "reason": "domain_requires_human",
                    "context": {
                        "url": url,
                        "domain": domain_check.domain,
                        "matched_rule": domain_check.matched_rule,
                    },
                    "timeout_seconds": 300,
                }
                return SafetyCheckResult(
                    decision=SafetyDecision.REQUIRE_HUMAN,
                    reason=domain_check.reason,
                    domain_check=domain_check,
                    risk_assessment=None,
                    rate_limit=None,
                    captcha_detection=None,
                    hitl_request=hitl_request,
                )

            if not domain_check.allowed:
                logger.warning(
                    "Domain blocked by policy",
                    url=url,
                    reason=domain_check.reason,
                )
                return SafetyCheckResult(
                    decision=SafetyDecision.BLOCK,
                    reason=domain_check.reason,
                    domain_check=domain_check,
                    risk_assessment=None,
                    rate_limit=None,
                    captcha_detection=None,
                    hitl_request=None,
                )

            if (
                domain_check.action == DomainAction.READ_ONLY
                and capability not in self.READ_ONLY_CAPABILITIES
            ):
                return SafetyCheckResult(
                    decision=SafetyDecision.BLOCK,
                    reason=(
                        f"Domain is read-only, capability '{capability}' not allowed"
                    ),
                    domain_check=domain_check,
                    risk_assessment=None,
                    rate_limit=None,
                    captcha_detection=None,
                    hitl_request=None,
                )

        risk_assessment = self.risk_detector.assess(
            capability,
            {
                "parameters": parameters,
                "url": url,
                "domain": domain_context,
                "user_preferences": context.get("user_preferences", {}),
                "has_observation": context.get("has_observation", False),
            },
        )

        rate_action = self._get_rate_action(capability)
        rate_limit = await self.rate_limiter.check(user_id, rate_action)

        if not rate_limit.allowed:
            logger.warning("Rate limit exceeded", user_id=user_id, action=rate_action)
            return SafetyCheckResult(
                decision=SafetyDecision.RATE_LIMITED,
                reason=(
                    f"Rate limit exceeded. Retry after {rate_limit.retry_after:.0f} seconds."
                ),
                domain_check=domain_check,
                risk_assessment=risk_assessment,
                rate_limit=rate_limit,
                captcha_detection=None,
                hitl_request=None,
            )

        captcha_detection = None
        if context.get("page_source") or context.get("elements"):
            captcha_detection = await self.captcha_handler.detect_captcha(
                page_source=context.get("page_source"),
                elements=context.get("elements"),
                screenshot_ref=context.get("screenshot_ref"),
            )

            if captcha_detection.detected:
                captcha_result = await self.captcha_handler.handle_captcha(
                    captcha_detection,
                    session_id,
                    context,
                )

                if captcha_result.get("action") == "require_human":
                    return SafetyCheckResult(
                        decision=SafetyDecision.REQUIRE_HUMAN,
                        reason=captcha_result.get("reason", "captcha detected"),
                        domain_check=domain_check,
                        risk_assessment=risk_assessment,
                        rate_limit=rate_limit,
                        captcha_detection=captcha_detection,
                        hitl_request=captcha_result.get("hitl_request"),
                    )

        if risk_assessment.action == RiskAction.BLOCK:
            return SafetyCheckResult(
                decision=SafetyDecision.BLOCK,
                reason=risk_assessment.reason,
                domain_check=domain_check,
                risk_assessment=risk_assessment,
                rate_limit=rate_limit,
                captcha_detection=captcha_detection,
                hitl_request=None,
            )

        if risk_assessment.action in {RiskAction.REQUIRE_HUMAN, RiskAction.CONFIRM}:
            hitl_request = {
                "request_id": f"risk_{session_id}_{capability}",
                "reason": "high_risk_action",
                "context": {
                    "capability": capability,
                    "parameters": self.pii_handler.mask_dict(parameters),
                    "risk_level": risk_assessment.level.value,
                    "risk_factors": risk_assessment.factors,
                },
                "timeout_seconds": 300,
            }

            return SafetyCheckResult(
                decision=SafetyDecision.REQUIRE_HUMAN,
                reason=risk_assessment.reason,
                domain_check=domain_check,
                risk_assessment=risk_assessment,
                rate_limit=rate_limit,
                captcha_detection=captcha_detection,
                hitl_request=hitl_request,
            )

        await self.rate_limiter.consume(user_id, rate_action)
        self.risk_detector.record_action(capability, context)

        return SafetyCheckResult(
            decision=SafetyDecision.ALLOW,
            reason="All safety checks passed",
            domain_check=domain_check,
            risk_assessment=risk_assessment,
            rate_limit=rate_limit,
            captcha_detection=captcha_detection,
            hitl_request=None,
        )

    async def post_check(
        self,
        capability: str,
        result: dict[str, Any],
        context: dict[str, Any],
    ) -> dict:
        """Perform post-execution safety checks."""
        warnings: list[dict[str, Any]] = []

        if isinstance(result, dict):
            if get_settings().safety.pii.detect:
                result_str = str(result)
                pii_matches = self.pii_handler.detect(result_str)
                if pii_matches:
                    warnings.append(
                        {
                            "type": "pii_detected",
                            "count": len(pii_matches),
                            "types": list(
                                {match.pii_type.value for match in pii_matches}
                            ),
                        },
                    )

        new_url = result.get("url") or result.get("current_url")
        expected_url = context.get("expected_url")

        if new_url and expected_url:
            if not new_url.startswith(expected_url.split("?")[0]):
                domain_check = self.domain_policy.check(
                    new_url,
                    context.get("domain", "job_apply"),
                )
                if not domain_check.allowed:
                    warnings.append(
                        {
                            "type": "unexpected_navigation_blocked",
                            "url": new_url,
                            "reason": domain_check.reason,
                        },
                    )

        if warnings:
            logger.warning(
                "Post-check warnings",
                capability=capability,
                warnings=warnings,
            )

        return {"warnings": warnings}

    def _get_rate_action(self, capability: str) -> str:
        if "submit" in capability.lower():
            return "submit"
        if "apply" in capability.lower():
            return "apply"
        if "login" in capability.lower():
            return "login"
        return "default"

    def disable(self) -> None:
        """Disable safety checks (for testing only)."""
        logger.warning("Safety checks DISABLED")
        self._enabled = False

    def enable(self) -> None:
        """Enable safety checks."""
        logger.info("Safety checks enabled")
        self._enabled = True


_safety_gate: SafetyGate | None = None


def get_safety_gate() -> SafetyGate:
    """Get safety gate singleton."""
    global _safety_gate
    if _safety_gate is None:
        _safety_gate = SafetyGate()
    return _safety_gate
