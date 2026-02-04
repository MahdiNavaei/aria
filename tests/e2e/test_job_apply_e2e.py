import pytest

from aria.core.hand.capability import Capability, CapabilityResult
from aria.plugins.job_apply.models.job import Job, JobStatus
from aria.plugins.job_apply.models.profile import UserProfile
from aria.plugins.job_apply.service import JobApplyService


class FakeHand:
    def __init__(self) -> None:
        self.browser_adapter = object()

    async def execute(self, capability, parameters, context):
        _ = parameters
        _ = context
        if capability == Capability.WEB_SCREENSHOT:
            return CapabilityResult.ok({}, screenshot_ref="shot-1")
        return CapabilityResult.ok({})


class FakeFormFiller:
    def __init__(self, browser_adapter) -> None:
        _ = browser_adapter

    async def fill_form(self, form_data, context=None):
        _ = context
        return CapabilityResult.ok({"filled": list(form_data.keys())})


class FakeMemoryManager:
    def __init__(self, session_id, user_id):
        _ = session_id
        _ = user_id

    async def record_observation(self, content, source, importance=0.5):
        _ = content
        _ = source
        _ = importance

    async def save_experience(self, goal, actions, outcome, domain):
        _ = goal
        _ = actions
        _ = outcome
        _ = domain
        return "mem-1"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_job_apply_pipeline(
    monkeypatch: pytest.MonkeyPatch,
    docker_services,
) -> None:
    profile = UserProfile(full_name="Test User", email="test@example.com")
    job = Job(url="https://example.com/job", title="Engineer", company="Acme")

    async def fake_extract(self, url):
        _ = self
        _ = url
        return job

    async def fake_match(self, job_arg):
        _ = job_arg
        return 80, ["match"], []

    async def fake_get_hand():
        return FakeHand()

    monkeypatch.setattr(
        "aria.plugins.job_apply.service.JobExtractor.extract_from_url",
        fake_extract,
    )
    monkeypatch.setattr(
        "aria.plugins.job_apply.service.JobMatcher.match",
        fake_match,
    )
    monkeypatch.setattr("aria.plugins.job_apply.service.get_hand", fake_get_hand)
    monkeypatch.setattr("aria.plugins.job_apply.service.FormFiller", FakeFormFiller)
    monkeypatch.setattr("aria.plugins.job_apply.service.MemoryManager", FakeMemoryManager)

    service = JobApplyService(user_id="default")
    await service.initialize(profile=profile)

    result = await service.process_job_url(
        "https://example.com/job",
        auto_apply=False,
        session_id="e2e-job",
    )

    assert result is not None
    assert result.status == JobStatus.MATCHED
