"""Event emission utilities for ARIA."""

from __future__ import annotations

import contextvars
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from aria.adapters.kafka import get_event_bus
from aria.models.events import EventEnvelope, EventType
from aria.utils.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = get_logger(__name__)

_session_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "session_id",
    default=None,
)
_trace_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "trace_id",
    default=None,
)
_parent_event_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "parent_event_id",
    default=None,
)
_step_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "step_id",
    default=None,
)
_model_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "model_id",
    default=None,
)


class EventEmitter:
    """Convenient event emission with automatic context."""

    @staticmethod
    def get_context() -> dict[str, str | None]:
        """Get current event context."""
        return {
            "session_id": _session_id.get(),
            "trace_id": _trace_id.get(),
            "parent_event_id": _parent_event_id.get(),
            "step_id": _step_id.get(),
            "model_id": _model_id.get(),
        }

    @staticmethod
    async def emit(
        event_type: EventType,
        payload: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Emit event with current context."""
        ctx = EventEmitter.get_context()
        if not ctx["session_id"] or not ctx["trace_id"]:
            msg = "Event context not initialized"
            raise RuntimeError(msg)

        event = EventEnvelope(
            event_type=event_type,
            session_id=ctx["session_id"],
            trace_id=ctx["trace_id"],
            parent_event_id=ctx["parent_event_id"],
            step_id=ctx["step_id"],
            model_id=ctx["model_id"],
            payload=payload,
            metadata=metadata or {},
        )

        event_bus = await get_event_bus()
        await event_bus.publish(event)

        logger.debug(
            "Event emitted",
            event_type=event_type.value,
            event_id=event.event_id,
        )
        return event.event_id

    @staticmethod
    @asynccontextmanager
    async def child_context(parent_event_id: str) -> AsyncIterator[None]:
        """Create child context for nested events."""
        token = _parent_event_id.set(parent_event_id)
        try:
            yield
        finally:
            _parent_event_id.reset(token)

    @staticmethod
    @asynccontextmanager
    async def step_context(step_id: str) -> AsyncIterator[None]:
        """Attach a step_id to emitted events."""
        token = _step_id.set(step_id)
        try:
            yield
        finally:
            _step_id.reset(token)

    @staticmethod
    @asynccontextmanager
    async def model_context(model_id: str) -> AsyncIterator[None]:
        """Attach a model_id to emitted events."""
        token = _model_id.set(model_id)
        try:
            yield
        finally:
            _model_id.reset(token)


@asynccontextmanager
async def event_context(
    session_id: str,
    trace_id: str | None = None,
) -> AsyncIterator[EventEmitter]:
    """Manage event emission context."""
    session_token = _session_id.set(session_id)
    trace_token = _trace_id.set(trace_id or str(uuid4()))

    try:
        yield EventEmitter()
    finally:
        _session_id.reset(session_token)
        _trace_id.reset(trace_token)


async def emit_brain_event(
    event_type: EventType,
    **payload: str | float | bool | dict[str, Any] | list[Any] | None,
) -> str:
    """Emit a brain event with the given payload."""
    return await EventEmitter.emit(event_type, dict(payload))


async def emit_hand_event(
    event_type: EventType,
    **payload: str | float | bool | dict[str, Any] | list[Any] | None,
) -> str:
    """Emit a hand event with the given payload."""
    return await EventEmitter.emit(event_type, dict(payload))


async def emit_human_event(
    event_type: EventType,
    **payload: str | float | bool | dict[str, Any] | list[Any] | None,
) -> str:
    """Emit a human event with the given payload."""
    return await EventEmitter.emit(event_type, dict(payload))
