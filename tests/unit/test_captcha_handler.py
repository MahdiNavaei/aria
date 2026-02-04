import pytest

from aria.core.safety.captcha_handler import CaptchaHandler, CaptchaPolicy, CaptchaType


@pytest.mark.asyncio
async def test_detect_captcha_html() -> None:
    handler = CaptchaHandler()
    detection = await handler.detect_captcha(page_source="<div class='g-recaptcha'></div>")
    assert detection.detected is True
    assert detection.captcha_type == CaptchaType.RECAPTCHA_V2


@pytest.mark.asyncio
async def test_detect_captcha_hcaptcha() -> None:
    handler = CaptchaHandler()
    detection = await handler.detect_captcha(page_source="<div class='h-captcha'></div>")
    assert detection.detected is True
    assert detection.captcha_type == CaptchaType.HCAPTCHA


@pytest.mark.asyncio
async def test_detect_captcha_funcaptcha() -> None:
    handler = CaptchaHandler()
    detection = await handler.detect_captcha(
        page_source="<script src='https://funcaptcha.com'></script>"
    )
    assert detection.detected is True
    assert detection.captcha_type == CaptchaType.FUNCAPTCHA


@pytest.mark.asyncio
async def test_detect_captcha_elements() -> None:
    handler = CaptchaHandler()
    elements = [
        {"attributes": {"class": "captcha-challenge", "id": "captcha-123"}}
    ]
    detection = await handler.detect_captcha(elements=elements)
    assert detection.detected is True
    assert detection.captcha_type == CaptchaType.UNKNOWN


@pytest.mark.asyncio
async def test_detect_captcha_not_found() -> None:
    handler = CaptchaHandler()
    detection = await handler.detect_captcha(page_source="<div>No captcha here</div>")
    assert detection.detected is False
    assert detection.captcha_type is None


@pytest.mark.asyncio
async def test_handle_captcha_requires_human(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_emit(*args, **kwargs):
        _ = args, kwargs
        return "evt"

    monkeypatch.setattr("aria.utils.events.EventEmitter.emit", fake_emit)

    handler = CaptchaHandler()
    detection = await handler.detect_captcha(page_source="<div class='h-captcha'></div>")
    result = await handler.handle_captcha(detection, session_id="sess-1")

    assert result["action"] == "require_human"
    assert "hitl_request" in result
    assert result["hitl_request"]["reason"] == "captcha"


@pytest.mark.asyncio
async def test_handle_captcha_skip_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = CaptchaHandler(default_policy=CaptchaPolicy.SKIP_PAGE)
    detection = await handler.detect_captcha(page_source="<div class='g-recaptcha'></div>")
    result = await handler.handle_captcha(detection, session_id="sess-1")

    assert result["action"] == "skip"
    assert "reason" in result


@pytest.mark.asyncio
async def test_handle_captcha_abort_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = CaptchaHandler(default_policy=CaptchaPolicy.ABORT_TASK)
    detection = await handler.detect_captcha(page_source="<div class='g-recaptcha'></div>")
    result = await handler.handle_captcha(detection, session_id="sess-1")

    assert result["action"] == "abort"
    assert "reason" in result


@pytest.mark.asyncio
async def test_handle_captcha_user_policy_override(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_emit(*args, **kwargs):
        _ = args, kwargs
        return "evt"

    monkeypatch.setattr("aria.utils.events.EventEmitter.emit", fake_emit)

    handler = CaptchaHandler(default_policy=CaptchaPolicy.REQUIRE_HUMAN)
    detection = await handler.detect_captcha(page_source="<div class='g-recaptcha'></div>")
    
    # User preference override
    context = {"user_preferences": {"captcha_policy": "skip_page"}}
    result = await handler.handle_captcha(detection, session_id="sess-1", context=context)

    assert result["action"] == "skip"
