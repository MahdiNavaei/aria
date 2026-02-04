"""Learning engine for ARIA."""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING

from aria.adapters.kafka import get_event_bus
from aria.adapters.kafka.topics import (
    EYE_PERCEPTION_TOPIC,
    HAND_EXECUTION_TOPIC,
    HUMAN_ACTION_TOPIC,
    SESSION_LIFECYCLE_TOPIC,
)
from aria.config import get_settings
from aria.utils.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aria.models.events import EventEnvelope, EventType

logger = get_logger(__name__)


class LearningEngine:
    """ARIA Learning Engine.

    Consumes events from Kafka and triggers learning processes:
    - Skill extraction from successful executions
    - Policy updates from human feedback
    - UIRef refinement from failures
    """

    def __init__(
        self,
        topics: list[str] | None = None,
        consumer_group: str | None = None,
    ) -> None:
        """Initialize learning engine."""
        self._settings = get_settings().learning
        self._handlers: dict[EventType, list[Callable[[EventEnvelope], Awaitable[None]]]] = {}
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._topics = topics or [
            HAND_EXECUTION_TOPIC,
            HUMAN_ACTION_TOPIC,
            EYE_PERCEPTION_TOPIC,
            SESSION_LIFECYCLE_TOPIC,
        ]
        self._consumer_group = consumer_group or self._settings.consumer_group

    def register_handler(
        self,
        event_type: EventType,
        handler: Callable[[EventEnvelope], Awaitable[None]],
    ) -> None:
        """Register a handler for an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def start(self) -> None:
        """Start consuming events."""
        if self._running:
            return

        if not self._settings.enabled:
            logger.info("Learning engine disabled in configuration")
            return

        self._running = True
        self._task = asyncio.create_task(self._consume_loop())
        logger.info("Learning engine started")

    async def stop(self) -> None:
        """Stop consuming events."""
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        logger.info("Learning engine stopped")

    async def _consume_loop(self) -> None:
        """Run the main consumption loop."""
        event_bus = await get_event_bus()

        try:
            await event_bus.subscribe(
                self._topics,
                handler=self._handle_event,
                group_id=self._consumer_group,
            )
        except asyncio.CancelledError:
            logger.debug("Learning engine consume loop cancelled")
            raise

    async def _handle_event(self, event: EventEnvelope) -> None:
        """Route event to registered handlers."""
        handlers = self._handlers.get(event.event_type, [])

        for handler in handlers:
            try:
                await handler(event)
            except Exception:
                logger.exception(
                    "Learning handler failed",
                    event_type=event.event_type.value,
                    handler=getattr(handler, "__name__", "handler"),
                )

    async def process_single_event(self, event: EventEnvelope) -> None:
        """Process a single event (for testing)."""
        await self._handle_event(event)


_learning_engine: LearningEngine | None = None


def get_learning_engine() -> LearningEngine:
    """Return singleton LearningEngine instance."""
    global _learning_engine  # noqa: PLW0603
    if _learning_engine is None:
        _learning_engine = LearningEngine()
    return _learning_engine
