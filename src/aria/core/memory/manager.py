"""Unified memory manager for ARIA."""

from __future__ import annotations

from typing import Any

from aria.config import get_settings
from aria.core.memory.episodic import EpisodicMemory
from aria.core.memory.semantic import SemanticMemory
from aria.core.memory.working import WorkingMemory
from aria.models.events import EventType
from aria.utils.events import EventEmitter
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class MemoryManager:
    """Unified interface for working, episodic, and semantic memory tiers."""

    def __init__(  # noqa: PLR0913
        self,
        session_id: str,
        user_id: str = "default",
        *,
        working: WorkingMemory | None = None,
        episodic: EpisodicMemory | None = None,
        semantic: SemanticMemory | None = None,
        emit_events: bool = True,
    ) -> None:
        """Initialize memory manager with all tiers."""
        self.session_id = session_id
        self.user_id = user_id
        self._emit_events = emit_events

        settings = get_settings().memory
        working_config = settings.tiers.working

        self.working = working or WorkingMemory(session_id, max_items=working_config.max_items)
        self.episodic = episodic or EpisodicMemory(user_id)
        self.semantic = semantic or SemanticMemory()

    async def build_context(self, goal: str, domain: str, max_tokens: int = 4000) -> dict[str, Any]:
        """Build a combined context for planning."""
        context = {
            "working": {},
            "episodic": [],
            "skills": [],
            "policies": [],
            "knowledge": [],
        }

        context["working"]["recent"] = await self.working.get_context_window(
            max_tokens=max_tokens // 4,
        )
        context["episodic"] = await self.episodic.recall_for_goal(goal, domain)
        context["skills"] = await self.semantic.find_skills(goal, domain, limit=3)
        context["policies"] = await self.semantic.find_policies(f"{domain}: {goal}", limit=3)
        context["knowledge"] = await self.semantic.search_knowledge(goal, domain=domain, limit=3)

        logger.debug(
            "Context built",
            working_len=len(context["working"]["recent"]),
            episodic_count=len(context["episodic"]),
            skills_count=len(context["skills"]),
        )

        return context

    async def record_observation(
        self,
        content: dict[str, Any],
        source: str,
        importance: float = 0.5,
    ) -> None:
        """Record an observation in working memory."""
        await self.working.add(content, source=source, importance=importance)

    async def record_action(
        self,
        action: dict[str, Any],
        result: dict[str, Any],
        *,
        success: bool,
    ) -> None:
        """Record an action outcome in working memory."""
        await self.working.add(
            {"action": action, "result": result, "success": success},
            source="hand",
            importance=0.8 if not success else 0.6,
        )

    async def record_human_input(self, input_type: str, content: dict[str, Any]) -> None:
        """Record human input in working memory."""
        await self.working.add(
            {"type": input_type, **content},
            source="human",
            importance=0.9,
        )

    async def save_experience(
        self,
        goal: str,
        actions: list[dict[str, Any]],
        outcome: str,
        domain: str,
    ) -> str:
        """Persist a completed task as an episodic memory."""
        summary = await self.working.get_context_window(max_tokens=2000)
        experience = {
            "goal": goal,
            "actions": actions,
            "outcome": outcome,
            "context_summary": summary,
        }

        memory_id = await self.episodic.add_experience(
            experience,
            metadata={"domain": domain, "outcome": outcome},
        )

        if self._emit_events:
            try:
                await EventEmitter.emit(
                    EventType.LEARNING_ARTIFACT,
                    {"memory_id": memory_id, "outcome": outcome, "domain": domain},
                )
            except RuntimeError as exc:
                logger.debug("Event context not initialized", error=str(exc))

        return memory_id

    async def get_skill_for_action(
        self,
        action: str,
        context: str,
        domain: str,
    ) -> dict[str, Any] | None:
        """Find the best skill for a given action."""
        skills = await self.semantic.find_skills(f"{action} in {context}", domain=domain, limit=1)
        return skills[0] if skills else None

    async def learn_skill(self, skill_id: str, skill_def: dict[str, Any], description: str) -> None:
        """Store a learned skill."""
        await self.semantic.add_skill(skill_id, skill_def, description)

    async def start_session(self, goal: str, domain: str) -> dict[str, Any]:
        """Initialize memory for a new session and preload context."""
        await self.working.add(
            {"goal": goal, "domain": domain, "status": "started"},
            source="brain",
            importance=1.0,
        )
        return await self.build_context(goal, domain)

    async def end_session(self, outcome: str, actions: list[dict[str, Any]]) -> None:
        """Archive session memory and clear working memory."""
        recent = await self.working.get_recent(limit=1)
        goal = recent[0].content.get("goal", "Unknown") if recent else "Unknown"
        domain = recent[0].content.get("domain", "unknown") if recent else "unknown"

        await self.save_experience(goal, actions, outcome, domain)
        await self.working.clear()

        logger.info("Session ended", session_id=self.session_id, outcome=outcome)


def create_memory_manager(session_id: str, user_id: str = "default") -> MemoryManager:
    """Create a MemoryManager instance."""
    return MemoryManager(session_id, user_id)
