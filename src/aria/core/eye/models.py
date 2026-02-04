"""Models for Eye observations and UI elements."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ElementType(str, Enum):
    """Supported UI element types."""

    BUTTON = "button"
    INPUT = "input"
    LINK = "link"
    TEXT = "text"
    IMAGE = "image"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    FORM = "form"
    TABLE = "table"
    LIST = "list"
    OTHER = "other"


class Location(BaseModel):
    """Element location in pixels."""

    x: int
    y: int
    width: int
    height: int

    @property
    def center(self) -> tuple[int, int]:
        """Return center point of the bounding box."""
        return (self.x + self.width // 2, self.y + self.height // 2)


class Element(BaseModel):
    """Detected UI element."""

    element_id: str
    type: ElementType
    text: str | None = None
    value: str | None = None
    location: Location | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    is_visible: bool = True
    is_enabled: bool = True
    confidence: float = 1.0


class PageState(str, Enum):
    """Page readiness state."""

    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    BLOCKED = "blocked"


class BlockerType(str, Enum):
    """Types of blockers that prevent interaction."""

    CAPTCHA = "captcha"
    LOGIN = "login"
    POPUP = "popup"
    ERROR = "error"
    RATE_LIMIT = "rate_limit"


class Blocker(BaseModel):
    """Obstacle blocking interaction."""

    type: BlockerType
    description: str
    screenshot_ref: str | None = None


class Observation(BaseModel):
    """Complete observation from Eye."""

    observation_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source: str
    screenshot_ref: str
    screenshot_base64: str | None = None
    page_title: str | None = None
    page_url: str | None = None
    page_type: str | None = None
    state: PageState = PageState.READY
    elements: list[Element] = Field(default_factory=list)
    blockers: list[Blocker] = Field(default_factory=list)
    has_captcha: bool = False
    requires_login: bool = False
    login_form_ref: str | None = None
    text_content: str | None = None
    vlm_analysis: dict[str, Any] | None = None

    @property
    def is_blocked(self) -> bool:
        """Return True if any blockers are present."""
        return len(self.blockers) > 0 or self.has_captcha or self.requires_login

    def get_element_by_type(self, element_type: ElementType) -> list[Element]:
        """Return elements that match the given type."""
        return [element for element in self.elements if element.type == element_type]

    def get_element_by_text(self, text: str) -> Element | None:
        """Return the first element whose text contains the given string."""
        for element in self.elements:
            if element.text and text.lower() in element.text.lower():
                return element
        return None
