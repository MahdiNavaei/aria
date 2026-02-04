"""Kafka event bus implementation for ARIA."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError

from aria.adapters.kafka.topics import (
    AGENT_COMMAND_TOPIC,
    AGENT_ERROR_TOPIC,
    AGENT_PLAN_TOPIC,
    EYE_PERCEPTION_TOPIC,
    HAND_EXECUTION_TOPIC,
    HAND_OBSERVATION_TOPIC,
    HUMAN_ACTION_TOPIC,
    LEARNING_ARTIFACT_TOPIC,
    SESSION_LIFECYCLE_TOPIC,
)
from aria.config import get_settings
from aria.models.events import EventEnvelope, EventType
from aria.utils.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

logger = get_logger(__name__)


_EVENT_TYPE_TOPIC = {
    EventType.AGENT_COMMAND: AGENT_COMMAND_TOPIC,
    EventType.AGENT_PLAN: AGENT_PLAN_TOPIC,
    EventType.BRAIN_PLAN_CREATED: AGENT_PLAN_TOPIC,
    EventType.BRAIN_STEP_STARTED: AGENT_PLAN_TOPIC,
    EventType.BRAIN_STEP_COMPLETED: AGENT_PLAN_TOPIC,
    EventType.HAND_EXECUTION: HAND_EXECUTION_TOPIC,
    EventType.HAND_EXECUTION_STARTED: HAND_EXECUTION_TOPIC,
    EventType.HAND_EXECUTION_COMPLETED: HAND_EXECUTION_TOPIC,
    EventType.HAND_EXECUTION_FAILED: HAND_EXECUTION_TOPIC,
    EventType.HAND_OBSERVATION: HAND_OBSERVATION_TOPIC,
    EventType.EYE_PERCEPTION: EYE_PERCEPTION_TOPIC,
    EventType.EYE_PERCEPTION_COMPLETED: EYE_PERCEPTION_TOPIC,
    EventType.HUMAN_ACTION: HUMAN_ACTION_TOPIC,
    EventType.HUMAN_ACTION_RECEIVED: HUMAN_ACTION_TOPIC,
    EventType.HUMAN_CORRECTION_RECEIVED: HUMAN_ACTION_TOPIC,
    EventType.HUMAN_FEEDBACK_RECEIVED: HUMAN_ACTION_TOPIC,
    EventType.LEARNING_ARTIFACT: LEARNING_ARTIFACT_TOPIC,
    EventType.AGENT_ERROR: AGENT_ERROR_TOPIC,
    EventType.SESSION_STARTED: SESSION_LIFECYCLE_TOPIC,
    EventType.SESSION_ENDED: SESSION_LIFECYCLE_TOPIC,
}


class EventBus:
    """Async Kafka event bus for ARIA."""

    def __init__(self) -> None:
        """Initialize the event bus with Kafka settings."""
        self.settings = get_settings().kafka
        self._producer: AIOKafkaProducer | None = None
        self._consumers: dict[str, AIOKafkaConsumer] = {}

    async def connect(self) -> None:
        """Initialize Kafka producer."""
        if self._producer is not None:
            return
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.settings.bootstrap_servers,
            value_serializer=lambda v: v.to_kafka_message(),
        )
        await self._producer.start()
        logger.info("EventBus connected", servers=self.settings.bootstrap_servers)

    async def disconnect(self) -> None:
        """Close producer and all consumers."""
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None
        for consumer in self._consumers.values():
            await consumer.stop()
        self._consumers.clear()

    async def publish(self, event: EventEnvelope, retries: int = 3) -> None:
        """Publish event to Kafka with retries."""
        if self._producer is None:
            await self.connect()
        topic = self._get_topic_for_event(event.event_type)
        await self.publish_to_topic(topic, event, retries=retries)

    async def publish_to_topic(self, topic: str, event: EventEnvelope, retries: int = 3) -> None:
        """Publish event to a specific Kafka topic with retries."""
        if self._producer is None:
            await self.connect()
        key = event.trace_id.encode("utf-8")

        attempt = 0
        while attempt < retries:
            try:
                await self._producer.send_and_wait(topic, event, key=key)
            except KafkaError as exc:
                attempt += 1
                logger.warning(
                    "Publish failed",
                    event_type=event.event_type.value,
                    event_id=event.event_id,
                    topic=topic,
                    attempt=attempt,
                    error=str(exc),
                )
                if attempt >= retries:
                    raise
                await asyncio.sleep(0.5 * attempt)
            else:
                logger.debug(
                    "Event published",
                    event_type=event.event_type.value,
                    event_id=event.event_id,
                    topic=topic,
                )
                return

    def _get_topic_for_event(self, event_type: EventType) -> str:
        """Map event type to Kafka topic."""
        return _EVENT_TYPE_TOPIC.get(event_type, AGENT_ERROR_TOPIC)

    async def subscribe(
        self,
        topics: list[str],
        handler: Callable[[EventEnvelope], Awaitable[None]],
        group_id: str | None = None,
    ) -> None:
        """Subscribe to topics and invoke handler for each event."""
        consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self.settings.bootstrap_servers,
            group_id=group_id or self.settings.consumer_group,
            auto_offset_reset=self.settings.auto_offset_reset,
            enable_auto_commit=True,
            value_deserializer=EventEnvelope.from_kafka_message,
        )
        await consumer.start()

        consumer_key = ",".join(sorted(topics))
        self._consumers[consumer_key] = consumer

        try:
            async for msg in consumer:
                try:
                    await handler(msg.value)
                except Exception as exc:
                    event_id = getattr(msg.value, "event_id", None)
                    logger.exception(
                        "Handler error",
                        event_id=event_id,
                        error=str(exc),
                    )
        except Exception as exc:
            logger.exception("Consumer error", topics=topics, error=str(exc))
            raise
        finally:
            await consumer.stop()
            self._consumers.pop(consumer_key, None)


_event_bus: EventBus | None = None
_event_bus_lock = asyncio.Lock()


async def get_event_bus() -> EventBus:
    """Return a singleton EventBus instance."""
    global _event_bus  # noqa: PLW0603
    async with _event_bus_lock:
        if _event_bus is None:
            _event_bus = EventBus()
            await _event_bus.connect()
        return _event_bus
