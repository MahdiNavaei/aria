import pytest

import aria.core.memory.working as working_module
from aria.core.memory.working import MemoryItem, WorkingMemory


class FakeStateStore:
    def __init__(self) -> None:
        self.items: list[dict] = []

    async def push_to_memory(self, session_id: str, item: dict, max_items: int = 100) -> None:
        self.items.insert(0, item)
        self.items = self.items[:max_items]

    async def get_memory(self, session_id: str, limit: int = 10) -> list[dict]:
        return list(self.items[:limit])

    async def clear_memory(self, session_id: str) -> None:
        self.items = []


@pytest.mark.asyncio
async def test_working_memory_add_and_get(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_store = FakeStateStore()

    async def fake_get_state_store():
        return fake_store

    monkeypatch.setattr(working_module, "get_state_store", fake_get_state_store)

    memory = WorkingMemory("session-1", max_items=2)
    await memory.add({"message": "first"}, source="brain", importance=0.4)
    await memory.add({"message": "second"}, source="brain", importance=0.6)

    items = await memory.get_recent(limit=10)
    assert items[0].content["message"] == "second"
    assert items[1].content["message"] == "first"


def test_memory_item_roundtrip() -> None:
    item = MemoryItem(content={"foo": "bar"}, source="human", importance=0.7)
    payload = item.to_dict()
    restored = MemoryItem.from_dict(payload)

    assert restored.content == item.content
    assert restored.source == "human"
    assert restored.importance == 0.7
