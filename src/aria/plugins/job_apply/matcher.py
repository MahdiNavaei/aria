"""Job matcher for job apply plugin."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from aria.core.llm import Message, ModelRole, get_llm_client
from aria.plugins.job_apply.models.job import Job, JobStatus
from aria.utils.logging import get_logger

if TYPE_CHECKING:
    from aria.plugins.job_apply.models.profile import UserProfile

logger = get_logger(__name__)

MIN_WORD_LENGTH = 3


class JobMatcher:
    """Match jobs to user profile."""

    def __init__(self, profile: UserProfile) -> None:
        """Initialize matcher with user profile."""
        self.profile = profile
        self.llm = get_llm_client()

    async def match(self, job: Job) -> tuple[float, list[str], list[str]]:
        """Match job to profile and return score, reasons, and rejections."""
        rejection_reasons: list[str] = []
        match_reasons: list[str] = []

        passed, reasons = self._apply_hard_filters(job)
        if not passed:
            return 0, [], reasons

        skill_score, skill_reasons = self._match_skills(job)
        match_reasons.extend(skill_reasons)

        exp_score = self._match_experience_level(job)

        llm_score, llm_reasons = await self._llm_match(job)
        match_reasons.extend(llm_reasons)

        final_score = skill_score * 0.35 + exp_score * 0.25 + llm_score * 0.40
        return final_score, match_reasons, rejection_reasons

    def _apply_hard_filters(self, job: Job) -> tuple[bool, list[str]]:
        reasons: list[str] = []
        prefs = self.profile.preferences

        if job.company.lower() in [item.lower() for item in prefs.excluded_companies]:
            reasons.append(f"Company '{job.company}' is in exclusion list")
            return False, reasons

        if (
            job.salary
            and prefs.min_salary
            and job.salary.max_amount
            and job.salary.max_amount < prefs.min_salary
        ):
            reasons.append(f"Salary below minimum ({job.salary} vs {prefs.min_salary}+)")
            return False, reasons

        if job.location:
            location_lower = job.location.lower()
            is_remote = "remote" in location_lower
            is_hybrid = "hybrid" in location_lower

            if is_remote and not prefs.remote_ok:
                reasons.append("Remote position but remote not preferred")
                return False, reasons
            if not is_remote and not is_hybrid and not prefs.on_site_ok:
                reasons.append("On-site position but on-site not preferred")
                return False, reasons

        job_text = f"{job.title} {job.description}".lower()
        for keyword in prefs.exclude_keywords:
            if keyword.lower() in job_text:
                reasons.append(f"Contains excluded keyword: {keyword}")
                return False, reasons

        return True, []

    def _match_skills(self, job: Job) -> tuple[float, list[str]]:
        user_skills = {skill.lower() for skill in self.profile.skills}
        job_skills = set()

        for req in job.requirements:
            job_skills.update(word.lower() for word in req.split() if len(word) >= MIN_WORD_LENGTH)

        matched = user_skills & job_skills

        if not job_skills:
            return 70, ["No specific skills mentioned in job"]

        match_ratio = len(matched) / len(job_skills)
        score = min(100, match_ratio * 100 + 20)

        reasons = []
        if matched:
            reasons.append(f"Matching skills: {', '.join(list(matched)[:5])}")

        return score, reasons

    def _match_experience_level(self, job: Job) -> float:
        if not job.experience_level:
            return 70

        job_level = job.experience_level.lower()
        user_level = self.profile.experience_level

        level_map = {
            "entry": 1,
            "junior": 2,
            "mid": 3,
            "senior": 4,
            "lead": 5,
            "executive": 6,
        }

        user_num = level_map.get(user_level.value, 3)
        job_num = 3
        for level, num in level_map.items():
            if level in job_level:
                job_num = num
                break

        diff = abs(user_num - job_num)
        if diff == 0:
            return 100
        if diff == 1:
            return 80
        if diff == 2:  # noqa: PLR2004
            return 50
        return 20

    async def _llm_match(self, job: Job) -> tuple[float, list[str]]:
        prompt = (
            "Rate how well this job matches this candidate profile.\n\n"
            f"JOB:\nTitle: {job.title}\nCompany: {job.company}\n"
            f"Description: {job.description[:1000]}\n"
            f"Requirements: {job.requirements[:5]}\n\n"
            "CANDIDATE:\n"
            f"Headline: {self.profile.headline}\n"
            f"Skills: {self.profile.primary_skills or self.profile.skills[:10]}\n"
            f"Experience: {self.profile.experience_summary}\n"
            f"Looking for: {self.profile.preferences.titles}\n\n"
            "Output JSON:\n"
            "{\n"
            '  "score": 0-100,\n'
            '  "reasons": ["reason1", "reason2"],\n'
            '  "concerns": ["concern1"]\n'
            "}\n"
        )

        response = await self.llm.generate(
            [Message(role="user", content=prompt)],
            role=ModelRole.BRAIN,
            temperature=0.3,
            max_tokens=500,
        )

        try:
            result = json.loads(response.content)
            return float(result.get("score", 50)), result.get("reasons", [])
        except (json.JSONDecodeError, TypeError, ValueError):
            return 50, []

    async def filter_and_rank(self, jobs: list[Job]) -> list[Job]:
        """Filter and rank jobs by match score."""
        results: list[Job] = []
        for job in jobs:
            score, match_reasons, _ = await self.match(job)
            job.update_match(score, match_reasons)
            if job.status == JobStatus.MATCHED:
                results.append(job)
        results.sort(key=lambda item: item.match_score or 0, reverse=True)
        return results
