import pytest

from aria.core.llm.base import LLMResponse
from aria.plugins.job_apply.matcher import JobMatcher
from aria.plugins.job_apply.models.job import Job
from aria.plugins.job_apply.models.profile import ExperienceLevel, JobPreferences, UserProfile


class FakeLLM:
    async def generate(self, messages, role=None, **kwargs):
        _ = messages
        _ = role
        _ = kwargs
        return LLMResponse(content='{"score": 75, "reasons": ["good"]}', model="fake")


@pytest.mark.asyncio
async def test_matcher_returns_score() -> None:
    profile = UserProfile(
        full_name="Test User",
        email="test@example.com",
        skills=["Python", "SQL"],
        experience_level=ExperienceLevel.MID,
        preferences=JobPreferences(),
    )
    job = Job(
        url="https://example.com",
        title="Python Developer",
        company="Acme",
        requirements=["Python", "SQL"],
        experience_level="mid",
    )

    matcher = JobMatcher(profile)
    matcher.llm = FakeLLM()

    score, reasons, rejections = await matcher.match(job)

    assert 0 <= score <= 100
    assert isinstance(reasons, list)
    assert rejections == []


def test_hard_filters_excluded_company() -> None:
    prefs = JobPreferences(excluded_companies=["BadCo"])
    profile = UserProfile(full_name="Test", email="t@example.com", preferences=prefs)
    job = Job(url="https://example.com", title="Dev", company="BadCo")

    matcher = JobMatcher(profile)
    passed, reasons = matcher._apply_hard_filters(job)

    assert passed is False
    assert reasons
