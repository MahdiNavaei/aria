import pytest

from aria.adapters.redis.state_store import StateStore


@pytest.mark.asyncio
async def test_state_store_connect(state_store: StateStore) -> None:
    assert state_store is not None


@pytest.mark.asyncio
async def test_session_state(state_store: StateStore) -> None:
    await state_store.set_session_state("test_sess", {"status": "active"})
    state = await state_store.get_session_state("test_sess")
    assert state == {"status": "active"}


@pytest.mark.asyncio
async def test_working_memory(state_store: StateStore) -> None:
    await state_store.push_to_memory("test_sess", {"item": 1})
    await state_store.push_to_memory("test_sess", {"item": 2})
    memory = await state_store.get_memory("test_sess", limit=10)
    assert len(memory) >= 2
    assert memory[0]["item"] == 2


@pytest.mark.asyncio
async def test_distributed_lock(state_store: StateStore) -> None:
    acquired = await state_store.acquire_lock("test_lock", ttl=5)
    assert acquired is True

    acquired2 = await state_store.acquire_lock("test_lock", ttl=5)
    assert acquired2 is False

    await state_store.release_lock("test_lock")
