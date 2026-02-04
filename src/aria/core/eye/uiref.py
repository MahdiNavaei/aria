"""UI reference extraction and storage for Eye."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from aria.config import get_settings
from aria.core.memory import SemanticMemory
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class LocatorType(str, Enum):
    """Supported locator types."""

    CSS = "css"
    TEXT = "text"
    ARIA_LABEL = "aria_label"
    ROLE = "role"
    XPATH = "xpath"


class Locator(BaseModel):
    """A UI locator with confidence score."""

    type: LocatorType
    value: str
    confidence: float = 0.5
    last_success: str | None = None


class UIRef(BaseModel):
    """UI reference definition for reuse."""

    uiref_id: str
    description: str
    domain: str
    page_pattern: str
    locators: list[Locator] = Field(default_factory=list)
    visual_description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class UIRefExtractor:
    """Extract UIRefs from Playwright element handles."""

    def __init__(self, semantic_memory: SemanticMemory | None = None) -> None:
        """Initialize UIRef extractor with semantic memory."""
        self.semantic_memory = semantic_memory or SemanticMemory()
        self._browser_page: Any | None = None
        self._settings = get_settings().eye.uiref

    def set_browser_page(self, page: Any) -> None:  # noqa: ANN401
        """Set Playwright page context for extraction."""
        self._browser_page = page

    async def extract_from_element(  # noqa: PLR0912, PLR0915, C901
        self,
        element_handle: Any,  # noqa: ANN401
        description: str,
        domain: str,
    ) -> UIRef:
        """Extract locators from an element handle."""
        locators: list[Locator] = []

        try:
            element_id = await element_handle.get_attribute("id")
            if element_id:
                locators.append(
                    Locator(
                        type=LocatorType.CSS,
                        value=f"#{element_id}",
                        confidence=0.95,
                    ),
                )
        except Exception:  # noqa: BLE001
            logger.debug("Failed to extract element id", exc_info=True)

        try:
            test_id = await element_handle.get_attribute("data-testid")
            if test_id:
                locators.append(
                    Locator(
                        type=LocatorType.CSS,
                        value=f'[data-testid="{test_id}"]',
                        confidence=0.9,
                    ),
                )
        except Exception:  # noqa: BLE001
            logger.debug("Failed to extract data-testid", exc_info=True)

        try:
            name_attr = await element_handle.get_attribute("name")
            if name_attr:
                locators.append(
                    Locator(
                        type=LocatorType.CSS,
                        value=f'[name="{name_attr}"]',
                        confidence=0.8,
                    ),
                )
        except Exception:  # noqa: BLE001
            logger.debug("Failed to extract name attribute", exc_info=True)

        try:
            text = await element_handle.inner_text()
            max_text_length = 120
            if text and len(text) < max_text_length:
                locators.append(
                    Locator(
                        type=LocatorType.TEXT,
                        value=text.strip(),
                        confidence=0.8,
                    ),
                )
        except Exception:  # noqa: BLE001
            logger.debug("Failed to extract inner text", exc_info=True)

        try:
            aria_label = await element_handle.get_attribute("aria-label")
            if aria_label:
                locators.append(
                    Locator(
                        type=LocatorType.ARIA_LABEL,
                        value=aria_label,
                        confidence=0.9,
                    ),
                )
        except Exception:  # noqa: BLE001
            logger.debug("Failed to extract aria-label", exc_info=True)

        try:
            role = await element_handle.get_attribute("role")
            if role:
                locators.append(
                    Locator(
                        type=LocatorType.ROLE,
                        value=role,
                        confidence=0.7,
                    ),
                )
        except Exception:  # noqa: BLE001
            logger.debug("Failed to extract role attribute", exc_info=True)

        try:
            xpath = await element_handle.evaluate(
                """
                (el) => {
                    let path = [];
                    while (el && el.nodeType === Node.ELEMENT_NODE) {
                        let idx = 0;
                        let sibling = el.previousSibling;
                        while (sibling) {
                            if (sibling.nodeType === Node.ELEMENT_NODE &&
                                sibling.nodeName === el.nodeName) {
                                idx++;
                            }
                            sibling = sibling.previousSibling;
                        }
                        let name = el.nodeName.toLowerCase();
                        if (idx > 0) {
                            name += '[' + (idx + 1) + ']';
                        }
                        path.unshift(name);
                        el = el.parentNode;
                    }
                    return '/' + path.join('/');
                }
                """,
            )
            if xpath:
                locators.append(
                    Locator(
                        type=LocatorType.XPATH,
                        value=xpath,
                        confidence=0.85,
                    ),
                )
        except Exception:  # noqa: BLE001
            logger.debug("Failed to extract xpath", exc_info=True)

        locators = _dedupe_locators(locators)
        threshold = self._settings.confidence_threshold
        if threshold > 0:
            locators = [loc for loc in locators if loc.confidence >= threshold]

        page_url = self._browser_page.url if self._browser_page else "unknown"
        uiref_id = f"{domain}.{_slugify(description)}"

        uiref = UIRef(
            uiref_id=uiref_id,
            description=description,
            domain=domain,
            page_pattern=page_url,
            locators=locators,
            visual_description=description,
        )

        logger.debug(
            "UIRef extracted",
            uiref_id=uiref_id,
            locators_count=len(locators),
        )

        return uiref

    async def save_uiref(self, uiref: UIRef) -> None:
        """Save UIRef to semantic memory."""
        await self.semantic_memory.add_uiref(
            uiref_id=uiref.uiref_id,
            uiref_def=uiref.model_dump(),
            description=uiref.description,
        )

    async def get_uiref(self, uiref_id: str) -> UIRef | None:
        """Load UIRef by id."""
        data = await self.semantic_memory.get_uiref(uiref_id)
        if data:
            return UIRef(**data)
        return None

    async def find_uiref(self, description: str, domain: str) -> UIRef | None:
        """Find UIRef by description search."""
        uiref_id = f"{domain}.{_slugify(description)}"
        return await self.get_uiref(uiref_id)


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower())
    cleaned = cleaned.strip("_")
    return cleaned or "element"


def _dedupe_locators(locators: list[Locator]) -> list[Locator]:
    seen = set()
    unique: list[Locator] = []
    for locator in locators:
        key = (locator.type, locator.value)
        if key in seen:
            continue
        seen.add(key)
        unique.append(locator)
    return unique


_uiref_extractor: UIRefExtractor | None = None


def get_uiref_extractor() -> UIRefExtractor:
    """Return singleton UIRefExtractor instance."""
    global _uiref_extractor  # noqa: PLW0603
    if _uiref_extractor is None:
        _uiref_extractor = UIRefExtractor()
    return _uiref_extractor
