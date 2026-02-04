"""Structured logging utilities for ARIA."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any, Self

import structlog
from opentelemetry import trace

if TYPE_CHECKING:
    from types import TracebackType


class LogContext:
    """Context manager for log enrichment.

    Args:
        session_id: Session identifier.
        user_id: User identifier.
        trace_id: Trace identifier override.

    """

    def __init__(
        self,
        session_id: str | None = None,
        user_id: str | None = None,
        trace_id: str | None = None,
    ) -> None:
        """Initialize the log context with optional identifiers."""
        self._values: dict[str, str] = {}
        if session_id:
            self._values["session_id"] = session_id
        if user_id:
            self._values["user_id"] = user_id
        if trace_id:
            self._values["trace_id"] = trace_id

    def __enter__(self) -> Self:
        """Enter the context and bind context variables."""
        structlog.contextvars.bind_contextvars(**self._values)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Exit the context and unbind context variables."""
        _ = exc_type, exc, tb
        if self._values:
            structlog.contextvars.unbind_contextvars(*self._values.keys())


def _add_trace_context(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    _ = logger, method_name
    if not event_dict.get("trace_id"):
        span = trace.get_current_span()
        span_context = span.get_span_context()
        if span_context and span_context.is_valid:
            event_dict["trace_id"] = format(span_context.trace_id, "032x")
            event_dict["span_id"] = format(span_context.span_id, "016x")
    return event_dict


def _redact_pii(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    _ = logger, method_name
    try:
        from aria.config import get_settings
        from aria.core.safety import get_pii_handler

        settings = get_settings()
        if not settings.safety.pii.detect or not settings.safety.pii.redact_in_logs:
            return event_dict

        pii_handler = get_pii_handler()
        return pii_handler.mask_dict(event_dict)
    except (ImportError, AttributeError, RuntimeError) as exc:
        # Only catch expected errors (module not loaded, missing attribute, circular import)
        logger.debug("PII redaction skipped", error=str(exc))
        return event_dict
    except Exception:  # noqa: BLE001
        # Log unexpected errors but don't break logging
        logger.warning("Unexpected error in PII redaction", error=str(exc), exc_info=True)
        return event_dict


def configure_logging(env: str) -> None:
    """Configure structlog and stdlib logging."""
    level_name = os.getenv("ARIA_LOG_LEVEL", "DEBUG" if env == "development" else "INFO")
    level = getattr(logging, level_name.upper(), logging.INFO)

    logging.basicConfig(level=level, format="%(message)s")

    processors = [
        structlog.contextvars.merge_contextvars,
        _add_trace_context,
        _redact_pii,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    add_logger_name = getattr(structlog.processors, "add_logger_name", None)
    if add_logger_name is not None:
        processors.insert(3, add_logger_name)

    if env == "production":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structured logger instance."""
    return structlog.get_logger(name)
