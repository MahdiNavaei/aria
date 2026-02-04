"""Policy learning from human feedback."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from aria.config import get_settings
from aria.core.memory import SemanticMemory
from aria.utils.logging import get_logger

if TYPE_CHECKING:
    from aria.config.learning import LearningConfig
    from aria.models.events import EventEnvelope

logger = get_logger(__name__)


@dataclass
class Policy:
    """Decision policy definition."""

    policy_id: str
    name: str
    domain: str
    condition: str
    action: str
    confidence: float = 0.5
    source: str = "learned"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    applied_count: int = 0
    success_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert policy to dictionary."""
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "domain": self.domain,
            "condition": self.condition,
            "action": self.action,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "success_rate": self.success_count / max(1, self.applied_count),
        }


class PolicyLearner:
    """Learn decision policies from human feedback.

    Analyzes human corrections, approvals, and rejections
    to build decision rules.
    """

    def __init__(
        self,
        semantic_memory: SemanticMemory | None = None,
        settings: LearningConfig | None = None,
    ) -> None:
        """Initialize policy learner."""
        self._settings = settings or get_settings().learning
        self.semantic_memory = semantic_memory or SemanticMemory()

    async def on_human_feedback(self, event: EventEnvelope) -> None:
        """Handle human feedback events."""
        payload = event.payload or {}
        feedback_type = payload.get("type") or payload.get("feedback_type")

        response = payload.get("response") if isinstance(payload.get("response"), dict) else {}
        if not feedback_type and response:
            action = response.get("action")
            if action in {"correct", "correction"}:
                feedback_type = "correction"
            elif action in {"approve", "approved"}:
                feedback_type = "approval"
            elif action in {"reject", "rejection"}:
                feedback_type = "rejection"

        if feedback_type == "correction" and self._settings.policy_learning.from_corrections:
            await self._process_correction(event, payload, response)
        elif feedback_type == "approval" and self._settings.policy_learning.from_approvals:
            await self._process_approval(event, payload, response)
        elif feedback_type == "rejection" and self._settings.policy_learning.from_rejections:
            await self._process_rejection(event, payload, response)

    async def _process_correction(
        self,
        event: EventEnvelope,
        payload: dict[str, Any],
        response: dict[str, Any],
    ) -> None:
        """Process human correction to learn policy."""
        original_action = payload.get("original_action") or response.get("original_action")
        corrected_action = payload.get("corrected_action") or response.get("corrected_action")
        context = payload.get("context") or response.get("context") or {}

        if not original_action or not corrected_action:
            logger.debug("Correction missing actions", event_id=event.event_id)
            return

        confidence = self._settings.policy_learning.initial_confidence
        policy = Policy(
            policy_id=f"correction_{event.event_id[:8]}",
            name=f"Correction: {self._action_name(original_action)}",
            domain=context.get("domain", "general"),
            condition=self._extract_condition(context),
            action=f"Instead of {original_action}, do {corrected_action}",
            confidence=confidence,
            source="human_correction",
            created_at=datetime.now(UTC),
        )

        await self._save_policy(policy)

        logger.info(
            "Policy learned from correction",
            policy_id=policy.policy_id,
        )

    async def _process_approval(
        self,
        event: EventEnvelope,
        payload: dict[str, Any],
        response: dict[str, Any],
    ) -> None:
        """Process approval to reinforce existing policies."""
        action = payload.get("action") or response.get("action")
        context = payload.get("context") or response.get("context") or {}

        if not action:
            logger.debug("Approval missing action", event_id=event.event_id)
            return

        condition = self._extract_condition(context)
        policies = await self.semantic_memory.find_policies(condition)

        for policy in policies:
            definition = policy.get("definition") or policy
            if definition.get("action") == action:
                new_confidence = min(1.0, definition.get("confidence", 0.5) + 0.1)
                definition["confidence"] = new_confidence
                await self.semantic_memory.add_policy(
                    definition["policy_id"],
                    definition,
                    definition.get("name", ""),
                )
                logger.info(
                    "Policy reinforced",
                    policy_id=definition.get("policy_id"),
                    confidence=new_confidence,
                )

    async def _process_rejection(
        self,
        event: EventEnvelope,
        payload: dict[str, Any],
        response: dict[str, Any],
    ) -> None:
        """Process rejection to create negative policy."""
        rejected_action = payload.get("action") or response.get("action")
        reason = payload.get("reason") or response.get("reason", "")
        context = payload.get("context") or response.get("context") or {}

        if not rejected_action:
            logger.debug("Rejection missing action", event_id=event.event_id)
            return

        confidence = max(self._settings.policy_learning.initial_confidence, 0.8)
        policy = Policy(
            policy_id=f"rejection_{event.event_id[:8]}",
            name=f"Avoid: {self._action_name(rejected_action)}",
            domain=context.get("domain", "general"),
            condition=self._extract_condition(context),
            action=f"DO NOT: {rejected_action}. Reason: {reason}",
            confidence=confidence,
            source="human_rejection",
            created_at=datetime.now(UTC),
        )

        await self._save_policy(policy)

    def _extract_condition(self, context: dict[str, Any]) -> str:
        """Extract condition string from context."""
        parts: list[str] = []

        if context.get("page_type"):
            parts.append(f"page_type={context['page_type']}")
        if context.get("domain"):
            parts.append(f"domain={context['domain']}")
        if context.get("step_type"):
            parts.append(f"step={context['step_type']}")

        return " AND ".join(parts) if parts else "general"

    async def _save_policy(self, policy: Policy) -> None:
        """Save policy to semantic memory."""
        await self.semantic_memory.add_policy(
            policy.policy_id,
            policy.to_dict(),
            f"{policy.name}: {policy.condition} -> {policy.action}",
        )

    @staticmethod
    def _action_name(action: dict[str, Any] | str | None) -> str:
        """Return a readable name for an action payload."""
        if isinstance(action, dict):
            return action.get("type") or action.get("capability") or "unknown"
        return str(action) if action else "unknown"
