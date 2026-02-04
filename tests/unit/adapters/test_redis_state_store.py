import asyncio

import pytest
from redis.exceptions import RedisError

from aria.adapters.redis.state_store import StateStore


class FakeRedis:
    def __init__(self) -> None:
        self.calls = 0
        self.fail_first = False
        self.fail_with: Exception | None = None

    async def get(self, key: str) -> str:
        _ = key
        self.calls += 1
        if self.fail_with is not None:
            raise self.fail_with
        if self.fail_first and self.calls == 1:
            msg = "boom"
            raise RedisError(msg)
        return "value"


@pytest.mark.asyncio
async def test_execute_retries_on_redis_error(monkeypatch: pytest.MonkeyPatch) -> None:
    store = StateStore()
    fake = FakeRedis()
    fake.fail_first = True
    store._client = fake

    async def fake_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    result = await store._execute("get", "key")

    assert result == "value"
    assert fake.calls == 2


@pytest.mark.asyncio
async def test_execute_raises_on_unexpected_error() -> None:
    store = StateStore()
    fake = FakeRedis()
    fake.fail_with = RuntimeError("nope")
    store._client = fake

    with pytest.raises(RuntimeError):
        await store._execute("get", "key")

    assert fake.calls == 1


def test_prefix_and_ttl_resolution() -> None:
    store = StateStore()
    store._prefixes = {"session": "sess"}
    store._ttls = {"session_state": 11}

    assert store._prefix("session", "abc") == "sess:abc"
    assert store._ttl("session_state", 5) == 11
    assert store._ttl("missing", 7) == 7
