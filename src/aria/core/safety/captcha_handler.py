"""Captcha Handler for ARIA Safety."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, NamedTuple

from aria.models.events import EventType
from aria.utils.events import EventEmitter
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class CaptchaType(str, Enum):
    """Types of captcha we can detect."""

    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    FUNCAPTCHA = "funcaptcha"
    IMAGE_CAPTCHA = "image_captcha"
    TEXT_CAPTCHA = "text_captcha"
    SLIDER_CAPTCHA = "slider_captcha"
    UNKNOWN = "unknown"


class CaptchaDetection(NamedTuple):
    """Result of captcha detection."""

    detected: bool
    captcha_type: CaptchaType | None
    confidence: float
    element_info: dict[str, Any] | None
    screenshot_ref: str | None


class CaptchaPolicy(str, Enum):
    """Policy for handling captchas."""

    REQUIRE_HUMAN = "require_human"
    SKIP_PAGE = "skip_page"
    ABORT_TASK = "abort_task"


class CaptchaHandler:
    """Handle captcha detection and human intervention."""

    DETECTION_PATTERNS = {
        CaptchaType.RECAPTCHA_V2: [
            "g-recaptcha",
            "recaptcha-anchor",
            "rc-anchor",
            "data-sitekey",
            "grecaptcha",
        ],
        CaptchaType.RECAPTCHA_V3: [
            "grecaptcha.execute",
            "recaptcha/api.js?render=",
        ],
        CaptchaType.HCAPTCHA: [
            "h-captcha",
            "hcaptcha.com",
            "data-hcaptcha-",
        ],
        CaptchaType.FUNCAPTCHA: [
            "funcaptcha",
            "arkoselabs.com",
            "fc-iframe",
        ],
        CaptchaType.SLIDER_CAPTCHA: [
            "slider-captcha",
            "slide-verify",
            "drag-verify",
        ],
    }

    def __init__(
        self,
        default_policy: CaptchaPolicy = CaptchaPolicy.REQUIRE_HUMAN,
    ) -> None:
        self.default_policy = default_policy
        self._detection_count = 0
        self._last_detection: datetime | None = None

    async def detect_captcha(
        self,
        page_source: str | None = None,
        screenshot_ref: str | None = None,
        elements: list[dict[str, Any]] | None = None,
    ) -> CaptchaDetection:
        """Detect if page contains a captcha."""
        detected = False
        captcha_type: CaptchaType | None = None
        confidence = 0.0
        element_info = None

        if page_source:
            for ctype, patterns in self.DETECTION_PATTERNS.items():
                for pattern in patterns:
                    if pattern.lower() in page_source.lower():
                        detected = True
                        captcha_type = ctype
                        confidence = 0.9
                        break
                if detected:
                    break

        if not detected and elements:
            for element in elements:
                attrs = element.get("attributes", {})
                class_name = attrs.get("class", "").lower()
                element_id = attrs.get("id", "").lower()

                captcha_indicators = [
                    "captcha",
                    "recaptcha",
                    "hcaptcha",
                    "challenge",
                    "cf-turnstile",
                    "arkose",
                ]

                if any(
                    indicator in class_name or indicator in element_id
                    for indicator in captcha_indicators
                ):
                    detected = True
                    captcha_type = CaptchaType.UNKNOWN
                    confidence = 0.8
                    element_info = element
                    break

        if detected:
            self._detection_count += 1
            self._last_detection = datetime.now(UTC)
            logger.warning(
                "Captcha detected",
                captcha_type=captcha_type,
                confidence=confidence,
                detection_count=self._detection_count,
            )

        return CaptchaDetection(
            detected=detected,
            captcha_type=captcha_type,
            confidence=confidence,
            element_info=element_info,
            screenshot_ref=screenshot_ref,
        )

    async def handle_captcha(
        self,
        detection: CaptchaDetection,
        session_id: str,
        context: dict[str, Any] | None = None,
    ) -> dict:
        """Handle detected captcha according to policy."""
        context = context or {}
        policy = self.default_policy

        user_policy = context.get("user_preferences", {}).get("captcha_policy")
        if user_policy:
            policy = CaptchaPolicy(user_policy)

        if policy == CaptchaPolicy.SKIP_PAGE:
            logger.info("Captcha policy: skip page", session_id=session_id)
            return {
                "action": "skip",
                "reason": "Captcha detected, skipping page per user policy",
            }

        if policy == CaptchaPolicy.ABORT_TASK:
            logger.info("Captcha policy: abort task", session_id=session_id)
            return {
                "action": "abort",
                "reason": "Captcha detected, aborting task per user policy",
            }

        hitl_request = {
            "request_id": f"captcha_{session_id}_{self._detection_count}",
            "reason": "captcha",
            "captcha_type": (
                detection.captcha_type.value if detection.captcha_type else "unknown"
            ),
            "context": {
                "screenshot_ref": detection.screenshot_ref,
                "element_info": detection.element_info,
                "page_url": context.get("page_url"),
                "instruction": self._get_instruction(detection.captcha_type),
            },
            "timeout_seconds": 300,
        }

        try:
            await EventEmitter.emit(
                EventType.HUMAN_ACTION_RECEIVED,
                {
                    "type": "captcha_request",
                    "session_id": session_id,
                    **hitl_request,
                },
            )
        except RuntimeError as exc:
            logger.debug("Event context not initialized", error=str(exc))

        logger.info(
            "Captcha HITL request created",
            session_id=session_id,
            captcha_type=detection.captcha_type,
        )

        return {
            "action": "require_human",
            "hitl_request": hitl_request,
            "reason": (
                f"Captcha detected ({detection.captcha_type}), human intervention required"
            ),
        }

    def _get_instruction(self, captcha_type: CaptchaType | None) -> str:
        """Get human-readable instruction for captcha type."""
        instructions = {
            CaptchaType.RECAPTCHA_V2: (
                "لطفاً چک‌باکس 'من ربات نیستم' را کلیک کنید و چالش را حل کنید."
            ),
            CaptchaType.HCAPTCHA: "لطفاً چالش hCaptcha را حل کنید.",
            CaptchaType.IMAGE_CAPTCHA: "لطفاً تصاویر صحیح را انتخاب کنید.",
            CaptchaType.TEXT_CAPTCHA: "لطفاً متن نمایش داده شده را تایپ کنید.",
            CaptchaType.SLIDER_CAPTCHA: "لطفاً اسلایدر را به سمت راست بکشید.",
        }
        return instructions.get(
            captcha_type,
            "لطفاً چالش امنیتی نمایش داده شده را حل کنید.",
        )


_captcha_handler: CaptchaHandler | None = None


def get_captcha_handler() -> CaptchaHandler:
    """Get captcha handler singleton."""
    global _captcha_handler
    if _captcha_handler is None:
        _captcha_handler = CaptchaHandler()
    return _captcha_handler
