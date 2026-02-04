"""Voice configuration models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class STTConfig(BaseModel):
    """Speech-to-text configuration."""

    primary: str = "nezamisafa/whisper-persian-v4"
    files: list[str] = Field(default_factory=list)
    audio_model: str = "Qwen2-Audio-7B-Instruct"


class VoiceConfig(BaseModel):
    """Top-level voice configuration."""

    model_config = ConfigDict(extra="ignore")

    enabled: bool = True
    stt: STTConfig = Field(default_factory=STTConfig)
    use_cases: list[str] = Field(default_factory=list)
