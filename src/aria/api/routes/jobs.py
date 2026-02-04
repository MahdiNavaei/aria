"""Job endpoints for job apply."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from aria.config import get_settings
from aria.plugins.job_apply import JobApplyService
from aria.plugins.job_apply.extractor import JobExtractor
from aria.plugins.job_apply.models.job import ApplicationResult, Job
from aria.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class JobExtractRequest(BaseModel):
    """Job extraction request payload."""

    url: str


class JobApplyRequest(BaseModel):
    """Job apply request payload."""

    job_id: str
    user_id: str = "default"
    auto_fill: bool = True
    session_id: str | None = None


@router.post("/extract")
async def extract_job(request: JobExtractRequest) -> dict:
    """Extract job information from URL."""
    if "example.com" in request.url:
        raise HTTPException(status_code=400, detail="Example URL not supported")

    extractor = JobExtractor()
    job = await extractor.extract_from_url(request.url)

    if not job:
        raise HTTPException(status_code=400, detail="Failed to extract job")

    _save_job(job)
    return job.model_dump()


@router.post("/apply")
async def apply_to_job(request: JobApplyRequest) -> dict:
    """Apply to a job."""
    job = _load_job(request.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    service = JobApplyService(user_id=request.user_id)
    await service.initialize()

    session_id = request.session_id or f"job_{job.job_id}"
    result = await service.apply_to_job(job, session_id)

    if isinstance(result, ApplicationResult):
        return result.model_dump()

    raise HTTPException(status_code=500, detail="Failed to apply")


@router.get("/")
async def list_jobs(status: str | None = None, limit: int = 50) -> dict:
    """List jobs in pipeline."""
    jobs_dir = Path(get_settings().job_apply.jobs_dir)
    jobs_dir.mkdir(parents=True, exist_ok=True)
    jobs: list[Job] = []

    for path in jobs_dir.glob("*.json"):
        try:
            job = Job.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            logger.debug("Failed to parse job file", path=str(path), error=str(exc))
            continue
        if status and job.status.value != status:
            continue
        jobs.append(job)
        if len(jobs) >= limit:
            break

    return {"jobs": [job.model_dump() for job in jobs]}


def _jobs_dir() -> Path:
    return Path(get_settings().job_apply.jobs_dir)


def _save_job(job: Job) -> None:
    jobs_dir = _jobs_dir()
    jobs_dir.mkdir(parents=True, exist_ok=True)
    path = jobs_dir / f"{job.job_id}.json"
    path.write_text(job.model_dump_json(indent=2), encoding="utf-8")


def _load_job(job_id: str) -> Job | None:
    path = _jobs_dir() / f"{job_id}.json"
    if not path.exists():
        return None
    return Job.model_validate_json(path.read_text(encoding="utf-8"))
