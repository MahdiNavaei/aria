"""UI configuration models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class UIFeatures(BaseModel):
    """Feature flags for UI components."""

    live_browser_view: bool = True
    hitl_panel: bool = True
    activity_log: bool = True
    chat_interface: bool = True


class ScreenshotStreamingConfig(BaseModel):
    """Screenshot streaming settings."""

    enabled: bool = True
    interval_ms: int = 1000
    quality: int = 50
    max_width: int = 1280


class UIConfig(BaseModel):
    """Top-level UI configuration."""

    model_config = ConfigDict(extra="ignore")

    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8501
    theme: str = "light"
    features: UIFeatures = Field(default_factory=UIFeatures)
    screenshot_streaming: ScreenshotStreamingConfig = Field(
        default_factory=ScreenshotStreamingConfig,
    )
