"""Episodic memory implementation using Mem0."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from mem0 import Memory

from aria.config import get_settings
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class EpisodicMemory:
    """Store and recall past experiences with Mem0."""

    def __init__(self, user_id: str = "default", mem0_client: Memory | None = None) -> None:
        """Initialize episodic memory for a user."""
        self.user_id = user_id
        self._mem0: Memory | None = mem0_client

    def _build_mem0_config(self) -> dict[str, Any]:
        settings = get_settings().memory.mem0
        return {
            "vector_store": {
                "provider": settings.vector_store.provider,
                "config": settings.vector_store.config.model_dump(),
            },
            "embedder": settings.embedder.model_dump(exclude_none=True),
            "llm": settings.llm.model_dump(exclude_none=True),
        }

    def _get_mem0(self) -> Memory:
        if self._mem0 is None:
            config = self._build_mem0_config()
            try:
                self._mem0 = Memory.from_config(config)
                logger.info("Mem0 client initialized", user_id=self.user_id)
            except Exception:
                logger.exception("Failed to initialize Mem0")
                raise
        return self._mem0

    async def add_experience(
        self,
        experience: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store a new experience."""
        mem0 = self._get_mem0()
        payload = {
            **experience,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        result = mem0.add(
            [{"role": "user", "content": str(payload)}],
            user_id=self.user_id,
            metadata=metadata or {},
        )
        logger.debug("Experience stored", user_id=self.user_id)
        return result.get("id", "")

    async def recall_similar(
        self,
        query: str,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Recall experiences similar to a query."""
        mem0 = self._get_mem0()
        results = mem0.search(query, user_id=self.user_id, limit=limit)

        if filters:
            results = [
                item
                for item in results
                if all(item.get("metadata", {}).get(k) == v for k, v in filters.items())
            ]

        logger.debug("Experiences recalled", query=query[:50], count=len(results))
        return results

    async def recall_for_goal(self, goal: str, domain: str | None = None) -> list[dict[str, Any]]:
        """Recall relevant experiences for a goal."""
        filters = {"domain": domain} if domain else None
        return await self.recall_similar(f"Previous attempts at: {goal}", limit=5, filters=filters)

    async def get_success_patterns(self, domain: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get successful experiences for a domain."""
        return await self.recall_similar(
            f"Successful task completion in {domain}",
            limit=limit,
            filters={"outcome": "success", "domain": domain},
        )

    async def get_failure_patterns(self, domain: str, limit: int = 5) -> list[dict[str, Any]]:
        """Get failed experiences for a domain."""
        return await self.recall_similar(
            f"Failed attempts in {domain} and what went wrong",
            limit=limit,
            filters={"outcome": "failure", "domain": domain},
        )

    async def update_experience(self, memory_id: str, updates: dict[str, Any]) -> None:
        """Update an existing experience."""
        mem0 = self._get_mem0()
        mem0.update(memory_id, data=updates)

    async def get_all(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get all experiences for user."""
        mem0 = self._get_mem0()
        return mem0.get_all(user_id=self.user_id, limit=limit)
