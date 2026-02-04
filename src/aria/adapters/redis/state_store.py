"""Redis state store for ARIA."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import redis.asyncio as redis
from redis.exceptions import RedisError

from aria.config import get_settings
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class StateStore:
    """Async Redis state store for ARIA."""

    def __init__(self) -> None:
        """Initialize the state store with Redis settings."""
        self.settings = get_settings().redis
        self._client: redis.Redis | None = None
        self._prefixes = self.settings.key_prefixes
        self._ttls = self.settings.ttl_defaults

    async def connect(self) -> None:
        """Initialize Redis connection."""
        if self._client is not None:
            return
        self._client = redis.Redis(
            host=self.settings.host,
            port=self.settings.port,
            db=self.settings.db,
            password=self.settings.password,
            decode_responses=True,
        )
        await self._client.ping()
        logger.info("StateStore connected", host=self.settings.host, port=self.settings.port)

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client is not None:
            await self._client.aclose()
        self._client = None

    async def _execute(
        self,
        method: str,
        *args: str | int | bytes,
        **kwargs: str | int | bool | None,
    ) -> Any:  # noqa: ANN401
        if self._client is None:
            await self.connect()
        if self._client is None:
            msg = "Redis client failed to initialize"
            raise RuntimeError(msg)
        retries = int(kwargs.pop("retries", 3) or 3)
        attempt = 0
        while True:
            try:
                func = getattr(self._client, method)
                return await func(*args, **kwargs)
            except RedisError as exc:
                attempt += 1
                logger.warning(
                    "Redis operation failed",
                    error=str(exc),
                    attempt=attempt,
                    method=method,
                )
                if attempt >= retries:
                    raise
                await asyncio.sleep(0.2 * attempt)
            except (OSError, TypeError) as exc:
                logger.exception(
                    "Unexpected error in Redis operation",
                    error=str(exc),
                    method=method,
                )
                raise

    def _prefix(self, prefix_key: str, suffix: str) -> str:
        prefix = self._prefixes.get(prefix_key, prefix_key)
        return f"{prefix}:{suffix}"

    def _ttl(self, ttl_key: str, default: int) -> int:
        return int(self._ttls.get(ttl_key, default))

    # Session State
    async def set_session_state(self, session_id: str, state: dict[str, Any]) -> None:
        """Store session state in Redis with TTL."""
        key = self._prefix("session", session_id)
        payload = json.dumps(state, ensure_ascii=False)
        await self._execute("setex", key, self._ttl("session_state", 86400), payload)

    async def get_session_state(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve session state from Redis."""
        key = self._prefix("session", session_id)
        data = await self._execute("get", key)
        return json.loads(data) if data else None

    # Working Memory
    async def push_to_memory(
        self,
        session_id: str,
        item: dict[str, Any],
        max_items: int = 100,
    ) -> None:
        """Push an item to the working memory list."""
        key = self._prefix("memory", session_id)
        payload = json.dumps(item, ensure_ascii=False)
        await self._execute("lpush", key, payload)
        await self._execute("ltrim", key, 0, max_items - 1)
        await self._execute("expire", key, self._ttl("working_memory", 14400))

    async def get_memory(self, session_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Retrieve recent items from working memory."""
        key = self._prefix("memory", session_id)
        items = await self._execute("lrange", key, 0, limit - 1)
        return [json.loads(item) for item in items]

    async def clear_memory(self, session_id: str) -> None:
        """Clear all items from the session's working memory."""
        key = self._prefix("memory", session_id)
        await self._execute("delete", key)

    # Cache
    async def cache_set(
        self,
        key: str,
        value: dict[str, Any] | list[Any] | str | float | bool | None,  # noqa: FBT001
        ttl: int | None = None,
    ) -> None:
        """Store a value in the cache with optional TTL."""
        cache_key = self._prefix("cache", key)
        payload = json.dumps(value, ensure_ascii=False)
        await self._execute("setex", cache_key, ttl or self._ttl("cache", 3600), payload)

    async def cache_get(self, key: str) -> dict[str, Any] | list[Any] | str | int | float | None:
        """Retrieve a value from the cache."""
        cache_key = self._prefix("cache", key)
        data = await self._execute("get", cache_key)
        return json.loads(data) if data else None

    async def cache_delete(self, key: str) -> None:
        """Delete a value from the cache."""
        cache_key = self._prefix("cache", key)
        await self._execute("delete", cache_key)

    # Flags
    async def set_flag(
        self,
        name: str,
        *,
        value: bool = True,
        ttl: int | None = None,
    ) -> None:
        """Set a boolean flag with optional TTL."""
        key = self._prefix("flag", name)
        await self._execute("setex", key, ttl or self._ttl("flag", 600), "1" if value else "0")

    async def get_flag(self, name: str) -> bool:
        """Retrieve a boolean flag value."""
        key = self._prefix("flag", name)
        value = await self._execute("get", key)
        return value == "1"

    # Locks
    async def acquire_lock(self, name: str, ttl: int = 30) -> bool:
        """Acquire a distributed lock with the given TTL."""
        key = self._prefix("lock", name)
        result = await self._execute("set", key, "1", nx=True, ex=ttl)
        return bool(result)

    async def release_lock(self, name: str) -> None:
        """Release a distributed lock."""
        key = self._prefix("lock", name)
        await self._execute("delete", key)


_state_store: StateStore | None = None
_state_store_lock = asyncio.Lock()


async def get_state_store() -> StateStore:
    """Return a singleton StateStore instance."""
    global _state_store  # noqa: PLW0603
    async with _state_store_lock:
        if _state_store is None:
            _state_store = StateStore()
            await _state_store.connect()
        return _state_store
