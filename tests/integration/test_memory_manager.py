import pytest

import aria.core.memory.working as working_module
from aria.core.memory.manager import MemoryManager
from aria.core.memory.working import WorkingMemory


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


class DummyEpisodic:
    def __init__(self) -> None:
        self.saved: list[dict] = []

    async def recall_for_goal(self, goal: str, domain: str | None = None):
        return [{"goal": goal, "domain": domain}]

    async def add_experience(self, experience: dict, metadata: dict | None = None):
        self.saved.append({"experience": experience, "metadata": metadata})
        return "memory-1"


class DummySemantic:
    async def find_skills(self, query: str, domain: str | None = None, limit: int = 5):
        return [{"skill_id": "demo.skill", "definition": {"steps": []}, "score": 0.9}]

    async def find_policies(self, context: str, limit: int = 3):
        return [{"policy_id": "policy.demo", "definition": {"rule": "stay safe"}, "score": 0.8}]

    async def search_knowledge(self, query: str, domain: str | None = None, limit: int = 5):
        return [{"topic": "demo", "content": "info"}]

    async def add_skill(self, skill_id: str, skill_def: dict, description: str) -> None:
        return None


@pytest.mark.asyncio
async def test_memory_manager_builds_context(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_store = FakeStateStore()

    async def fake_get_state_store():
        return fake_store

    monkeypatch.setattr(working_module, "get_state_store", fake_get_state_store)

    session_id = "memory-session"
    working = WorkingMemory(session_id, max_items=10)
    episodic = DummyEpisodic()
    semantic = DummySemantic()

    manager = MemoryManager(
        session_id,
        user_id="user-1",
        working=working,
        episodic=episodic,
        semantic=semantic,
        emit_events=False,
    )

    await manager.record_observation({"note": "hello"}, source="brain", importance=0.6)
    context = await manager.build_context(goal="apply", domain="job_apply")

    assert "hello" in context["working"]["recent"]
    assert context["episodic"][0]["goal"] == "apply"
    assert context["skills"][0]["skill_id"] == "demo.skill"
    assert context["policies"][0]["policy_id"] == "policy.demo"
    assert context["knowledge"][0]["topic"] == "demo"


@pytest.mark.asyncio
async def test_memory_manager_end_session(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_store = FakeStateStore()

    async def fake_get_state_store():
        return fake_store

    monkeypatch.setattr(working_module, "get_state_store", fake_get_state_store)

    session_id = "memory-session-2"
    working = WorkingMemory(session_id, max_items=10)
    episodic = DummyEpisodic()
    semantic = DummySemantic()

    manager = MemoryManager(
        session_id,
        user_id="user-1",
        working=working,
        episodic=episodic,
        semantic=semantic,
        emit_events=False,
    )

    await manager.start_session(goal="demo", domain="job_apply")
    await manager.end_session(outcome="success", actions=[{"step": 1}])

    assert episodic.saved
    assert episodic.saved[0]["metadata"]["domain"] == "job_apply"
    assert fake_store.items == []
