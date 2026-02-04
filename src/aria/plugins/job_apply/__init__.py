"""Job Apply Plugin for ARIA providing job search, matching, and application automation."""

from typing import Any, ClassVar

from aria.plugins.job_apply.extractor import JobExtractor
from aria.plugins.job_apply.matcher import JobMatcher
from aria.plugins.job_apply.models.job import ApplicationResult, Job, JobSource, JobStatus
from aria.plugins.job_apply.models.profile import ProfileManager, UserProfile
from aria.plugins.job_apply.service import JobApplyService

__all__ = [
    "ApplicationResult",
    "Job",
    "JobApplyPlugin",
    "JobApplyService",
    "JobExtractor",
    "JobMatcher",
    "JobSource",
    "JobStatus",
    "ProfileManager",
    "UserProfile",
]


class JobApplyPlugin:
    """Job Apply domain plugin for ARIA."""

    name = "job_apply"
    version = "1.0.0"

    capabilities: ClassVar[list[str]] = [
        "job.search",
        "job.extract",
        "job.match",
        "job.apply",
        "job.generate_cover_letter",
        "job.process",
    ]

    def __init__(self) -> None:
        """Initialize the plugin."""
        self.service: JobApplyService | None = None

    async def initialize(self, user_id: str = "default") -> None:
        """Initialize plugin with user profile."""
        self.service = JobApplyService(user_id)
        await self.service.initialize()

    async def execute(
        self, capability: str, parameters: dict, context: dict,
    ) -> Any:  # noqa: ANN401
        """Execute a capability."""
        if self.service is None:
            msg = "JobApplyPlugin not initialized"
            raise RuntimeError(msg)

        if capability == "job.extract":
            return await self.service.extractor.extract_from_url(parameters.get("url"))

        if capability == "job.match":
            job = parameters.get("job")
            if job:
                score, reasons, _ = await self.service._matcher.match(job)  # noqa: SLF001
                return {"score": score, "reasons": reasons}

        if capability == "job.apply":
            job = parameters.get("job")
            session_id = context.get("session_id", "default")
            if job:
                return await self.service.apply_to_job(job, session_id)

        if capability == "job.process":
            url = parameters.get("url")
            auto_apply = parameters.get("auto_apply", False)
            session_id = context.get("session_id", "default")
            return await self.service.process_job_url(url, auto_apply, session_id)

        msg = f"Unknown capability: {capability}"
        raise ValueError(msg)

    def get_brain_tools(self) -> list[dict]:
        """Get tool definitions for Brain."""
        return [
            {
                "name": "job.process",
                "description": (
                    "Process a job URL: extract info, match with profile, optionally apply"
                ),
                "parameters": {
                    "url": {"type": "string", "description": "Job posting URL"},
                    "auto_apply": {"type": "boolean", "default": False},
                },
            },
            {
                "name": "job.extract",
                "description": "Extract job information from URL",
                "parameters": {"url": {"type": "string", "description": "Job posting URL"}},
            },
            {
                "name": "job.apply",
                "description": "Apply to a matched job",
                "parameters": {"job": {"type": "object", "description": "Job object to apply"}},
            },
        ]


def register_plugin() -> JobApplyPlugin:
    """Register plugin with ARIA."""
    return JobApplyPlugin()
