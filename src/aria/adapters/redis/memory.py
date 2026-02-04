"""Working memory utilities for Redis."""

from __future__ import annotations

from typing import Any

from aria.adapters.redis.state_store import StateStore, get_state_store


class WorkingMemoryStore:
    """Working memory operations on top of Redis lists."""

    def __init__(self, store: StateStore | None = None) -> None:
        """Initialize the working memory store.

        Args:
            store: Optional StateStore instance, created lazily if not provided.

        """
        self._store = store

    async def _get_store(self) -> StateStore:
        if self._store is None:
            self._store = await get_state_store()
        return self._store

    async def append(
        self,
        session_id: str,
        item: dict[str, Any],
        max_items: int = 100,
    ) -> None:
        """Append an item to the working memory list."""
        store = await self._get_store()
        await store.push_to_memory(session_id, item, max_items=max_items)

    async def recent(self, session_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Retrieve the most recent items from working memory."""
        store = await self._get_store()
        return await store.get_memory(session_id, limit=limit)

    async def search(
        self,
        session_id: str,
        field: str,
        value: str | float | bool | None,  # noqa: FBT001
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Search working memory for items matching a field value."""
        items = await self.recent(session_id, limit=limit)
        return [item for item in items if item.get(field) == value]

    async def clear(self, session_id: str) -> None:
        """Clear all items from the session's working memory."""
        store = await self._get_store()
        await store.clear_memory(session_id)
