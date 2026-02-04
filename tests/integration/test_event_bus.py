import asyncio
from contextlib import suppress

import pytest

from aria.adapters.kafka.event_bus import EventBus
from aria.models.events import EventEnvelope, EventType


@pytest.mark.asyncio
async def test_event_bus_connect(kafka_ready: bool) -> None:
    bus = EventBus()
    await bus.connect()
    assert bus._producer is not None
    await bus.disconnect()


@pytest.mark.asyncio
async def test_publish_and_consume(event_bus: EventBus, test_topic: str) -> None:
    received = asyncio.Queue()

    async def handler(event: EventEnvelope) -> None:
        await received.put(event)

    consumer_task = asyncio.create_task(
        event_bus.subscribe([test_topic], handler, group_id="test-group"),
    )

    event = EventEnvelope(
        event_type=EventType.AGENT_PLAN,
        session_id="test_session",
        trace_id="test_trace",
        payload={"step": "test"},
    )
    await event_bus.publish_to_topic(test_topic, event)

    received_event = await asyncio.wait_for(received.get(), timeout=10.0)
    assert received_event.event_id == event.event_id

    consumer_task.cancel()
    with suppress(asyncio.CancelledError):
        await consumer_task
