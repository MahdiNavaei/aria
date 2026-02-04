"""Capability interfaces for Hand adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CapabilityCategory(str, Enum):
    """Capability categories for adapters."""

    WEB = "web"
    DESKTOP = "desktop"
    CURSOR = "cursor"
    ML = "ml"
    FILE = "file"


class Capability(str, Enum):
    """All available capabilities."""

    WEB_NAVIGATE = "web.navigate"
    WEB_CLICK = "web.click"
    WEB_FILL = "web.fill"
    WEB_SELECT = "web.select"
    WEB_EXTRACT = "web.extract"
    WEB_SCREENSHOT = "web.screenshot"
    WEB_SCROLL = "web.scroll"
    WEB_WAIT = "web.wait"
    WEB_UPLOAD = "web.upload"

    DESKTOP_CLICK = "desktop.click"
    DESKTOP_TYPE = "desktop.type"
    DESKTOP_HOTKEY = "desktop.hotkey"
    DESKTOP_SCREENSHOT = "desktop.screenshot"
    DESKTOP_FIND_WINDOW = "desktop.find_window"
    DESKTOP_FOCUS_WINDOW = "desktop.focus_window"

    CURSOR_OPEN_FILE = "cursor.open_file"
    CURSOR_EDIT = "cursor.edit"
    CURSOR_RUN_COMMAND = "cursor.run_command"
    CURSOR_CHAT = "cursor.chat"

    ML_MATCH_JOB = "ml.match_job"
    ML_GENERATE_COVER_LETTER = "ml.generate_cover_letter"
    ML_EXTRACT_JOB_INFO = "ml.extract_job_info"

    @property
    def category(self) -> CapabilityCategory:
        """Return the category of this capability."""
        prefix = self.value.split(".")[0]
        return CapabilityCategory(prefix)


class CapabilityResult(BaseModel):
    """Result of capability execution."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    duration_ms: int = 0
    screenshot_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def ok(
        cls,
        data: dict[str, Any] | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> CapabilityResult:
        """Create a successful capability result."""
        return cls(success=True, data=data or {}, **kwargs)

    @classmethod
    def fail(cls, error: str, **kwargs: Any) -> CapabilityResult:  # noqa: ANN401
        """Create a failed capability result."""
        return cls(success=False, error=error, **kwargs)


class ExecutionContext(BaseModel):
    """Context passed to capability execution."""

    model_config = ConfigDict(extra="ignore")

    session_id: str
    domain: str
    step_id: str | None = None
    timeout: int = 30
    retry_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class CapabilityAdapter(ABC):
    """Base class for capability adapters."""

    @property
    @abstractmethod
    def category(self) -> CapabilityCategory:
        """Return the category this adapter handles."""

    @property
    @abstractmethod
    def capabilities(self) -> list[Capability]:
        """Return list of capabilities this adapter provides."""

    @abstractmethod
    async def execute(
        self,
        capability: Capability,
        parameters: dict[str, Any],
        context: ExecutionContext,
    ) -> CapabilityResult:
        """Execute a capability with given parameters."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize adapter resources."""

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup adapter resources."""
