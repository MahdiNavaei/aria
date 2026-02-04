"""Eye service orchestrating perception."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from aria.core.eye.models import (
    Blocker,
    BlockerType,
    Element,
    ElementType,
    Location,
    Observation,
    PageState,
)
from aria.core.eye.screenshot import Screenshot, get_screenshot_service
from aria.core.eye.uiref import UIRef, get_uiref_extractor
from aria.core.eye.vlm import get_vlm_analyzer
from aria.models.events import EventType
from aria.utils.events import EventEmitter
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class Eye:
    """ARIA Eye - perception component."""

    def __init__(self) -> None:
        """Initialize Eye with screenshot, VLM, and UIRef services."""
        self.screenshot_service = get_screenshot_service()
        self.vlm = get_vlm_analyzer()
        self.uiref_extractor = get_uiref_extractor()
        self._browser_page: Any | None = None

    def set_browser_page(self, page: Any) -> None:  # noqa: ANN401
        """Set Playwright page for browser operations."""
        self._browser_page = page
        self.screenshot_service.set_browser_page(page)
        self.uiref_extractor.set_browser_page(page)

    async def observe(
        self,
        domain: str,
        context: dict | None = None,
        source: str = "browser",
    ) -> Observation:
        """Capture screenshot, analyze it, and return an Observation."""
        _ = context or {}
        logger.debug("Creating observation", domain=domain, source=source)

        screenshot = await self.screenshot_service.capture(source=source)
        vlm_analysis = await self.vlm.analyze(screenshot)

        observation = Observation(
            observation_id=str(uuid4()),
            source=source,
            screenshot_ref=screenshot.ref,
            screenshot_base64=screenshot.base64,
            page_title=screenshot.metadata.get("title") or vlm_analysis.get("title"),
            page_url=screenshot.metadata.get("url"),
            page_type=vlm_analysis.get("page_type"),
            vlm_analysis=vlm_analysis,
        )

        observation.elements = self._extract_elements(vlm_analysis)

        blockers = self._detect_blockers(vlm_analysis)
        observation.blockers = blockers
        observation.has_captcha = any(b.type == BlockerType.CAPTCHA for b in blockers)
        observation.requires_login = any(b.type == BlockerType.LOGIN for b in blockers)

        if observation.is_blocked:
            observation.state = PageState.BLOCKED
        elif vlm_analysis.get("state") == "loading":
            observation.state = PageState.LOADING
        elif vlm_analysis.get("state") == "error":
            observation.state = PageState.ERROR
        else:
            observation.state = PageState.READY

        observations = vlm_analysis.get("observations")
        if isinstance(observations, list):
            observation.text_content = "\n".join(str(item) for item in observations)
        elif isinstance(observations, str):
            observation.text_content = observations

        await self._emit_observation_event(observation)

        logger.info(
            "Observation created",
            observation_id=observation.observation_id,
            state=observation.state.value,
            elements=len(observation.elements),
        )

        return observation

    def _extract_elements(self, vlm_analysis: dict) -> list[Element]:
        elements: list[Element] = []
        for index, elem_data in enumerate(vlm_analysis.get("elements", [])):
            elem_type = _parse_element_type(elem_data.get("type"))

            location = None
            if isinstance(elem_data.get("location"), dict):
                loc = elem_data["location"]
                location = Location(
                    x=int(loc.get("x", 0)),
                    y=int(loc.get("y", 0)),
                    width=int(loc.get("width", 0)),
                    height=int(loc.get("height", 0)),
                )

            element = Element(
                element_id=elem_data.get("id") or f"elem_{index}",
                type=elem_type,
                text=elem_data.get("text") or elem_data.get("label"),
                value=elem_data.get("value"),
                location=location,
                is_visible=True,
                is_enabled=elem_data.get("state") != "disabled",
                attributes=elem_data.get("attributes", {}),
                confidence=float(elem_data.get("confidence", 1.0)),
            )
            elements.append(element)
        return elements

    def _detect_blockers(self, vlm_analysis: dict) -> list[Blocker]:
        blockers: list[Blocker] = []
        for blocker_data in vlm_analysis.get("blockers", []):
            if isinstance(blocker_data, str):
                lowered = blocker_data.lower()
                if "captcha" in lowered:
                    blockers.append(
                        Blocker(type=BlockerType.CAPTCHA, description=blocker_data),
                    )
                elif "login" in lowered:
                    blockers.append(
                        Blocker(type=BlockerType.LOGIN, description=blocker_data),
                    )
                elif "popup" in lowered:
                    blockers.append(
                        Blocker(type=BlockerType.POPUP, description=blocker_data),
                    )
                elif "rate" in lowered:
                    blockers.append(
                        Blocker(type=BlockerType.RATE_LIMIT, description=blocker_data),
                    )
                else:
                    blockers.append(
                        Blocker(type=BlockerType.ERROR, description=blocker_data),
                    )
            elif isinstance(blocker_data, dict):
                blocker_type = _parse_blocker_type(blocker_data.get("type"))
                blockers.append(
                    Blocker(
                        type=blocker_type,
                        description=blocker_data.get("description", "Unknown blocker"),
                    ),
                )
        return blockers

    async def locate_element(
        self,
        description: str,
        screenshot: Screenshot | None = None,
    ) -> Element | None:
        """Locate an element by description using VLM."""
        if screenshot is None:
            screenshot = await self.screenshot_service.capture()

        element_data = await self.vlm.locate_element(screenshot, description)
        if not element_data:
            return None

        location = None
        if isinstance(element_data.get("location"), dict):
            loc = element_data["location"]
            location = Location(
                x=int(loc.get("x", 0)),
                y=int(loc.get("y", 0)),
                width=int(loc.get("width", 0)),
                height=int(loc.get("height", 0)),
            )

        return Element(
            element_id="located",
            type=_parse_element_type(element_data.get("type")),
            text=element_data.get("text"),
            location=location,
            confidence=float(element_data.get("confidence", 0.8)),
            is_visible=True,
            is_enabled=True,
        )

    async def extract_uiref(
        self,
        element_handle: Any,  # noqa: ANN401
        description: str,
        domain: str,
    ) -> UIRef:
        """Extract and save UIRef for an element."""
        uiref = await self.uiref_extractor.extract_from_element(
            element_handle,
            description,
            domain,
        )
        await self.uiref_extractor.save_uiref(uiref)
        return uiref

    async def _emit_observation_event(self, observation: Observation) -> None:
        try:
            await EventEmitter.emit(
                EventType.EYE_PERCEPTION_COMPLETED,
                {
                    "observation_id": observation.observation_id,
                    "screenshot_ref": observation.screenshot_ref,
                    "page_type": observation.page_type,
                    "state": observation.state.value,
                    "elements_count": len(observation.elements),
                    "blockers_count": len(observation.blockers),
                    "source": observation.source,
                },
            )
        except RuntimeError as exc:
            logger.debug("Event context not initialized", error=str(exc))


def _parse_element_type(value: str | None) -> ElementType:
    if not value:
        return ElementType.OTHER
    try:
        return ElementType(value)
    except ValueError:
        return ElementType.OTHER


def _parse_blocker_type(value: str | None) -> BlockerType:
    if not value:
        return BlockerType.ERROR
    try:
        return BlockerType(value)
    except ValueError:
        return BlockerType.ERROR


_eye: Eye | None = None


async def get_eye() -> Eye:
    """Return singleton Eye instance."""
    global _eye  # noqa: PLW0603
    if _eye is None:
        _eye = Eye()
    return _eye
