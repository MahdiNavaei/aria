"""Kafka consumer utilities for ARIA."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from aria.adapters.kafka.event_bus import EventBus, get_event_bus
from aria.adapters.kafka.topics import DLQ_TOPIC
from aria.models.events import EventEnvelope
from aria.utils.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

logger = get_logger(__name__)


class EventConsumer:
    """Consumer wrapper with error handling and DLQ support."""

    def __init__(
        self,
        topics: list[str],
        handler: Callable[[EventEnvelope], Awaitable[None]],
        group_id: str | None = None,
        max_retries: int = 3,
        dlq_topic: str = DLQ_TOPIC,
    ) -> None:
        """Initialize the event consumer.

        Args:
            topics: List of Kafka topics to consume.
            handler: Async callback to handle each event.
            group_id: Consumer group ID.
            max_retries: Maximum retry attempts before sending to DLQ.
            dlq_topic: Dead letter queue topic name.

        """
        self._topics = topics
        self._handler = handler
        self._group_id = group_id
        self._max_retries = max_retries
        self._dlq_topic = dlq_topic
        self._consumer: AIOKafkaConsumer | None = None
        self._running = False

    @property
    def running(self) -> bool:
        """Return whether the consumer is currently running."""
        return self._running

    async def start(self) -> None:
        """Start consuming messages."""
        if self._running:
            return

        kafka_settings = EventBus().settings

        self._consumer = AIOKafkaConsumer(
            *self._topics,
            bootstrap_servers=kafka_settings.bootstrap_servers,
            group_id=self._group_id or kafka_settings.consumer_group,
            auto_offset_reset=kafka_settings.auto_offset_reset,
            enable_auto_commit=True,
            value_deserializer=EventEnvelope.from_kafka_message,
        )
        await self._consumer.start()
        self._running = True
        logger.info("EventConsumer started", topics=self._topics)

    async def stop(self) -> None:
        """Stop consuming messages."""
        if self._consumer is not None:
            await self._consumer.stop()
        self._consumer = None
        self._running = False

    async def run(self) -> None:
        """Consume messages until stopped."""
        if self._consumer is None:
            await self.start()

        if self._consumer is None:
            msg = "Consumer failed to initialize"
            raise RuntimeError(msg)

        try:
            async for msg in self._consumer:
                await self._handle_message(msg.value)
        except KafkaError as exc:
            logger.exception("Consumer error", error=str(exc))
            raise
        finally:
            await self.stop()

    async def _handle_message(self, event: EventEnvelope) -> None:
        attempts = 0
        last_exc: BaseException | None = None
        while attempts < self._max_retries:
            try:
                await self._handler(event)
            except (RuntimeError, ValueError, TypeError, OSError) as exc:
                attempts += 1
                last_exc = exc
                logger.warning(
                    "Handler failed",
                    event_id=event.event_id,
                    event_type=event.event_type.value,
                    attempt=attempts,
                    error=str(exc),
                )
                await asyncio.sleep(0.2 * attempts)
            else:
                return
        if last_exc is not None:
            await self._send_to_dlq(event, last_exc)

    async def _send_to_dlq(self, event: EventEnvelope, exc: BaseException) -> None:
        try:
            bus = await get_event_bus()
            dlq_event = event.model_copy()
            dlq_event.metadata["dlq_reason"] = str(exc)
            await bus.publish_to_topic(self._dlq_topic, dlq_event)
            logger.info("Event sent to DLQ", event_id=event.event_id, topic=self._dlq_topic)
        except (OSError, KafkaError) as dlq_exc:
            logger.exception("Failed to send event to DLQ", error=str(dlq_exc))
