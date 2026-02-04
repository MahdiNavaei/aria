"""Convert OpenAdapt recordings to ARIA skills."""

from __future__ import annotations

from typing import Any

from aria.core.learning.skill_extractor import Skill
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class OpenAdaptSkillConverter:
    """Convert OpenAdapt recordings to ARIA skills.

    OpenAdapt records mouse/keyboard actions with screenshots.
    We convert these to ARIA skill format.
    """

    def convert_recording(
        self,
        recording: dict[str, Any],
        skill_id: str,
        name: str,
        description: str,
    ) -> Skill:
        """Convert an OpenAdapt recording to an ARIA Skill."""
        actions = recording.get("actions", [])
        steps: list[dict[str, Any]] = []

        for action in actions:
            step = self._convert_action(action)
            if step:
                steps.append(step)

        parameters = self._detect_parameters(steps)

        logger.info(
            "OpenAdapt recording converted",
            skill_id=skill_id,
            steps=len(steps),
            parameters=len(parameters),
        )

        return Skill(
            skill_id=skill_id,
            name=name,
            description=description,
            domain="desktop",
            trigger=f"User says: {name}",
            steps=steps,
            parameters=parameters,
        )

    def _convert_action(self, action: dict[str, Any]) -> dict[str, Any] | None:
        """Convert a single OpenAdapt action to an ARIA step."""
        action_type = action.get("type")

        if action_type == "click":
            return {
                "capability": "desktop.click",
                "parameters_template": {
                    "x": action.get("x"),
                    "y": action.get("y"),
                    "button": action.get("button", "left"),
                },
            }

        if action_type == "type":
            return {
                "capability": "desktop.type",
                "parameters_template": {"text": action.get("text", "")},
            }

        if action_type == "hotkey":
            return {
                "capability": "desktop.hotkey",
                "parameters_template": {"keys": action.get("keys", [])},
            }

        return None

    def _detect_parameters(self, steps: list[dict[str, Any]]) -> list[str]:
        """Detect variable parameters in steps."""
        parameters: list[str] = []

        for index, step in enumerate(steps):
            params = step.get("parameters_template", {})
            if step.get("capability") == "desktop.type":
                param_name = f"input_{index}"
                parameters.append(param_name)
                params["text"] = f"${{{param_name}}}"

        return parameters
