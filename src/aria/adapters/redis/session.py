"""Session management utilities for Redis state store."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from aria.adapters.redis.state_store import StateStore, get_state_store

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class SessionManager:
    """Manage session lifecycle in Redis."""

    def __init__(self, store: StateStore | None = None) -> None:
        """Initialize the session manager.

        Args:
            store: Optional StateStore instance, created lazily if not provided.

        """
        self._store = store

    async def _get_store(self) -> StateStore:
        if self._store is None:
            self._store = await get_state_store()
        return self._store

    async def create_session(
        self,
        session_id: str,
        initial_state: dict[str, Any] | None = None,
    ) -> None:
        """Create a new session with the given ID and initial state."""
        store = await self._get_store()
        state = {
            "status": "active",
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }
        if initial_state:
            state.update(initial_state)
        await store.set_session_state(session_id, state)

    async def update_session(self, session_id: str, updates: dict[str, Any]) -> None:
        """Update an existing session with the given state updates."""
        store = await self._get_store()
        state = await store.get_session_state(session_id) or {}
        state.update(updates)
        state["updated_at"] = datetime.now(UTC).isoformat()
        await store.set_session_state(session_id, state)

    async def end_session(self, session_id: str, reason: str | None = None) -> None:
        """Mark a session as ended with an optional reason."""
        store = await self._get_store()
        state = await store.get_session_state(session_id) or {}
        state.update(
            {
                "status": "ended",
                "ended_at": datetime.now(UTC).isoformat(),
                "reason": reason,
            },
        )
        await store.set_session_state(session_id, state)

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve session state by ID."""
        store = await self._get_store()
        return await store.get_session_state(session_id)

    @asynccontextmanager
    async def session_scope(
        self,
        session_id: str,
        initial_state: dict[str, Any] | None = None,
    ) -> AsyncIterator[SessionManager]:
        """Context manager that creates and ends a session automatically."""
        await self.create_session(session_id, initial_state=initial_state)
        try:
            yield self
        finally:
            await self.end_session(session_id)
