import structlog

from aria.utils.logging import LogContext, configure_logging, get_logger


def test_log_context_binds_and_unbinds() -> None:
    structlog.contextvars.clear_contextvars()

    with LogContext(session_id="sess-1", user_id="user-1"):
        ctx = structlog.contextvars.get_contextvars()
        assert ctx["session_id"] == "sess-1"
        assert ctx["user_id"] == "user-1"

    ctx = structlog.contextvars.get_contextvars()
    assert "session_id" not in ctx
    assert "user_id" not in ctx


def test_configure_logging_and_get_logger() -> None:
    configure_logging("development")
    logger = get_logger("aria.test")
    assert logger is not None
