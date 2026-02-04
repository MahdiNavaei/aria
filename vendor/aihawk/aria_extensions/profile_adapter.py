"""Profile adapter to map ARIA profiles into AIHawk needs."""

from __future__ import annotations

from typing import Any

from aria.utils.logging import get_logger

logger = get_logger(__name__)


class ProfileAdapter:
    """Adapt ARIA user profiles to AIHawk input schema."""

    @staticmethod
    def to_aihawk(profile: dict[str, Any]) -> dict[str, Any]:
        """Translate a profile dict into AIHawk-friendly fields."""
        mapped = {
            "full_name": profile.get("full_name") or profile.get("name"),
            "email": profile.get("email"),
            "phone": profile.get("phone"),
            "location": profile.get("location"),
            "skills": profile.get("skills", []),
            "headline": profile.get("headline"),
            "linkedin_url": profile.get("linkedin_url"),
        }
        logger.debug("Profile adapted for AIHawk", keys=list(mapped.keys()))
        return mapped
