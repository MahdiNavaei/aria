"""Job apply plugin configuration models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MatchingConfig(BaseModel):
    """Matching thresholds for job apply."""

    min_score: int = 70
    auto_apply_threshold: int = 85


class LinkedInConfig(BaseModel):
    """LinkedIn-specific settings."""

    easy_apply_only: bool = False
    max_applications_per_day: int = 50
    email: str | None = None


class FormFillingConfig(BaseModel):
    """Form filling preferences."""

    use_skyvern: bool = True
    fallback_to_manual: bool = True


class JobApplyConfig(BaseModel):
    """Top-level job apply configuration."""

    model_config = ConfigDict(extra="ignore")

    sources: list[str] = Field(default_factory=lambda: ["linkedin", "indeed", "company_sites"])
    matching: MatchingConfig = Field(default_factory=MatchingConfig)
    linkedin: LinkedInConfig = Field(default_factory=LinkedInConfig)
    form_filling: FormFillingConfig = Field(default_factory=FormFillingConfig)
    profiles_dir: str = "data/profiles"
    jobs_dir: str = "data/jobs"
    applications_dir: str = "data/applications"
