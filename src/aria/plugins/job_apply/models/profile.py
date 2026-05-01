"""User profile models for job apply plugin."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import Path  # noqa: TC003 - used by Pydantic at runtime

from pydantic import BaseModel, Field


def _today() -> date:
    """Return today's date."""
    return datetime.now(UTC).date()


class ExperienceLevel(StrEnum):
    """User experience level."""

    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class JobType(StrEnum):
    """Type of job position."""

    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    REMOTE = "remote"
    HYBRID = "hybrid"
    ON_SITE = "on_site"


class Education(BaseModel):
    """Educational background."""

    degree: str
    field: str
    institution: str
    graduation_year: int | None = None
    gpa: float | None = None


class Experience(BaseModel):
    """Work experience entry."""

    title: str
    company: str
    start_date: date
    end_date: date | None = None
    description: str = ""
    skills_used: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)

    @property
    def is_current(self) -> bool:
        """Return whether this is the current position."""
        return self.end_date is None

    @property
    def duration_months(self) -> int:
        """Calculate duration in months."""
        end = self.end_date or _today()
        return (end.year - self.start_date.year) * 12 + (end.month - self.start_date.month)


class JobPreferences(BaseModel):
    """Job search preferences."""

    titles: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    remote_ok: bool = True
    hybrid_ok: bool = True
    on_site_ok: bool = False
    min_salary: int | None = None
    max_salary: int | None = None
    job_types: list[JobType] = Field(default_factory=lambda: [JobType.FULL_TIME])
    industries: list[str] = Field(default_factory=list)
    company_sizes: list[str] = Field(default_factory=list)
    excluded_companies: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    """Complete user profile for job applications."""

    full_name: str
    email: str
    phone: str | None = None
    location: str | None = None
    headline: str = ""
    summary: str = ""
    experience_level: ExperienceLevel = ExperienceLevel.MID
    skills: list[str] = Field(default_factory=list)
    primary_skills: list[str] = Field(default_factory=list)
    experiences: list[Experience] = Field(default_factory=list)
    total_years_experience: float = 0
    education: list[Education] = Field(default_factory=list)
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    resume_path: Path | None = None
    cover_letter_template: str | None = None
    preferences: JobPreferences = Field(default_factory=JobPreferences)
    last_updated: date = Field(default_factory=_today)

    @property
    def experience_summary(self) -> str:
        """Generate an experience summary from recent positions."""
        if not self.experiences:
            return self.summary

        recent = sorted(self.experiences, key=lambda exp: exp.start_date, reverse=True)[:3]
        parts = []
        for exp in recent:
            years = exp.duration_months // 12
            parts.append(f"{exp.title} at {exp.company} ({years}+ years)")
        return "; ".join(parts)

    def to_dict_for_llm(self) -> dict:
        """Convert profile data into a compact LLM context."""
        salary_range = None
        if self.preferences.min_salary:
            salary_range = f"{self.preferences.min_salary}-{self.preferences.max_salary}"

        return {
            "name": self.full_name,
            "headline": self.headline,
            "summary": self.summary,
            "skills": self.primary_skills or self.skills[:10],
            "experience_years": self.total_years_experience,
            "experience_level": self.experience_level.value,
            "recent_experience": self.experience_summary,
            "education": [f"{edu.degree} in {edu.field}" for edu in self.education],
            "preferences": {
                "titles": self.preferences.titles,
                "locations": self.preferences.locations,
                "remote_ok": self.preferences.remote_ok,
                "salary_range": salary_range,
            },
        }

    @classmethod
    def load(cls, path: Path) -> UserProfile:
        """Load profile from JSON file."""
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(**data)

    def save(self, path: Path) -> None:
        """Save profile to JSON file."""
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")


@dataclass
class ProfileManager:
    """Manage user profiles."""

    profiles_dir: Path
    _current_profile: UserProfile | None = None

    def __post_init__(self) -> None:
        """Initialize profile directory."""
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def get_profile(self, user_id: str = "default") -> UserProfile | None:
        """Get profile by user id."""
        path = self.profiles_dir / f"{user_id}.json"
        if path.exists():
            return UserProfile.load(path)
        return None

    def save_profile(self, profile: UserProfile, user_id: str = "default") -> None:
        """Save profile to disk."""
        path = self.profiles_dir / f"{user_id}.json"
        profile.save(path)

    def set_current(self, profile: UserProfile) -> None:
        """Set current active profile."""
        self._current_profile = profile

    @property
    def current(self) -> UserProfile | None:
        """Return current active profile."""
        return self._current_profile
