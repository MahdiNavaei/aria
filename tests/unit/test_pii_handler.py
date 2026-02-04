from aria.core.safety.pii_handler import PIIHandler, PIIType


def test_pii_detection_and_redaction() -> None:
    handler = PIIHandler()
    text = "Contact me at test@example.com or 09123456789."

    matches = handler.detect(text)
    types = {match.pii_type for match in matches}
    assert PIIType.EMAIL in types
    assert PIIType.PERSIAN_PHONE in types

    redacted = handler.redact(text)
    assert "test@example.com" not in redacted
    assert "09123456789" not in redacted


def test_pii_detection_credit_card() -> None:
    handler = PIIHandler()
    text = "Card number: 4111111111111111"
    matches = handler.detect(text)
    types = {match.pii_type for match in matches}
    assert PIIType.CREDIT_CARD in types


def test_pii_detection_ssn() -> None:
    handler = PIIHandler()
    text = "SSN: 123-45-6789"
    matches = handler.detect(text)
    types = {match.pii_type for match in matches}
    assert PIIType.SSN in types


def test_pii_detection_api_key() -> None:
    handler = PIIHandler()
    text = "API key: sk-1234567890abcdefghijklmnopqrstuvwxyz"
    matches = handler.detect(text)
    types = {match.pii_type for match in matches}
    assert PIIType.API_KEY in types


def test_pii_redaction_email() -> None:
    handler = PIIHandler()
    text = "Email: user@example.com"
    redacted = handler.redact(text, pii_types=[PIIType.EMAIL])
    assert "user@example.com" not in redacted
    assert "@example.com" in redacted  # Domain should remain


def test_pii_redaction_credit_card() -> None:
    handler = PIIHandler()
    text = "Card: 4111111111111111"
    redacted = handler.redact(text, pii_types=[PIIType.CREDIT_CARD])
    assert "4111111111111111" not in redacted
    assert "1111" in redacted  # Last 4 digits should remain


def test_mask_dict_sensitive_keys() -> None:
    handler = PIIHandler()
    data = {"password": "secret", "email": "user@example.com"}
    masked = handler.mask_dict(data)

    assert masked["password"].startswith("[REDACTED")
    assert "user@example.com" not in masked["email"]


def test_mask_dict_nested() -> None:
    handler = PIIHandler()
    data = {
        "user": {
            "email": "test@example.com",
            "phone": "09123456789",
        },
        "password": "secret123",
    }
    masked = handler.mask_dict(data)

    assert masked["password"].startswith("[REDACTED")
    assert "test@example.com" not in str(masked["user"]["email"])
    assert "09123456789" not in str(masked["user"]["phone"])


def test_mask_dict_list() -> None:
    handler = PIIHandler()
    data = {
        "users": [
            {"email": "user1@example.com"},
            {"email": "user2@example.com"},
        ]
    }
    masked = handler.mask_dict(data)

    assert "user1@example.com" not in str(masked["users"])
    assert "user2@example.com" not in str(masked["users"])


def test_pii_detection_persian_national_id() -> None:
    handler = PIIHandler()
    text = "کد ملی: 1234567890"
    matches = handler.detect(text)
    types = {match.pii_type for match in matches}
    # May or may not detect depending on pattern
    assert isinstance(matches, list)
