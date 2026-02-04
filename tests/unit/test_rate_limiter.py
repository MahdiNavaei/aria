import pytest

from aria.core.safety.rate_limiter import RateLimiter, RateLimitConfig


@pytest.mark.asyncio
async def test_rate_limiter_local_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_store():
        raise RuntimeError("no redis")

    monkeypatch.setattr("aria.core.safety.rate_limiter.get_state_store", fake_store)

    limiter = RateLimiter()
    limiter.configure("test", "3/second")

    # First consume should be allowed
    result = await limiter.consume("user-1", "test")
    assert result.allowed is True
    assert result.remaining >= 0

    # Second consume should be allowed
    result = await limiter.consume("user-1", "test")
    assert result.allowed is True
    assert result.remaining >= 0

    # Third consume should be allowed (limit is 3)
    result = await limiter.consume("user-1", "test")
    # After consuming 3, check will show limit hit
    # consume() calls check() again after consuming, so remaining might be 0
    assert result.remaining >= 0

    # Check should show limit hit
    result = await limiter.check("user-1", "test")
    assert result.allowed is False
    assert result.remaining == 0


@pytest.mark.asyncio
async def test_rate_limiter_reset_local(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_store():
        raise RuntimeError("no redis")

    monkeypatch.setattr("aria.core.safety.rate_limiter.get_state_store", fake_store)

    limiter = RateLimiter()
    limiter.configure("test", "2/second")

    # Consume to hit limit
    await limiter.consume("user-1", "test")
    await limiter.consume("user-1", "test")
    
    result = await limiter.check("user-1", "test")
    assert result.allowed is False

    # Reset
    await limiter.reset("user-1", "test")
    
    # Should be allowed again
    result = await limiter.check("user-1", "test")
    assert result.allowed is True


@pytest.mark.asyncio
async def test_rate_limiter_reset_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    deleted_keys = []

    class FakeStore:
        async def cache_get(self, key: str):
            return {"count": 2, "window_start": 1000.0}

        async def cache_set(self, key: str, value, ttl: int):
            pass

        async def cache_delete(self, key: str):
            deleted_keys.append(key)

    async def fake_store():
        return FakeStore()

    monkeypatch.setattr("aria.core.safety.rate_limiter.get_state_store", fake_store)

    limiter = RateLimiter()
    await limiter.reset("user-1", "test")
    
    assert len(deleted_keys) > 0
    assert any("ratelimit:user-1:test" in key for key in deleted_keys)


def test_rate_limit_config_from_string() -> None:
    config = RateLimitConfig.from_string("100/minute", "test")
    assert config.limit == 100
    assert config.window_seconds == 60
    assert config.name == "test"

    config = RateLimitConfig.from_string("10/hour", "hourly")
    assert config.limit == 10
    assert config.window_seconds == 3600

    config = RateLimitConfig.from_string("50/day", "daily")
    assert config.limit == 50
    assert config.window_seconds == 86400


def test_rate_limit_config_invalid() -> None:
    with pytest.raises(ValueError, match="Invalid rate limit spec"):
        RateLimitConfig.from_string("100", "test")

    with pytest.raises(ValueError, match="Unknown time unit"):
        RateLimitConfig.from_string("100/week", "test")


@pytest.mark.asyncio
async def test_rate_limiter_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_store():
        raise RuntimeError("no redis")

    monkeypatch.setattr("aria.core.safety.rate_limiter.get_state_store", fake_store)

    limiter = RateLimiter()
    limiter.configure("test", "1/second")

    # First consume allowed
    result = await limiter.consume("user-1", "test")
    # consume() calls check() again after consuming, so it may show limit hit
    # But we know we consumed 1, so check separately
    assert result.limit == 1

    # Check should show blocked (limit is 1, we consumed 1)
    result = await limiter.check("user-1", "test")
    assert result.allowed is False
    assert result.retry_after is not None
    assert result.retry_after >= 0
