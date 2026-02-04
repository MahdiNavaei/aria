"""Rate Limiter for ARIA Safety."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, NamedTuple

from aria.adapters.redis import get_state_store
from aria.config import get_settings
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class RateLimitResult(NamedTuple):
    """Result of rate limit check."""

    allowed: bool
    limit: int
    remaining: int
    reset_at: datetime
    retry_after: float | None


class RateLimitConfig:
    """Configuration for a rate limit."""

    def __init__(self, limit: int, window_seconds: int, name: str = "default") -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.name = name

    @classmethod
    def from_string(cls, spec: str, name: str = "default") -> "RateLimitConfig":
        """Parse rate limit from string like "100/minute"."""
        parts = spec.lower().split("/")
        if len(parts) != 2:
            msg = f"Invalid rate limit spec: {spec}"
            raise ValueError(msg)

        limit = int(parts[0])
        unit = parts[1].strip()

        unit_seconds = {
            "second": 1,
            "seconds": 1,
            "minute": 60,
            "minutes": 60,
            "hour": 3600,
            "hours": 3600,
            "day": 86400,
            "days": 86400,
        }

        if unit not in unit_seconds:
            msg = f"Unknown time unit: {unit}"
            raise ValueError(msg)

        return cls(limit=limit, window_seconds=unit_seconds[unit], name=name)


class RateLimiter:
    """Distributed rate limiter using Redis with local fallback."""

    DEFAULT_LIMITS = {
        "default": RateLimitConfig.from_string("100/minute", "default"),
        "submit": RateLimitConfig.from_string("10/hour", "submit"),
        "apply": RateLimitConfig.from_string("50/day", "apply"),
        "api_call": RateLimitConfig.from_string("1000/hour", "api_call"),
        "login": RateLimitConfig.from_string("5/minute", "login"),
    }

    def __init__(self) -> None:
        settings = get_settings()
        self._enabled = settings.safety.rate_limit_enabled
        self._strict_mode = settings.safety.strict_mode
        self._custom_limits: dict[str, RateLimitConfig] = {}
        self._local_hits: dict[str, list[float]] = {}

    def configure(self, action: str, limit_spec: str) -> None:
        """Configure custom limit for an action."""
        self._custom_limits[action] = RateLimitConfig.from_string(limit_spec, action)

    async def check(self, user_id: str, action: str = "default") -> RateLimitResult:
        """Check if action is allowed under rate limit."""
        config = self._get_config(action)
        reset_at = datetime.now(UTC) + timedelta(seconds=config.window_seconds)

        if not self._enabled:
            return RateLimitResult(
                allowed=True,
                limit=config.limit,
                remaining=config.limit,
                reset_at=reset_at,
                retry_after=None,
            )

        key = self._make_key(user_id, action)

        store = await self._get_store()
        if store is None:
            return self._check_local(key, config)

        count, window_start = await self._get_count(store, key, config.window_seconds)
        remaining = max(0, config.limit - count)
        reset_at = window_start + timedelta(seconds=config.window_seconds)

        if count >= config.limit:
            retry_after = max(0.0, (reset_at - datetime.now(UTC)).total_seconds())
            logger.warning(
                "Rate limit exceeded",
                user_id=user_id,
                action=action,
                limit=config.limit,
                window=config.window_seconds,
            )
            return RateLimitResult(
                allowed=False,
                limit=config.limit,
                remaining=0,
                reset_at=reset_at,
                retry_after=retry_after,
            )

        return RateLimitResult(
            allowed=True,
            limit=config.limit,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=None,
        )

    async def consume(
        self,
        user_id: str,
        action: str = "default",
        cost: int = 1,
    ) -> RateLimitResult:
        """Consume rate limit quota."""
        result = await self.check(user_id, action)
        if not result.allowed:
            return result

        config = self._get_config(action)
        key = self._make_key(user_id, action)

        store = await self._get_store()
        if store is None:
            self._consume_local(key, cost, config.window_seconds)
            return await self.check(user_id, action)

        count, window_start = await self._get_count(store, key, config.window_seconds)
        count += cost
        payload = {
            "count": count,
            "window_start": window_start.timestamp(),
        }
        await store.cache_set(key, payload, ttl=config.window_seconds)
        return await self.check(user_id, action)

    async def reset(self, user_id: str, action: str = "default") -> None:
        """Reset rate limit for user/action (admin function)."""
        key = self._make_key(user_id, action)
        
        # Reset in Redis if available
        store = await self._get_store()
        if store is not None:
            try:
                await store.cache_delete(key)
                logger.info("Rate limit reset in Redis", user_id=user_id, action=action, key=key)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to reset rate limit in Redis", error=str(exc), key=key)
        
        # Reset local cache
        if key in self._local_hits:
            del self._local_hits[key]
            logger.info("Rate limit reset in local cache", user_id=user_id, action=action)
        
        logger.info("Rate limit reset completed", user_id=user_id, action=action)

    def _get_config(self, action: str) -> RateLimitConfig:
        if action in self._custom_limits:
            return self._custom_limits[action]
        return self.DEFAULT_LIMITS.get(action, self.DEFAULT_LIMITS["default"])

    def _make_key(self, user_id: str, action: str) -> str:
        return f"ratelimit:{user_id}:{action}"

    async def _get_store(self) -> Any | None:  # noqa: ANN401
        try:
            return await get_state_store()
        except Exception as exc:  # pragma: no cover - defensive  # noqa: BLE001
            logger.warning("Rate limiter store unavailable", error=str(exc))
            if self._strict_mode:
                raise
            return None

    async def _get_count(
        self,
        store: Any,  # noqa: ANN401
        key: str,
        window_seconds: int,
    ) -> tuple[int, datetime]:
        payload = await store.cache_get(key)
        now = datetime.now(UTC)

        if isinstance(payload, dict):
            count = int(payload.get("count", 0))
            window_start_ts = float(payload.get("window_start", now.timestamp()))
        else:
            count = int(payload) if payload else 0
            window_start_ts = now.timestamp()

        window_start = datetime.fromtimestamp(window_start_ts, UTC)
        if (now - window_start).total_seconds() >= window_seconds:
            return 0, now

        return count, window_start

    def _check_local(self, key: str, config: RateLimitConfig) -> RateLimitResult:
        now = datetime.now(UTC)
        hits = self._local_hits.get(key, [])
        hits = [
            t
            for t in hits
            if (now - datetime.fromtimestamp(t, UTC)).total_seconds()
            < config.window_seconds
        ]
        self._local_hits[key] = hits

        remaining = max(0, config.limit - len(hits))
        reset_at = now + timedelta(seconds=config.window_seconds)

        if len(hits) >= config.limit:
            oldest = min(hits) if hits else now.timestamp()
            retry_after = max(
                0.0,
                (
                    datetime.fromtimestamp(oldest, UTC)
                    + timedelta(seconds=config.window_seconds)
                    - now
                ).total_seconds(),
            )
            return RateLimitResult(
                allowed=False,
                limit=config.limit,
                remaining=0,
                reset_at=reset_at,
                retry_after=retry_after,
            )

        return RateLimitResult(
            allowed=True,
            limit=config.limit,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=None,
        )

    def _consume_local(self, key: str, cost: int, window_seconds: int) -> None:
        now = datetime.now(UTC)
        hits = self._local_hits.get(key, [])
        hits = [
            t
            for t in hits
            if (now - datetime.fromtimestamp(t, UTC)).total_seconds() < window_seconds
        ]
        hits.extend([now.timestamp()] * cost)
        self._local_hits[key] = hits


_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter singleton."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()

        settings = get_settings()
        for action, spec in settings.safety.rate_limits.items():
            _rate_limiter.configure(action, spec)

    return _rate_limiter
