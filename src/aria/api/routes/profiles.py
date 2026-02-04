"""Profile endpoints for job apply."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from aria.config import get_settings
from aria.plugins.job_apply.models.profile import ProfileManager, UserProfile

router = APIRouter()


@router.get("/")
async def list_profiles() -> dict[str, list[str]]:
    """List available profiles."""
    profiles_dir = Path(get_settings().job_apply.profiles_dir)
    profiles_dir.mkdir(parents=True, exist_ok=True)
    profiles = [path.stem for path in profiles_dir.glob("*.json")]
    return {"profiles": sorted(profiles)}


@router.get("/{user_id}")
async def get_profile(user_id: str) -> dict:
    """Return a profile by user id."""
    manager = ProfileManager(Path(get_settings().job_apply.profiles_dir))
    profile = manager.get_profile(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile.model_dump()


@router.post("/{user_id}")
async def save_profile(user_id: str, profile: UserProfile) -> dict:
    """Create or update a user profile."""
    manager = ProfileManager(Path(get_settings().job_apply.profiles_dir))
    manager.save_profile(profile, user_id=user_id)
    return profile.model_dump()
