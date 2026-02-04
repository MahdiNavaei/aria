"""LLM configuration models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

MIN_TEMPERATURE = 0.0
MAX_TEMPERATURE = 2.0


class ModelConfig(BaseModel):
    """Legacy configuration for a single model role."""

    model_name: str
    temperature: float = 0.0
    max_tokens: int | None = None
    base_url: str | None = None
    api_key: str | None = None

    @field_validator("temperature")
    @classmethod
    def _validate_temperature(cls, value: float) -> float:
        if value < MIN_TEMPERATURE or value > MAX_TEMPERATURE:
            msg = f"temperature must be between {MIN_TEMPERATURE} and {MAX_TEMPERATURE}"
            raise ValueError(msg)
        return value


class OllamaModelOptions(BaseModel):
    """Per-model options for Ollama."""

    temperature: float = 0.7
    num_predict: int = 2000
    top_p: float | None = None

    @field_validator("temperature")
    @classmethod
    def _validate_temperature(cls, value: float) -> float:
        if value < MIN_TEMPERATURE or value > MAX_TEMPERATURE:
            msg = f"temperature must be between {MIN_TEMPERATURE} and {MAX_TEMPERATURE}"
            raise ValueError(msg)
        return value


class OllamaModels(BaseModel):
    """Model names for Ollama roles."""

    brain: str = "aria-brain"
    brain_persian: str | None = None
    brain_persian_reasoning: str | None = None
    coder: str | None = None
    eye: str | None = None
    embedding: str | None = None
    audio: str | None = None
    ml: str | None = None


class OllamaSettings(BaseModel):
    """Ollama-specific settings."""

    base_url: str = "http://localhost:11434"
    models: OllamaModels = Field(default_factory=OllamaModels)
    options: OllamaModelOptions = Field(default_factory=OllamaModelOptions)
    model_options: dict[str, OllamaModelOptions] = Field(default_factory=dict)


class LLMConfig(BaseModel):
    """Configuration for LLM providers and role assignments."""

    model_config = ConfigDict(extra="ignore")

    provider: Literal["ollama", "openai", "anthropic"] = "ollama"
    models_path: str | None = None

    # Legacy fields
    model_name: str = "aria-brain"
    base_url: str = "http://localhost:11434"
    api_key: str | None = None
    roles: dict[str, ModelConfig] = Field(default_factory=dict)

    # Provider-specific
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
