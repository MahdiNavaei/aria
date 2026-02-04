"""ARIA Safety Module.

Provides defense-in-depth safety for the ARIA agent:
- Domain Policy: URL access control
- Risk Detector: Action risk assessment
- Captcha Handler: Human-required challenges
- Rate Limiter: Abuse prevention
- PII Handler: Sensitive data protection
- Safety Gate: Central integration point
"""

from aria.core.safety.captcha_handler import (
    CaptchaHandler,
    CaptchaPolicy,
    CaptchaType,
    get_captcha_handler,
)
from aria.core.safety.domain_policy import (
    DomainAction,
    DomainCheckResult,
    DomainPolicy,
    get_domain_policy,
)
from aria.core.safety.pii_handler import (
    PIIHandler,
    PIIMatch,
    PIIType,
    get_pii_handler,
    mask_sensitive_data,
    redact_pii,
)
from aria.core.safety.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    RateLimitResult,
    get_rate_limiter,
)
from aria.core.safety.risk_detector import (
    RiskAction,
    RiskAssessment,
    RiskDetector,
    RiskLevel,
    get_risk_detector,
)
from aria.core.safety.safety_gate import (
    SafetyCheckResult,
    SafetyDecision,
    SafetyGate,
    get_safety_gate,
)

__all__ = [
    "CaptchaHandler",
    "CaptchaPolicy",
    "CaptchaType",
    "DomainAction",
    "DomainCheckResult",
    "DomainPolicy",
    "PIIHandler",
    "PIIMatch",
    "PIIType",
    "RateLimiter",
    "RateLimitConfig",
    "RateLimitResult",
    "RiskAction",
    "RiskAssessment",
    "RiskDetector",
    "RiskLevel",
    "SafetyCheckResult",
    "SafetyDecision",
    "SafetyGate",
    "get_captcha_handler",
    "get_domain_policy",
    "get_pii_handler",
    "get_rate_limiter",
    "get_risk_detector",
    "get_safety_gate",
    "mask_sensitive_data",
    "redact_pii",
]
