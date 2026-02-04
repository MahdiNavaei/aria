import pytest
from aiokafka.errors import KafkaError

from aria.adapters.kafka.event_bus import EventBus
from aria.adapters.kafka.topics import AGENT_ERROR_TOPIC, HAND_EXECUTION_TOPIC
from aria.models.events import EventEnvelope, EventType


class FakeProducer:
    def __init__(self, fail_first: bool = False) -> None:
        self.fail_first = fail_first
        self.calls: list[tuple[str, EventEnvelope, bytes | None]] = []
        self.attempts = 0

    async def send_and_wait(
        self,
        topic: str,
        event: EventEnvelope,
        key: bytes | None = None,
    ) -> None:
        self.attempts += 1
        if self.fail_first and self.attempts == 1:
            msg = "boom"
            raise KafkaError(msg)
        self.calls.append((topic, event, key))


@pytest.mark.asyncio
async def test_publish_to_topic_retries() -> None:
    bus = EventBus()
    producer = FakeProducer(fail_first=True)
    bus._producer = producer

    event = EventEnvelope(
        event_type=EventType.HAND_EXECUTION,
        session_id="sess-1",
        trace_id="trace-1",
        payload={"action": "click"},
    )

    await bus.publish_to_topic(HAND_EXECUTION_TOPIC, event, retries=2)

    assert producer.attempts == 2
    assert producer.calls[0][0] == HAND_EXECUTION_TOPIC


def test_get_topic_for_event() -> None:
    bus = EventBus()
    assert bus._get_topic_for_event(EventType.HAND_EXECUTION) == HAND_EXECUTION_TOPIC
    assert bus._get_topic_for_event(EventType.AGENT_ERROR) == AGENT_ERROR_TOPIC
