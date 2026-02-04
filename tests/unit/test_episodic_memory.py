import pytest

from aria.core.memory.episodic import EpisodicMemory


class FakeMem0:
    def __init__(self) -> None:
        self.add_calls: list[tuple] = []
        self.search_results: list[dict] = []
        self.update_calls: list[tuple] = []

    def add(self, messages, user_id: str, metadata: dict):
        self.add_calls.append((messages, user_id, metadata))
        return {"id": "mem-1"}

    def search(self, query: str, user_id: str, limit: int = 5):
        return list(self.search_results[:limit])

    def update(self, memory_id: str, data: dict):
        self.update_calls.append((memory_id, data))

    def get_all(self, user_id: str, limit: int = 100):
        return [{"id": "mem-1"}][:limit]


@pytest.mark.asyncio
async def test_add_experience_stores_payload() -> None:
    mem0 = FakeMem0()
    memory = EpisodicMemory(user_id="user-1", mem0_client=mem0)

    memory_id = await memory.add_experience({"goal": "test"}, metadata={"domain": "demo"})

    assert memory_id == "mem-1"
    assert mem0.add_calls
    assert mem0.add_calls[0][1] == "user-1"


@pytest.mark.asyncio
async def test_recall_similar_filters_results() -> None:
    mem0 = FakeMem0()
    mem0.search_results = [
        {"metadata": {"domain": "a"}, "score": 0.9},
        {"metadata": {"domain": "b"}, "score": 0.8},
    ]

    memory = EpisodicMemory(user_id="user-1", mem0_client=mem0)
    results = await memory.recall_similar("query", filters={"domain": "a"})

    assert len(results) == 1
    assert results[0]["metadata"]["domain"] == "a"


@pytest.mark.asyncio
async def test_update_and_get_all() -> None:
    mem0 = FakeMem0()
    memory = EpisodicMemory(user_id="user-1", mem0_client=mem0)

    await memory.update_experience("mem-1", {"outcome": "success"})
    assert mem0.update_calls == [("mem-1", {"outcome": "success"})]

    all_items = await memory.get_all(limit=5)
    assert all_items == [{"id": "mem-1"}]
