"""PII Handler for ARIA Safety."""

from __future__ import annotations

import re
from enum import Enum
from typing import NamedTuple

from aria.utils.logging import get_logger

logger = get_logger(__name__)


class PIIType(str, Enum):
    """Types of PII we detect."""

    EMAIL = "email"
    PHONE = "phone"
    CREDIT_CARD = "credit_card"
    IBAN = "iban"
    NATIONAL_ID = "national_id"
    SSN = "ssn"
    PASSWORD = "password"
    API_KEY = "api_key"
    IP_ADDRESS = "ip_address"
    PERSIAN_NATIONAL_ID = "persian_national_id"
    PERSIAN_PHONE = "persian_phone"


class PIIMatch(NamedTuple):
    """A detected PII match."""

    pii_type: PIIType
    value: str
    start: int
    end: int
    confidence: float


class PIIHandler:
    """Detect and redact PII in text."""

    PATTERNS = {
        PIIType.EMAIL: (
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        ),
        PIIType.PHONE: (
            r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}"
            r"[-.\s]?[0-9]{4}\b"
        ),
        PIIType.CREDIT_CARD: (
            r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}"
            r"|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b"
        ),
        PIIType.IBAN: (
            r"\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}"
            r"(?:[A-Z0-9]?){0,16}\b"
        ),
        PIIType.SSN: r"\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b",
        PIIType.API_KEY: (
            r"\b(?:sk-|pk_|api[_-]?key[=:]\s*)[A-Za-z0-9_-]{20,}\b"
        ),
        PIIType.IP_ADDRESS: (
            r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
        ),
        PIIType.PERSIAN_NATIONAL_ID: r"\b[0-9]{10}\b",
        PIIType.PERSIAN_PHONE: r"\b(?:0|\+98)?9[0-9]{9}\b",
    }

    PASSWORD_KEYWORDS = {
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "رمز",
        "گذرواژه",
        "کلمه عبور",
    }

    def __init__(
        self,
        redact_char: str = "*",
        enabled_types: list[PIIType] | None = None,
    ) -> None:
        self.redact_char = redact_char
        self._enabled_types = (
            set(enabled_types) if enabled_types else set(self.PATTERNS)
        )
        self._compiled_patterns = {
            pii_type: re.compile(pattern, re.IGNORECASE)
            for pii_type, pattern in self.PATTERNS.items()
            if pii_type in self._enabled_types
        }

    def detect(self, text: str) -> list[PIIMatch]:
        """Detect all PII in text."""
        matches: list[PIIMatch] = []

        for pii_type, pattern in self._compiled_patterns.items():
            for match in pattern.finditer(text):
                confidence = 0.9 if pii_type != PIIType.PERSIAN_NATIONAL_ID else 0.7
                matches.append(
                    PIIMatch(
                        pii_type=pii_type,
                        value=match.group(),
                        start=match.start(),
                        end=match.end(),
                        confidence=confidence,
                    ),
                )

        matches.extend(self._detect_passwords(text))

        return sorted(matches, key=lambda item: item.start)

    def _detect_passwords(self, text: str) -> list[PIIMatch]:
        """Detect password fields in text."""
        matches: list[PIIMatch] = []
        text_lower = text.lower()

        for keyword in self.PASSWORD_KEYWORDS:
            idx = text_lower.find(keyword)
            while idx != -1:
                after = text[idx + len(keyword) : idx + len(keyword) + 100]
                value_match = re.search(
                    r"[=:]\s*[\"']?([^\"'\s,}\]]+)",
                    after,
                )
                if value_match:
                    start = idx + len(keyword) + value_match.start(1)
                    value = value_match.group(1)
                    matches.append(
                        PIIMatch(
                            pii_type=PIIType.PASSWORD,
                            value=value,
                            start=start,
                            end=start + len(value),
                            confidence=0.95,
                        ),
                    )
                idx = text_lower.find(keyword, idx + 1)

        return matches

    def redact(self, text: str, pii_types: list[PIIType] | None = None) -> str:
        """Redact PII from text."""
        matches = self.detect(text)

        if pii_types:
            matches = [match for match in matches if match.pii_type in pii_types]

        matches = sorted(matches, key=lambda item: item.start, reverse=True)

        result = text
        for match in matches:
            redacted = self._redact_value(match.value, match.pii_type)
            result = result[: match.start] + redacted + result[match.end :]

        return result

    def _redact_value(self, value: str, pii_type: PIIType) -> str:
        """Redact a single value based on type."""
        if pii_type == PIIType.EMAIL:
            parts = value.split("@")
            if len(parts) == 2:
                return f"{parts[0][0]}{self.redact_char * 5}@{parts[1]}"

        if pii_type == PIIType.CREDIT_CARD:
            return f"{self.redact_char * 12}{value[-4:]}"

        if pii_type in {PIIType.PHONE, PIIType.PERSIAN_PHONE}:
            return f"{self.redact_char * (len(value) - 4)}{value[-4:]}"

        if pii_type in {PIIType.PASSWORD, PIIType.API_KEY}:
            return f"[REDACTED_{pii_type.value.upper()}]"

        if len(value) > 2:
            return f"{value[0]}{self.redact_char * (len(value) - 2)}{value[-1]}"

        return self.redact_char * len(value)

    def mask_dict(
        self,
        data: dict,
        sensitive_keys: list[str] | None = None,
    ) -> dict:
        """Mask sensitive values in a dictionary."""
        sensitive_keys = set(sensitive_keys or [])
        sensitive_keys.update(
            {
                "password",
                "secret",
                "token",
                "api_key",
                "apikey",
                "credit_card",
                "ssn",
                "national_id",
            },
        )

        def mask_value(key: str, value):  # noqa: ANN001
            key_lower = key.lower()

            if any(item in key_lower for item in sensitive_keys):
                if isinstance(value, str):
                    return f"[REDACTED_{key.upper()}]"
                return "[REDACTED]"

            if isinstance(value, str):
                return self.redact(value)
            if isinstance(value, dict):
                return self.mask_dict(value, list(sensitive_keys))
            if isinstance(value, list):
                return [mask_value(key, item) for item in value]

            return value

        return {key: mask_value(key, value) for key, value in data.items()}


_pii_handler: PIIHandler | None = None


def get_pii_handler() -> PIIHandler:
    """Get PII handler singleton."""
    global _pii_handler
    if _pii_handler is None:
        from aria.config import get_settings

        settings = get_settings()
        enabled_types = []
        if settings.safety.pii.entities:
            for entity in settings.safety.pii.entities:
                try:
                    enabled_types.append(PIIType(entity.lower()))
                except ValueError:
                    logger.warning("Unknown PII entity", entity=entity)
        _pii_handler = PIIHandler(enabled_types=enabled_types or None)
    return _pii_handler


def redact_pii(text: str) -> str:
    """Convenience function to redact PII from text."""
    return get_pii_handler().redact(text)


def mask_sensitive_data(data: dict) -> dict:
    """Convenience function to mask sensitive data in dict."""
    return get_pii_handler().mask_dict(data)
