"""Job extractor using Crawl4AI."""

from __future__ import annotations

import json
from datetime import datetime
from uuid import uuid4

from aria.core.llm import Message, ModelRole, get_llm_client
from aria.plugins.job_apply.models.job import Job, JobSource, JobStatus, SalaryInfo
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class JobExtractor:
    """Extract job information from URLs using Crawl4AI."""

    def __init__(self) -> None:
        """Initialize the job extractor."""
        self.llm = get_llm_client()
        self._crawler = None

    async def _get_crawler(self) -> AsyncWebCrawler:  # noqa: F821
        if self._crawler is None:
            from crawl4ai import AsyncWebCrawler, BrowserConfig  # noqa: PLC0415

            browser_config = BrowserConfig(headless=True, verbose=False)
            self._crawler = AsyncWebCrawler(config=browser_config)
        return self._crawler

    async def extract_from_url(self, url: str) -> Job | None:
        """Extract job information from a URL."""
        logger.info("Extracting job from URL", url=url)

        try:
            crawler = await self._get_crawler()
            from crawl4ai import CrawlerRunConfig  # noqa: PLC0415

            async with crawler:
                result = await crawler.arun(
                    url=url,
                    config=CrawlerRunConfig(
                        word_count_threshold=100,
                        remove_overlay_elements=True,
                    ),
                )

            if not result.success:
                logger.error("Crawl failed", url=url, error=result.error_message)
                return None

            job_data = await self._extract_with_llm(result.markdown, url)
        except Exception:
            logger.exception("Job extraction failed", url=url)
            return None
        else:
            if job_data:
                return self._create_job(job_data, url, result.markdown)
            return None

    async def _extract_with_llm(self, markdown: str, url: str) -> dict | None:
        prompt = (
            "Extract job posting information from this content.\n\n"
            f"URL: {url}\n\n"
            f"Content:\n{markdown[:8000]}\n\n"
            "Output JSON with these fields:\n"
            "{\n"
            '  "title": "Job Title",\n'
            '  "company": "Company Name",\n'
            '  "location": "City, State or Remote",\n'
            '  "job_type": "Full-time/Part-time/Contract",\n'
            '  "experience_level": "Entry/Mid/Senior/Lead",\n'
            '  "description": "Brief description",\n'
            '  "requirements": ["req1", "req2"],\n'
            '  "responsibilities": ["resp1", "resp2"],\n'
            '  "benefits": ["benefit1"],\n'
            '  "salary_min": null or number,\n'
            '  "salary_max": null or number,\n'
            '  "salary_currency": "USD",\n'
            '  "posted_date": "YYYY-MM-DD or null",\n'
            '  "application_deadline": "YYYY-MM-DD or null",\n'
            '  "industry": "Technology/Finance/etc"\n'
            "}\n"
        )

        response = await self.llm.generate(
            [Message(role="user", content=prompt)],
            role=ModelRole.BRAIN,
            temperature=0.1,
            max_tokens=1500,
        )

        try:
            json_start = response.content.find("{")
            json_end = response.content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response.content[json_start:json_end])
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON")
        return None

    def _create_job(self, data: dict, url: str, raw_content: str) -> Job:
        source = JobSource.OTHER
        if "linkedin.com" in url:
            source = JobSource.LINKEDIN
        elif "indeed.com" in url:
            source = JobSource.INDEED
        elif "glassdoor.com" in url:
            source = JobSource.GLASSDOOR

        salary = None
        if data.get("salary_min") or data.get("salary_max"):
            salary = SalaryInfo(
                min_amount=data.get("salary_min"),
                max_amount=data.get("salary_max"),
                currency=data.get("salary_currency", "USD"),
            )

        posted_date = _parse_date(data.get("posted_date"))
        deadline = _parse_date(data.get("application_deadline"))

        return Job(
            job_id=str(uuid4()),
            url=url,
            title=data.get("title", "Unknown"),
            company=data.get("company", "Unknown"),
            location=data.get("location"),
            description=data.get("description", ""),
            requirements=data.get("requirements", []),
            responsibilities=data.get("responsibilities", []),
            benefits=data.get("benefits", []),
            job_type=data.get("job_type"),
            experience_level=data.get("experience_level"),
            industry=data.get("industry"),
            salary=salary,
            source=source,
            posted_date=posted_date,
            application_deadline=deadline,
            status=JobStatus.EXTRACTED,
            raw_data={"url": url, "markdown_preview": raw_content[:1000]},
        )

    async def extract_from_search_results(
        self,
        search_url: str,
        max_jobs: int = 10,
    ) -> list[Job]:
        """Extract multiple jobs from search results page.

        Crawls a job search results page, extracts job listing URLs,
        and then extracts details from each job page.

        Args:
            search_url: URL of job search results page
            max_jobs: Maximum number of jobs to extract

        Returns:
            List of extracted Job objects

        """
        logger.info(
            "Extracting jobs from search results",
            url=search_url,
            max_jobs=max_jobs,
        )

        try:
            crawler = await self._get_crawler()
            from crawl4ai import CrawlerRunConfig  # noqa: PLC0415

            async with crawler:
                result = await crawler.arun(
                    url=search_url,
                    config=CrawlerRunConfig(
                        word_count_threshold=50,
                        remove_overlay_elements=True,
                    ),
                )

            if not result.success:
                logger.error(
                    "Search results crawl failed",
                    url=search_url,
                    error=result.error_message,
                )
                return []

            # Extract job URLs using LLM
            job_urls = await self._extract_job_urls(
                result.markdown,
                search_url,
                max_jobs,
            )

            if not job_urls:
                logger.warning("No job URLs found in search results", url=search_url)
                return []

            logger.info(
                "Found job URLs in search results",
                count=len(job_urls),
                url=search_url,
            )

            # Extract each job
            jobs: list[Job] = []
            for url in job_urls[:max_jobs]:
                try:
                    job = await self.extract_from_url(url)
                    if job:
                        jobs.append(job)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Failed to extract job",
                        url=url,
                        error=str(exc),
                    )

            logger.info(
                "Extracted jobs from search results",
                total=len(jobs),
                url=search_url,
            )
            return jobs

        except Exception:
            logger.exception("Search results extraction failed", url=search_url)
            return []

    async def _extract_job_urls(
        self,
        markdown: str,
        base_url: str,
        max_urls: int,
    ) -> list[str]:
        """Extract job posting URLs from search results markdown.

        Args:
            markdown: Markdown content from search results page
            base_url: Base URL for resolving relative links
            max_urls: Maximum URLs to extract

        Returns:
            List of job posting URLs

        """
        prompt = (
            "Extract job posting URLs from this search results page.\n\n"
            f"Base URL: {base_url}\n\n"
            f"Content:\n{markdown[:10000]}\n\n"
            f"Find up to {max_urls} job listing URLs. "
            "Look for links that lead to individual job postings.\n"
            "For LinkedIn: look for /jobs/view/ URLs\n"
            "For Indeed: look for /viewjob or /rc/clk URLs\n"
            "For Glassdoor: look for /job-listing/ URLs\n\n"
            "Output ONLY a JSON array of absolute URLs:\n"
            '["https://...", "https://..."]\n'
        )

        try:
            response = await self.llm.generate(
                [Message(role="user", content=prompt)],
                role=ModelRole.BRAIN,
                temperature=0.1,
                max_tokens=2000,
            )

            # Parse JSON array from response
            content = response.content.strip()
            json_start = content.find("[")
            json_end = content.rfind("]") + 1

            if json_start >= 0 and json_end > json_start:
                urls = json.loads(content[json_start:json_end])
                # Filter valid URLs
                return [
                    url for url in urls
                    if isinstance(url, str) and url.startswith("http")
                ][:max_urls]

        except (json.JSONDecodeError, Exception) as exc:  # noqa: BLE001
            logger.warning("Failed to parse job URLs", error=str(exc))

        return []


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
