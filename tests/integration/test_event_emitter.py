import asyncio
import time
from uuid import uuid4

import pytest
from aiokafka import AIOKafkaConsumer

from aria.adapters.kafka.topics import AGENT_COMMAND_TOPIC
from aria.config import get_settings
from aria.models.events import EventEnvelope, EventType
from aria.utils.events import event_context


@pytest.mark.asyncio
async def test_event_emitter_context(kafka_ready: bool) -> None:
    settings = get_settings().kafka
    consumer = AIOKafkaConsumer(
        AGENT_COMMAND_TOPIC,
        bootstrap_servers=settings.bootstrap_servers,
        group_id=f"test-emitter-{uuid4().hex}",
        auto_offset_reset="latest",
        value_deserializer=EventEnvelope.from_kafka_message,
    )
    await consumer.start()

    session_id = f"sess_{uuid4().hex}"
    trace_id = f"trace_{uuid4().hex}"

    try:
        async with event_context(session_id=session_id, trace_id=trace_id) as emitter:
            event_id = await emitter.emit(
                EventType.AGENT_COMMAND,
                {"command": "start", "goal": "test"},
            )
            async with emitter.child_context(event_id):
                child_id = await emitter.emit(
                    EventType.AGENT_COMMAND,
                    {"command": "pause"},
                )

        received = []
        deadline = time.monotonic() + 5
        while len(received) < 2 and time.monotonic() < deadline:
            timeout = max(0.1, deadline - time.monotonic())
            try:
                msg = await asyncio.wait_for(consumer.getone(), timeout=timeout)
            except TimeoutError:
                continue
            if msg.value.event_id in {event_id, child_id}:
                received.append(msg.value)

        assert len(received) == 2
        for event in received:
            assert event.session_id == session_id
            assert event.trace_id == trace_id

        parent_event = next(e for e in received if e.event_id == child_id)
        assert parent_event.parent_event_id == event_id
    finally:
        await consumer.stop()


@pytest.mark.asyncio
async def test_event_context_requires_init() -> None:
    with pytest.raises(RuntimeError):
        from aria.utils.events import EventEmitter  # noqa: PLC0415

        await EventEmitter.emit(EventType.AGENT_COMMAND, {"command": "pause"})
