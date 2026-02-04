import json
from pathlib import Path

import pytest

from aria.core.memory.semantic import SemanticMemory


class FakeMem0:
    def __init__(self) -> None:
        self.add_calls: list[tuple] = []
        self.search_results: list[dict] = []

    def add(self, messages, user_id: str, metadata: dict):
        self.add_calls.append((messages, user_id, metadata))

    def search(self, query: str, user_id: str, limit: int = 5):
        return list(self.search_results[:limit])


@pytest.mark.asyncio
async def test_add_and_get_skill(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ARIA_ENV", "test")
    mem0 = FakeMem0()
    memory = SemanticMemory(artifacts_dir=tmp_path, mem0_client=mem0)

    await memory.add_skill("demo.skill", {"steps": ["a", "b"]}, "demo skill")

    path = tmp_path / "skills" / "demo.skill.json"
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["steps"] == ["a", "b"]
    assert mem0.add_calls

    loaded = await memory.get_skill("demo.skill")
    assert loaded == {"steps": ["a", "b"]}


@pytest.mark.asyncio
async def test_find_skills_uses_mem0(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ARIA_ENV", "test")
    mem0 = FakeMem0()
    memory = SemanticMemory(artifacts_dir=tmp_path, mem0_client=mem0)

    await memory.add_skill("domain.skill", {"steps": ["x"]}, "desc")
    mem0.search_results = [
        {"metadata": {"type": "skill", "skill_id": "domain.skill"}, "score": 0.88},
    ]

    results = await memory.find_skills("query", domain="domain", limit=3)

    assert results
    assert results[0]["skill_id"] == "domain.skill"
    assert results[0]["definition"]["steps"] == ["x"]


@pytest.mark.asyncio
async def test_add_and_get_policy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ARIA_ENV", "test")
    mem0 = FakeMem0()
    memory = SemanticMemory(artifacts_dir=tmp_path, mem0_client=mem0)

    await memory.add_policy("policy.one", {"rule": "stay safe"}, "policy")
    loaded = await memory.get_policy("policy.one")

    assert loaded == {"rule": "stay safe"}
