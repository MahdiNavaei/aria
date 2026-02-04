"""Hand configuration models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BrowserViewportConfig(BaseModel):
    """Browser viewport configuration."""

    width: int = 1280
    height: int = 720


class BrowserConfig(BaseModel):
    """Browser adapter configuration."""

    headless: bool = False
    slow_mo: int = 50
    timeout: int = 30000
    viewport: BrowserViewportConfig = Field(default_factory=BrowserViewportConfig)


class DesktopConfig(BaseModel):
    """Desktop adapter configuration."""

    fail_safe: bool = True
    pause: float = 0.1


class HandConfig(BaseModel):
    """Top-level Hand configuration."""

    model_config = ConfigDict(extra="ignore")

    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    desktop: DesktopConfig = Field(default_factory=DesktopConfig)
    adapters: list[str] = Field(default_factory=lambda: ["browser", "desktop", "ml"])
