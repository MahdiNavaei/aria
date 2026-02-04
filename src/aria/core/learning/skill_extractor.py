"""Skill extraction from execution traces."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from aria.config import get_settings
from aria.core.llm import LLMClient, Message, ModelRole, get_llm_client
from aria.core.memory import SemanticMemory
from aria.models.events import EventEnvelope, EventType
from aria.utils.logging import get_logger

if TYPE_CHECKING:
    from aria.config.learning import LearningConfig

logger = get_logger(__name__)


@dataclass
class Skill:
    """Learned skill definition."""

    skill_id: str
    name: str
    description: str
    domain: str
    trigger: str
    steps: list[dict[str, Any]]
    parameters: list[str] = field(default_factory=list)
    success_rate: float = 1.0
    use_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert skill to dictionary."""
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "domain": self.domain,
            "trigger": self.trigger,
            "steps": self.steps,
            "parameters": self.parameters,
            "success_rate": self.success_rate,
            "use_count": self.use_count,
        }


class SkillExtractor:
    """Extract reusable skills from successful execution traces.

    Analyzes sequences of actions that led to success and
    generalizes them into reusable skills.
    """

    def __init__(
        self,
        semantic_memory: SemanticMemory | None = None,
        llm_client: LLMClient | None = None,
        settings: LearningConfig | None = None,
    ) -> None:
        """Initialize skill extractor."""
        self._settings = settings or get_settings().learning
        if semantic_memory is None:
            artifacts_dir = Path(self._settings.artifacts_dir)
            semantic_memory = SemanticMemory(artifacts_dir=artifacts_dir)
        self.semantic_memory = semantic_memory
        self.llm = llm_client or get_llm_client()
        self._pending_traces: dict[str, list[EventEnvelope]] = {}
        self._session_meta: dict[str, dict[str, Any]] = {}

    async def on_execution_event(self, event: EventEnvelope) -> None:
        """Handle execution events."""
        session_id = event.session_id
        trace = self._pending_traces.setdefault(session_id, [])
        trace.append(event)

        meta = self._session_meta.setdefault(
            session_id,
            {
                "step_count": None,
                "completed_steps": 0,
                "has_failure": False,
                "goal": None,
                "domain": None,
            },
        )

        if event.event_type == EventType.BRAIN_PLAN_CREATED:
            meta["goal"] = event.payload.get("goal") or meta.get("goal")
            meta["domain"] = event.payload.get("domain") or meta.get("domain")
            if "step_count" in event.payload:
                meta["step_count"] = event.payload.get("step_count")

        if event.event_type == EventType.BRAIN_STEP_COMPLETED:
            meta["completed_steps"] = meta.get("completed_steps", 0) + 1
            if not event.payload.get("success", True):
                meta["has_failure"] = True

        if event.event_type == EventType.HAND_EXECUTION_FAILED:
            meta["has_failure"] = True

        if self._should_finalize(event, meta):
            await self._extract_from_trace(session_id)

    def _should_finalize(self, event: EventEnvelope, meta: dict[str, Any]) -> bool:
        """Return True if the trace should be finalized for extraction."""
        if event.event_type == EventType.SESSION_ENDED:
            success = event.payload.get("success")
            status = event.payload.get("status")
            return success is True or status in {"completed", "success"}

        if event.event_type == EventType.BRAIN_STEP_COMPLETED:
            final_status = event.payload.get("final_status")
            task_status = event.payload.get("task_status")
            if final_status in {"completed", "success"}:
                return True
            if task_status in {"completed", "success"}:
                return True

            step_count = meta.get("step_count")
            completed_steps = meta.get("completed_steps", 0)
            if step_count and completed_steps >= step_count:
                return True

        return False

    async def _extract_from_trace(self, session_id: str) -> None:
        """Extract skill from completed trace."""
        events = self._pending_traces.pop(session_id, [])
        meta = self._session_meta.pop(session_id, {})

        if not events:
            return

        if self._settings.skill_extraction.success_required and meta.get("has_failure"):
            logger.debug("Trace had failures, skipping skill extraction", session_id=session_id)
            return

        trace_summary = self._build_trace_summary(events, meta)
        if trace_summary["total_steps"] < self._settings.skill_extraction.min_steps:
            logger.debug(
                "Trace too short for skill extraction",
                session_id=session_id,
                steps=trace_summary["total_steps"],
            )
            return

        skill_def = await self._analyze_trace(trace_summary)
        if skill_def:
            await self._save_skill(skill_def)

    def _build_trace_summary(
        self,
        events: list[EventEnvelope],
        meta: dict[str, Any],
    ) -> dict[str, Any]:
        """Build summary of execution trace."""
        goal = meta.get("goal")
        domain = meta.get("domain") or "general"
        actions: list[dict[str, Any]] = []
        action_index: dict[str, int] = {}

        for event in events:
            goal, domain = self._process_event(
                event, actions, action_index, goal, domain,
            )

        actions = [a for a in actions if a.get("capability")]
        return {"goal": goal, "domain": domain, "actions": actions, "total_steps": len(actions)}

    def _process_event(
        self,
        event: EventEnvelope,
        actions: list[dict[str, Any]],
        action_index: dict[str, int],
        goal: str | None,
        domain: str,
    ) -> tuple[str | None, str]:
        """Process a single event and update actions list."""
        payload = event.payload or {}

        if event.event_type == EventType.BRAIN_PLAN_CREATED:
            goal = payload.get("goal") or goal
            domain = payload.get("domain") or domain

        self._process_hand_event(event, actions, action_index)
        self._process_step_event(event, actions, action_index)

        return goal, domain

    def _process_hand_event(
        self,
        event: EventEnvelope,
        actions: list[dict[str, Any]],
        action_index: dict[str, int],
    ) -> None:
        """Process HAND_EXECUTION_* events."""
        hand_events = {
            EventType.HAND_EXECUTION_STARTED,
            EventType.HAND_EXECUTION_COMPLETED,
            EventType.HAND_EXECUTION_FAILED,
        }
        if event.event_type not in hand_events:
            return

        payload = event.payload or {}
        nested = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
        capability = payload.get("capability") or nested.get("capability")
        if not capability:
            return

        step_id = payload.get("step_id") or event.step_id or nested.get("step_id")
        key = step_id or f"action_{len(actions)}"
        action = self._ensure_action(key, capability, actions, action_index)
        action["capability"] = capability

        if event.event_type == EventType.HAND_EXECUTION_STARTED:
            action["parameters"] = nested.get("parameters") or payload.get("parameters") or {}
        else:
            success = nested.get("success")
            if success is None and event.event_type == EventType.HAND_EXECUTION_FAILED:
                success = False
            if success is not None:
                action["success"] = bool(success)
            if nested.get("result"):
                action["result"] = nested.get("result")

    def _process_step_event(
        self,
        event: EventEnvelope,
        actions: list[dict[str, Any]],
        action_index: dict[str, int],
    ) -> None:
        """Process BRAIN_STEP_COMPLETED events."""
        if event.event_type != EventType.BRAIN_STEP_COMPLETED:
            return

        payload = event.payload or {}
        nested = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
        step_id = payload.get("step_id") or event.step_id or nested.get("step_id")

        if not step_id or step_id not in action_index:
            return
        action = actions[action_index[step_id]]
        if "success" in payload:
            action["success"] = bool(payload.get("success"))
        if payload.get("result"):
            action["result"] = payload.get("result")

    @staticmethod
    def _ensure_action(
        key: str,
        capability: str | None,
        actions: list[dict[str, Any]],
        action_index: dict[str, int],
    ) -> dict[str, Any]:
        """Ensure an action exists for the given key."""
        if key not in action_index:
            action_index[key] = len(actions)
            actions.append({
                "capability": capability,
                "parameters": {},
                "success": None,
                "result": {},
            })
        return actions[action_index[key]]

    async def _analyze_trace(self, trace: dict[str, Any]) -> dict[str, Any] | None:
        """Use LLM to analyze trace and extract a skill definition."""
        generalize_hint = ""
        if self._settings.skill_extraction.auto_generalize:
            generalize_hint = (
                "Generalize variable parameters (like text inputs) into templates."
            )

        prompt = (
            "Analyze this execution trace and extract a reusable skill.\n\n"
            f"Goal: {trace.get('goal')}\n"
            f"Domain: {trace.get('domain')}\n"
            f"Actions: {json.dumps(trace.get('actions', []), indent=2)}\n\n"
            f"{generalize_hint}\n"
            "If this is a repeatable pattern that could be reused, output a skill definition:"
            "\n{\n"
            '  "skill_id": "domain.action_name",\n'
            '  "name": "Human readable name",\n'
            '  "description": "What this skill does",\n'
            '  "trigger": "When to use this skill",\n'
            '  "steps": [\n'
            '    {"capability": "...", "parameters_template": {}}\n'
            "  ],\n"
            '  "parameters": ["param1", "param2"]\n'
            "}\n\n"
            'If this is too specific or not reusable, output: {"skip": true, "reason": '
            '"..."}'
        )

        response = await self.llm.generate(
            [Message(role="user", content=prompt)],
            role=ModelRole.BRAIN,
            temperature=0.3,
            max_tokens=1200,
        )

        result = self._parse_llm_response(response.content)
        if result is None:
            return None

        if result.get("skip"):
            logger.debug("Trace not suitable for skill", reason=result.get("reason"))
            return None

        return result

    def _parse_llm_response(self, raw: str) -> dict[str, Any] | None:
        """Parse JSON from LLM response content."""
        json_start = raw.find("{")
        json_end = raw.rfind("}") + 1
        if json_start < 0 or json_end <= json_start:
            logger.warning("Skill extraction failed: no JSON found in response")
            return None
        try:
            return json.loads(raw[json_start:json_end])
        except json.JSONDecodeError as exc:
            logger.warning("Skill extraction failed to parse", error=str(exc))
            return None

    async def _save_skill(self, skill_def: dict[str, Any]) -> None:
        """Save extracted skill."""
        skill = Skill(
            skill_id=skill_def.get("skill_id", "skill.unknown"),
            name=skill_def.get("name", "Unnamed skill"),
            description=skill_def.get("description", ""),
            domain=skill_def.get("domain", "general"),
            trigger=skill_def.get("trigger", ""),
            steps=skill_def.get("steps", []),
            parameters=skill_def.get("parameters", []),
        )

        await self.semantic_memory.add_skill(
            skill.skill_id,
            skill.to_dict(),
            skill.description,
        )

        logger.info(
            "Skill extracted and saved",
            skill_id=skill.skill_id,
            steps=len(skill.steps),
        )
