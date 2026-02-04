"""Job apply service orchestrating extraction, matching, and apply."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from aria.adapters.browser.form_filler import FormFiller
from aria.config import get_settings
from aria.core.hand import get_hand
from aria.core.hand.capability import Capability
from aria.core.memory import MemoryManager
from aria.models.events import EventType
from aria.plugins.job_apply.extractor import JobExtractor
from aria.plugins.job_apply.matcher import JobMatcher
from aria.plugins.job_apply.models.job import ApplicationResult, Job, JobStatus
from aria.plugins.job_apply.models.profile import ProfileManager, UserProfile
from aria.utils.events import EventEmitter
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class JobApplyService:
    """Main service for job application automation."""

    def __init__(self, user_id: str = "default") -> None:
        """Initialize job apply service for a user."""
        self.user_id = user_id
        self.extractor = JobExtractor()
        self._profile: UserProfile | None = None
        self._matcher: JobMatcher | None = None
        self._hand = None
        self._form_filler: FormFiller | None = None
        self._memory: MemoryManager | None = None
        self._min_score = get_settings().job_apply.matching.min_score

    async def initialize(self, profile: UserProfile | None = None) -> None:
        """Initialize service with user profile."""
        if profile:
            self._profile = profile
        else:
            profiles_dir = Path(get_settings().job_apply.profiles_dir)
            manager = ProfileManager(profiles_dir)
            self._profile = manager.get_profile(self.user_id)

        if not self._profile:
            msg = f"No profile found for user: {self.user_id}"
            raise ValueError(msg)

        self._matcher = JobMatcher(self._profile)
        self._hand = await get_hand()

        browser = self._hand.browser_adapter
        if browser is None:
            msg = "Browser adapter not available"
            raise RuntimeError(msg)
        self._form_filler = FormFiller(browser)

        logger.info("JobApplyService initialized", user=self.user_id)

    async def process_job_url(
        self,
        url: str,
        *,
        auto_apply: bool = False,
        session_id: str | None = None,
    ) -> Job | None:
        """Process a job URL through the full pipeline."""
        session_id = session_id or f"job_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        self._memory = MemoryManager(session_id, self.user_id)

        logger.info("Extracting job", url=url)
        job = await self.extractor.extract_from_url(url)

        if not job:
            logger.error("Failed to extract job", url=url)
            return None

        await self._memory.record_observation(
            {"action": "job_extracted", "job_title": job.title, "company": job.company},
            source="extractor",
        )

        if self._matcher is None:
            msg = "Matcher not initialized"
            raise RuntimeError(msg)

        logger.info("Matching job", job_id=job.job_id, title=job.title)
        score, reasons, rejections = await self._matcher.match(job)
        job.update_match(score, reasons, min_score=self._min_score)

        await self._memory.record_observation(
            {"action": "job_matched", "score": score, "reasons": reasons},
            source="matcher",
        )

        if job.status == JobStatus.REJECTED:
            logger.info("Job rejected", job_id=job.job_id, reasons=rejections)
            return job

        logger.info("Job matched", job_id=job.job_id, score=score, title=job.title)

        if auto_apply and job.status == JobStatus.MATCHED:
            job.status = JobStatus.QUEUED
            result = await self.apply_to_job(job, session_id)
            if result.success:
                job.mark_applied(result.method)
            else:
                job.mark_failed(result.error or "Unknown error")

        await self._memory.save_experience(
            goal=f"Process job: {job.title} at {job.company}",
            actions=[
                {"action": "extract", "url": url},
                {"action": "match", "score": score},
                {"action": "apply" if auto_apply else "queue", "status": job.status.value},
            ],
            outcome=job.status.value,
            domain="job_apply",
        )

        return job

    async def apply_to_job(self, job: Job, session_id: str) -> ApplicationResult:
        """Apply to a specific job."""
        logger.info("Starting application", job_id=job.job_id, url=job.url)
        job.status = JobStatus.APPLYING

        await _emit_event(
            EventType.HAND_EXECUTION_STARTED,
            {"action": "apply", "job_id": job.job_id, "job_title": job.title},
        )

        try:
            result = await self._hand.execute(
                Capability.WEB_NAVIGATE,
                {"url": job.url},
                {"session_id": session_id, "domain": "job_apply"},
            )

            if not result.success:
                return ApplicationResult(
                    job_id=job.job_id,
                    success=False,
                    method="navigate",
                    error=result.error,
                )

            await self._hand.execute(
                Capability.WEB_SCREENSHOT,
                {},
                {"session_id": session_id, "domain": "job_apply"},
            )

            if "linkedin.com" in job.url:
                return await self._apply_linkedin(job, session_id)

            return await self._apply_generic(job, session_id)

        except Exception as exc:
            logger.exception("Application failed", job_id=job.job_id)
            return ApplicationResult(
                job_id=job.job_id,
                success=False,
                method="error",
                error=str(exc),
            )

    async def _apply_linkedin(self, job: Job, session_id: str) -> ApplicationResult:
        result = await self._hand.execute(
            Capability.WEB_CLICK,
            {"text": "Easy Apply"},
            {"session_id": session_id, "domain": "job_apply"},
        )

        if not result.success:
            result = await self._hand.execute(
                Capability.WEB_CLICK,
                {"text": "Apply"},
                {"session_id": session_id, "domain": "job_apply"},
            )

        if not result.success:
            return ApplicationResult(
                job_id=job.job_id,
                success=False,
                method="linkedin_easy_apply",
                error="Could not find Apply button",
            )

        if self._profile is None or self._form_filler is None:
            msg = "Profile or form filler not initialized"
            raise RuntimeError(msg)

        form_data = {
            "First name": self._profile.full_name.split()[0],
            "Last name": self._profile.full_name.split()[-1],
            "Email": self._profile.email,
            "Phone": self._profile.phone or "",
            "LinkedIn": self._profile.linkedin_url or "",
        }

        await self._form_filler.fill_form(form_data)

        if self._profile.resume_path:
            await self._hand.execute(
                Capability.WEB_UPLOAD,
                {
                    "selector": "input[type='file']",
                    "file_path": str(self._profile.resume_path),
                },
                {"session_id": session_id, "domain": "job_apply"},
            )

        submit_result = await self._hand.execute(
            Capability.WEB_CLICK,
            {"text": "Submit application"},
            {"session_id": session_id, "domain": "job_apply"},
        )

        final_screenshot = await self._hand.execute(
            Capability.WEB_SCREENSHOT,
            {},
            {"session_id": session_id, "domain": "job_apply"},
        )

        return ApplicationResult(
            job_id=job.job_id,
            success=submit_result.success,
            method="linkedin_easy_apply",
            screenshot_ref=final_screenshot.screenshot_ref if final_screenshot.success else None,
            error=submit_result.error if not submit_result.success else None,
        )

    async def _apply_generic(
        self, job: Job, session_id: str,  # noqa: ARG002
    ) -> ApplicationResult:
        if self._profile is None or self._form_filler is None:
            msg = "Profile or form filler not initialized"
            raise RuntimeError(msg)

        form_data = self._profile.to_dict_for_llm()
        fill_result = await self._form_filler.fill_form(form_data)

        return ApplicationResult(
            job_id=job.job_id,
            success=fill_result.success,
            method="form_fill",
            error=fill_result.error,
        )


async def _emit_event(event_type: EventType, payload: dict) -> None:
    try:
        await EventEmitter.emit(event_type, payload)
    except RuntimeError as exc:
        logger.debug("Event context not initialized", error=str(exc))
