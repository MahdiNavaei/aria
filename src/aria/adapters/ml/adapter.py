"""ML capability adapter for Hand."""

from __future__ import annotations

import json
from typing import Any

from aria.core.hand.capability import (
    Capability,
    CapabilityAdapter,
    CapabilityCategory,
    CapabilityResult,
    ExecutionContext,
)
from aria.core.llm import Message, ModelRole, get_llm_client
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class MLAdapter(CapabilityAdapter):
    """ML capabilities adapter."""

    def __init__(self) -> None:
        """Initialize ML adapter with LLM client."""
        self.llm = get_llm_client()

    @property
    def category(self) -> CapabilityCategory:
        """Return capability category."""
        return CapabilityCategory.ML

    @property
    def capabilities(self) -> list[Capability]:
        """Return list of supported capabilities."""
        return [
            Capability.ML_MATCH_JOB,
            Capability.ML_GENERATE_COVER_LETTER,
            Capability.ML_EXTRACT_JOB_INFO,
        ]

    async def initialize(self) -> None:
        """Initialize ML adapter (no-op)."""

    async def cleanup(self) -> None:
        """Cleanup ML adapter (no-op)."""

    async def execute(
        self,
        capability: Capability,
        parameters: dict[str, Any],
        context: ExecutionContext,  # noqa: ARG002
    ) -> CapabilityResult:
        """Execute ML capability."""
        try:
            if capability == Capability.ML_MATCH_JOB:
                return await self._match_job(parameters)
            if capability == Capability.ML_GENERATE_COVER_LETTER:
                return await self._generate_cover_letter(parameters)
            if capability == Capability.ML_EXTRACT_JOB_INFO:
                return await self._extract_job_info(parameters)
            return CapabilityResult.fail(f"Unknown capability: {capability}")
        except Exception as exc:
            logger.exception("ML execution failed")
            return CapabilityResult.fail(str(exc))

    async def _match_job(self, params: dict[str, Any]) -> CapabilityResult:
        job_data = params.get("job_data", {})
        profile = params.get("profile", {})

        prompt = (
            "Analyze this job posting and user profile.\n\n"
            f"Job:\nTitle: {job_data.get('title', 'Unknown')}\n"
            f"Company: {job_data.get('company', 'Unknown')}\n"
            f"Description: {job_data.get('description', '')[:2000]}\n"
            f"Requirements: {job_data.get('requirements', [])}\n\n"
            "Profile:\n"
            f"Skills: {profile.get('skills', [])}\n"
            f"Experience: {profile.get('experience_years', 0)} years\n"
            f"Preferences: {profile.get('preferences', {})}\n\n"
            'Rate the match from 0-100 and explain why.\n'
            'Output JSON: {"score": 85, "reasons": ["..."], "missing": ["..."]}'
        )

        response = await self.llm.generate(
            [Message(role="user", content=prompt)],
            role=ModelRole.BRAIN,
            temperature=0.3,
        )

        result = _parse_json_response(response.content, fallback={"score": 50})
        return CapabilityResult.ok(result)

    async def _generate_cover_letter(self, params: dict[str, Any]) -> CapabilityResult:
        job_data = params.get("job_data", {})
        profile = params.get("profile", {})
        style = params.get("style", "professional")

        prompt = (
            f"Write a {style} cover letter for this job application.\n\n"
            "Job:\n"
            f"Title: {job_data.get('title')}\n"
            f"Company: {job_data.get('company')}\n"
            f"Key Requirements: {job_data.get('requirements', [])}\n\n"
            "Applicant:\n"
            f"Name: {profile.get('name')}\n"
            f"Experience: {profile.get('experience_summary', '')}\n"
            f"Key Skills: {profile.get('skills', [])}\n\n"
            "Write a compelling cover letter (3-4 paragraphs) that:\n"
            "1. Shows enthusiasm for the role\n"
            "2. Highlights relevant experience\n"
            "3. Addresses key requirements\n"
            "4. Includes a strong closing"
        )

        response = await self.llm.generate(
            [Message(role="user", content=prompt)],
            role=ModelRole.BRAIN,
            temperature=0.7,
        )

        return CapabilityResult.ok(
            {
                "cover_letter": response.content,
                "word_count": len(response.content.split()),
            },
        )

    async def _extract_job_info(self, params: dict[str, Any]) -> CapabilityResult:
        text = params.get("text", "")
        url = params.get("url", "")

        if url and not text:
            try:
                from crawl4ai import AsyncWebCrawler  # noqa: PLC0415

                async with AsyncWebCrawler() as crawler:
                    result = await crawler.arun(url=url)
                    text = result.markdown
            except Exception as exc:  # noqa: BLE001
                logger.warning("Crawl4AI failed", error=str(exc))

        prompt = (
            "Extract job information from this posting:\n\n"
            f"{text[:4000]}\n\n"
            "Output JSON:\n"
            "{\n"
            '  "title": "Job Title",\n'
            '  "company": "Company Name",\n'
            '  "location": "City, State or Remote",\n'
            '  "salary_range": "if mentioned",\n'
            '  "job_type": "Full-time/Part-time/Contract",\n'
            '  "experience_required": "X years",\n'
            '  "skills_required": ["skill1", "skill2"],\n'
            '  "responsibilities": ["resp1", "resp2"],\n'
            '  "benefits": ["benefit1"],\n'
            '  "application_deadline": "if mentioned"\n'
            "}\n"
        )

        response = await self.llm.generate(
            [Message(role="user", content=prompt)],
            role=ModelRole.BRAIN,
            temperature=0.1,
        )

        result = _parse_json_response(response.content, fallback={"raw": response.content})
        return CapabilityResult.ok(result)


def _parse_json_response(content: str, fallback: dict[str, Any]) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return fallback
