"""Working memory implementation backed by Redis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol

from aria.adapters.redis import StateStore, get_state_store
from aria.utils.logging import get_logger

if TYPE_CHECKING:
    from typing import Any

logger = get_logger(__name__)


class LLMClient(Protocol):
    """Protocol for LLM client interface."""

    async def generate(self, prompt: str) -> str:
        """Generate text from prompt."""
        ...


@dataclass
class MemoryItem:
    """Single item in working memory."""

    content: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    source: str = "unknown"
    importance: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        """Convert MemoryItem to dictionary."""
        return {
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "importance": self.importance,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryItem:
        """Create MemoryItem from dictionary."""
        return cls(
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=data.get("source", "unknown"),
            importance=float(data.get("importance", 0.5)),
        )


class WorkingMemory:
    """Short-term memory for current task context."""

    def __init__(self, session_id: str, max_items: int = 100) -> None:
        """Initialize working memory for a session."""
        self.session_id = session_id
        self.max_items = max_items
        self._store = None

    async def _get_store(self) -> StateStore:
        """Get or initialize state store."""
        if self._store is None:
            self._store = await get_state_store()
        return self._store

    async def add(
        self,
        content: dict[str, Any],
        source: str = "unknown",
        importance: float = 0.5,
    ) -> None:
        """Add an item to working memory."""
        store = await self._get_store()
        item = MemoryItem(content=content, source=source, importance=importance)
        await store.push_to_memory(self.session_id, item.to_dict(), max_items=self.max_items)
        logger.debug("Working memory updated", session_id=self.session_id, source=source)

    async def get_recent(self, limit: int = 10) -> list[MemoryItem]:
        """Get most recent memory items."""
        store = await self._get_store()
        items = await store.get_memory(self.session_id, limit=limit)
        return [MemoryItem.from_dict(item) for item in items]

    async def get_by_source(self, source: str, limit: int = 5) -> list[MemoryItem]:
        """Get memory items from a specific source."""
        items = await self.get_recent(limit=self.max_items)
        return [item for item in items if item.source == source][:limit]

    async def get_context_window(self, max_tokens: int = 4000) -> str:
        """Get a formatted context window for LLM prompts."""
        items = await self.get_recent(limit=50)
        now = datetime.now(UTC)
        scored: list[tuple[float, MemoryItem]] = []

        for item in items:
            age_hours = (now - item.timestamp).total_seconds() / 3600
            recency_score = 1 / (1 + age_hours)
            score = item.importance * 0.7 + recency_score * 0.3
            scored.append((score, item))

        scored.sort(key=lambda pair: pair[0], reverse=True)

        context_parts: list[str] = []
        estimated_tokens = 0
        for _, item in scored:
            part = f"[{item.source}] {item.content}"
            part_tokens = max(1, len(part) // 4)
            if estimated_tokens + part_tokens > max_tokens:
                break
            context_parts.append(part)
            estimated_tokens += part_tokens

        return "\n".join(context_parts)

    async def summarize_and_archive(self, llm_client: LLMClient) -> str:
        """Summarize current context and prepare for archival.

        Called when task completes or context gets too large.
        """
        context = await self.get_context_window(max_tokens=8000)
        prompt = (
            "Summarize this task context concisely:\n"
            f"{context}\n"
            "Provide a brief summary (2-3 sentences) capturing:\n"
            "1. What was the goal\n"
            "2. Key actions taken\n"
            "3. Final outcome"
        )
        return await llm_client.generate(prompt)

    async def clear(self) -> None:
        """Clear working memory for the session."""
        store = await self._get_store()
        await store.clear_memory(self.session_id)
        logger.debug("Working memory cleared", session_id=self.session_id)
