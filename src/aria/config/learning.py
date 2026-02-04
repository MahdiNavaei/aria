"""Learning configuration models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SkillExtractionConfig(BaseModel):
    """Skill extraction settings."""

    min_steps: int = 3
    success_required: bool = True
    auto_generalize: bool = True


class PolicyLearningConfig(BaseModel):
    """Policy learning settings."""

    from_corrections: bool = True
    from_approvals: bool = True
    from_rejections: bool = True
    initial_confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class UIRefRefinementConfig(BaseModel):
    """UIRef refinement settings."""

    confidence_increment: float = 0.05
    confidence_decrement: float = 0.15
    min_confidence: float = 0.1


class LearningConfig(BaseModel):
    """Top-level learning configuration."""

    model_config = ConfigDict(extra="ignore")

    enabled: bool = True
    skill_extraction: SkillExtractionConfig = Field(default_factory=SkillExtractionConfig)
    policy_learning: PolicyLearningConfig = Field(default_factory=PolicyLearningConfig)
    uiref_refinement: UIRefRefinementConfig = Field(default_factory=UIRefRefinementConfig)
    artifacts_dir: str = "data/artifacts"
    recordings_dir: str = "data/recordings"
    consumer_group: str = "aria-learning"
