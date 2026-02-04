import pytest

import aria.utils.events as events_module
from aria.models.events import EventType
from aria.utils.events import EventEmitter, event_context


class FakeEventBus:
    def __init__(self) -> None:
        self.published = []

    async def publish(self, event) -> None:
        self.published.append(event)


@pytest.mark.asyncio
async def test_event_context_and_emit(monkeypatch: pytest.MonkeyPatch) -> None:
    bus = FakeEventBus()

    async def fake_get_event_bus():
        return bus

    monkeypatch.setattr(events_module, "get_event_bus", fake_get_event_bus)

    async with event_context("sess-1", trace_id="trace-1"):
        event_id = await EventEmitter.emit(EventType.HAND_EXECUTION, {"action": "run"})

    assert bus.published
    assert bus.published[0].event_type == EventType.HAND_EXECUTION
    assert bus.published[0].session_id == "sess-1"
    assert bus.published[0].trace_id == "trace-1"
    assert bus.published[0].event_id == event_id


@pytest.mark.asyncio
async def test_event_context_resets_context() -> None:
    async with event_context("sess-2"):
        ctx = EventEmitter.get_context()
        assert ctx["session_id"] == "sess-2"
        assert ctx["trace_id"]

    ctx = EventEmitter.get_context()
    assert ctx["session_id"] is None
    assert ctx["trace_id"] is None
