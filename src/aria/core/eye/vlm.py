"""Vision-language model analyzer for Eye."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from aria.config import get_settings
from aria.core.llm import Message, ModelRole, get_llm_client
from aria.utils.logging import get_logger

if TYPE_CHECKING:
    from aria.core.eye.screenshot import Screenshot
else:
    from aria.core.eye.screenshot import Screenshot  # noqa: TC001

logger = get_logger(__name__)

ANALYZE_SYSTEM_PROMPT = """You are the vision component of ARIA, an AI assistant.
Your job is to analyze screenshots and understand what is visible on the screen.

For each screenshot, identify:
1. Page type (login, form, list, article, dashboard, etc.)
2. Key UI elements (buttons, inputs, links, text)
3. Current state (loading, error, success, etc.)
4. Any blockers (CAPTCHA, popup, login required)

Output format (JSON):
{
    "page_type": "form",
    "title": "Job Application",
    "elements": [
        {
            "type": "input",
            "label": "First Name",
            "value": "",
            "location": {"x": 100, "y": 200, "width": 200, "height": 30},
            "required": true
        },
        {
            "type": "button",
            "text": "Submit",
            "location": {"x": 150, "y": 400, "width": 100, "height": 40},
            "state": "enabled"
        }
    ],
    "state": "ready",
    "blockers": [],
    "observations": ["Form has 5 required fields", "Submit button is enabled"]
}

For blockers, identify:
- captcha: CAPTCHA challenge visible
- login: Login/authentication required
- error: Error message displayed
- popup: Modal/popup blocking interaction
"""

ELEMENT_LOCATE_PROMPT = """Find the element described below in this screenshot.

Element to find: {description}

Return the element's location as JSON:
{
    "found": true,
    "element": {
        "type": "button",
        "text": "Submit",
        "location": {"x": 150, "y": 400, "width": 100, "height": 40},
        "confidence": 0.95
    }
}

If not found:
{
    "found": false,
    "reason": "Element not visible on screen"
}
"""


class VLMAnalyzer:
    """Vision-language analyzer for understanding screenshots."""

    def __init__(self) -> None:
        """Initialize VLM analyzer with LLM client."""
        self.llm = get_llm_client()
        self._settings = get_settings().eye.vlm

    async def analyze(self, screenshot: Screenshot) -> dict[str, Any]:
        """Analyze a screenshot and return a structured dict."""
        messages = [
            Message(role="system", content=ANALYZE_SYSTEM_PROMPT),
            Message(
                role="user",
                content="Analyze this screenshot and describe what you see.",
                images=[screenshot.base64],
            ),
        ]

        response = await self.llm.generate(
            messages,
            role=ModelRole.EYE,
            temperature=self._settings.temperature,
            max_tokens=self._settings.max_tokens,
        )

        analysis = _parse_json_response(response.content)
        logger.debug(
            "VLM analysis complete",
            page_type=analysis.get("page_type"),
            elements_count=len(analysis.get("elements", [])),
        )
        return analysis

    async def locate_element(
        self,
        screenshot: Screenshot,
        description: str,
    ) -> dict[str, Any] | None:
        """Locate a specific element by natural language description."""
        messages = [
            Message(role="system", content=ANALYZE_SYSTEM_PROMPT),
            Message(
                role="user",
                content=ELEMENT_LOCATE_PROMPT.replace("{description}", description),
                images=[screenshot.base64],
            ),
        ]

        response = await self.llm.generate(
            messages,
            role=ModelRole.EYE,
            temperature=self._settings.temperature,
            max_tokens=self._settings.max_tokens,
        )

        data = _parse_json_response(response.content)
        if data.get("found") is False:
            return None

        element = data.get("element")
        if isinstance(element, dict):
            return element
        return None


def _parse_json_response(content: str) -> dict[str, Any]:
    json_start = content.find("{")
    json_end = content.rfind("}")
    if json_start == -1 or json_end == -1 or json_end <= json_start:
        return {"raw": content}

    snippet = content[json_start : json_end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError:
        return {"raw": content}


_vlm_analyzer: VLMAnalyzer | None = None


def get_vlm_analyzer() -> VLMAnalyzer:
    """Return singleton VLMAnalyzer instance."""
    global _vlm_analyzer  # noqa: PLW0603
    if _vlm_analyzer is None:
        _vlm_analyzer = VLMAnalyzer()
    return _vlm_analyzer
