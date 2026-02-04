"""Planner node for ARIA Brain."""

from __future__ import annotations

import json
from uuid import uuid4

from aria.core.brain.state import AgentState, Plan, Step, StepStatus, TaskStatus
from aria.core.llm import Message, ModelRole, get_llm_client
from aria.core.memory import MemoryManager
from aria.core.safety import DomainAction, get_domain_policy
from aria.models.events import EventType
from aria.utils.events import EventEmitter
from aria.utils.logging import get_logger

logger = get_logger(__name__)

PLANNER_SYSTEM_PROMPT = """You are the planning component of ARIA, an AI assistant.
Your job is to decompose user goals into executable steps.

Available capabilities by domain:

JOB_APPLY domain:
- web.navigate(url): Open a URL
- web.click(selector): Click an element
- web.fill(selector, value): Fill a form field
- web.extract(selector): Extract text from element
- web.screenshot(): Take screenshot
- ml.match_job(job_data, profile): Check job match
- ml.generate_cover_letter(job_data, profile): Generate cover letter

CURSOR domain:
- cursor.open_file(path): Open file in editor
- cursor.edit(path, changes): Make code changes
- cursor.run_command(cmd): Run terminal command
- cursor.chat(message): Send message to Cursor AI

DESKTOP domain:
- desktop.click(x, y): Click at coordinates
- desktop.type(text): Type text
- desktop.hotkey(*keys): Press key combination
- desktop.screenshot(): Take screenshot

Guidelines:
1. Break down the goal into atomic, executable steps
2. Each step should use exactly one capability
3. Include observation steps (screenshots) when needed
4. Plan for potential failures (e.g., login required)
5. Keep steps independent where possible

Output format (JSON):
{
  "steps": [
    {
      "step_id": "step_1",
      "action": "Human-readable description",
      "capability": "web.navigate",
      "parameters": {"url": "https://example.com"}
    }
  ]
}
"""


class PlannerNode:
    """Create execution plans from goals."""

    def __init__(self) -> None:
        """Initialize planner node."""
        self.llm = get_llm_client()

    async def __call__(self, state: AgentState) -> dict:
        """Plan execution steps for the goal."""
        logger.info("Planning started", goal=state["goal"], domain=state["domain"])

        memory = MemoryManager(state["session_id"], state["user_id"], emit_events=False)
        context = await memory.build_context(
            state["goal"],
            state["domain"],
            max_tokens=4000,
        )

        user_prompt = self._build_prompt(state, context)
        messages = [
            Message(role="system", content=PLANNER_SYSTEM_PROMPT),
            Message(role="user", content=user_prompt),
        ]

        response = await self.llm.generate(
            messages,
            role=ModelRole.BRAIN,
            temperature=0.3,
            max_tokens=2000,
        )

        plan = self._parse_plan(response.content, state["goal"])
        self._apply_domain_policy(plan, state["domain"])

        try:
            await EventEmitter.emit(
                EventType.BRAIN_PLAN_CREATED,
                {
                    "plan_id": plan.plan_id,
                    "goal": state["goal"],
                    "step_count": len(plan.steps),
                },
            )
        except RuntimeError as exc:
            logger.debug("Event context not initialized", error=str(exc))

        logger.info("Plan created", plan_id=plan.plan_id, steps=len(plan.steps))

        return {
            "plan": plan,
            "task_status": TaskStatus.EXECUTING,
            "memory_context": context,
        }

    def _build_prompt(self, state: AgentState, context: dict) -> str:
        """Build planning prompt with context."""
        parts = [
            f"Goal: {state['goal']}",
            f"Domain: {state['domain']}",
            "",
        ]

        if context.get("episodic"):
            parts.append("Relevant past experiences:")
            parts.extend(
                f"- {exp.get('memory', '')}" for exp in context["episodic"][:3]
            )
            parts.append("")

        if context.get("skills"):
            parts.append("Available learned skills:")
            for skill in context["skills"]:
                description = skill.get("definition", {}).get("description", "")
                parts.append(f"- {skill['skill_id']}: {description}")
            parts.append("")

        if context.get("policies"):
            parts.append("Applicable policies:")
            parts.extend(f"- {policy['policy_id']}" for policy in context["policies"])
            parts.append("")

        parts.append("Create a step-by-step plan to achieve this goal.")
        return "\n".join(parts)

    def _parse_plan(self, response: str, goal: str) -> Plan:
        """Parse LLM response into a Plan object."""
        def _raise_no_json() -> None:
            msg = "No JSON found in response"
            raise ValueError(msg)

        def _raise_no_steps() -> None:
            msg = "No steps generated"
            raise ValueError(msg)

        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
            else:
                _raise_no_json()

            steps: list[Step] = []
            for idx, step_data in enumerate(data.get("steps", [])):
                steps.append(
                    Step(
                        step_id=step_data.get("step_id", f"step_{idx + 1}"),
                        action=step_data.get("action", "Unknown action"),
                        capability=step_data.get("capability", "unknown"),
                        parameters=step_data.get("parameters", {}),
                        status=StepStatus.PENDING,
                    ),
                )

            if not steps:
                _raise_no_steps()

            return Plan(plan_id=str(uuid4()), goal=goal, steps=steps)

        except (ValueError, json.JSONDecodeError, KeyError):
            logger.exception("Failed to parse plan")
            return Plan(
                plan_id=str(uuid4()),
                goal=goal,
                steps=[
                    Step(
                        step_id="step_1",
                        action="Execute goal directly",
                        capability="unknown",
                        parameters={"goal": goal},
                    ),
                ],
            )

    def _apply_domain_policy(self, plan: Plan, domain: str) -> None:
        """Apply domain policy checks to planned URLs."""
        domain_policy = get_domain_policy()
        for step in plan.steps:
            url = step.parameters.get("url")
            if not url:
                continue

            check = domain_policy.check(url, domain)
            if not check.allowed:
                step.status = StepStatus.SKIPPED
                step.error = f"Blocked by domain policy: {check.reason}"
                logger.warning(
                    "Plan step blocked by domain policy",
                    step_id=step.step_id,
                    url=url,
                    reason=check.reason,
                )
                continue

            if check.action == DomainAction.READ_ONLY:
                allowed = {
                    "web.extract",
                    "web.screenshot",
                    "web.get_text",
                    "web.scroll",
                    "web.wait",
                }
                if step.capability not in allowed:
                    step.status = StepStatus.SKIPPED
                    step.error = (
                        f"Read-only domain: capability '{step.capability}' not allowed"
                    )
                    logger.warning(
                        "Plan step blocked (read-only domain)",
                        step_id=step.step_id,
                        url=url,
                        capability=step.capability,
                    )

        while plan.current_step and plan.current_step.status == StepStatus.SKIPPED:
            plan.current_step_index += 1
