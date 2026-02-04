"""Eye configuration models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScreenshotConfig(BaseModel):
    """Screenshot configuration."""

    dir: str = "data/screenshots"
    format: str = "png"
    quality: int = 85
    max_storage_mb: int = 500

    @field_validator("quality")
    @classmethod
    def _validate_quality(cls, value: int) -> int:
        min_quality = 1
        max_quality = 100
        if value < min_quality or value > max_quality:
            msg = f"quality must be between {min_quality} and {max_quality}"
            raise ValueError(msg)
        return value


class VLMOCRConfig(BaseModel):
    """OCR VLM configuration."""

    model: str
    model_file: str | None = None


class VLMFallbackConfig(BaseModel):
    """Fallback VLM configuration."""

    model: str
    model_file: str | None = None
    mmproj_file: str | None = None


class VLMConfig(BaseModel):
    """Vision language model configuration."""

    model: str = "aria-eye"
    model_file: str | None = None
    mmproj_file: str | None = None
    max_tokens: int = 1000
    temperature: float = 0.1
    ocr_persian: VLMOCRConfig | None = None
    fallback: VLMFallbackConfig | None = None


class UIRefConfig(BaseModel):
    """UIRef storage configuration."""

    storage_dir: str = "data/artifacts/uirefs"
    confidence_threshold: float = 0.3


class EyeConfig(BaseModel):
    """Top-level Eye configuration."""

    model_config = ConfigDict(extra="ignore")

    screenshot: ScreenshotConfig = Field(default_factory=ScreenshotConfig)
    vlm: VLMConfig = Field(default_factory=VLMConfig)
    uiref: UIRefConfig = Field(default_factory=UIRefConfig)
