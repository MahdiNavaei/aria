from datetime import date

from aria.plugins.job_apply.models.profile import (
    Experience,
    ExperienceLevel,
    JobPreferences,
    ProfileManager,
    UserProfile,
)


def test_experience_duration_months() -> None:
    exp = Experience(
        title="Engineer",
        company="Acme",
        start_date=date(2020, 1, 1),
        end_date=date(2021, 1, 1),
    )

    assert exp.duration_months == 12
    assert exp.is_current is False


def test_experience_summary_uses_recent_roles() -> None:
    experiences = [
        Experience(
            title="Engineer",
            company="Acme",
            start_date=date(2021, 1, 1),
            end_date=date(2022, 1, 1),
        ),
        Experience(
            title="Analyst",
            company="Beta",
            start_date=date(2019, 1, 1),
            end_date=date(2020, 1, 1),
        ),
    ]
    profile = UserProfile(
        full_name="Test User",
        email="test@example.com",
        experiences=experiences,
    )

    summary = profile.experience_summary
    assert "Engineer" in summary
    assert "Acme" in summary


def test_to_dict_for_llm() -> None:
    profile = UserProfile(
        full_name="Test User",
        email="test@example.com",
        experience_level=ExperienceLevel.MID,
        skills=["Python", "SQL"],
        preferences=JobPreferences(titles=["Engineer"]),
    )

    payload = profile.to_dict_for_llm()

    assert payload["name"] == "Test User"
    assert payload["experience_level"] == "mid"
    assert payload["skills"]


def test_profile_manager_save_and_load(tmp_path) -> None:
    manager = ProfileManager(tmp_path)
    profile = UserProfile(full_name="Test User", email="test@example.com")

    manager.save_profile(profile, user_id="default")
    loaded = manager.get_profile(user_id="default")

    assert loaded is not None
    assert loaded.full_name == "Test User"
