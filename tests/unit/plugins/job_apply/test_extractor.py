from datetime import datetime

from aria.plugins.job_apply.extractor import JobExtractor, _parse_date
from aria.plugins.job_apply.models.job import JobSource, JobStatus


def test_parse_date_valid_and_invalid() -> None:
    assert _parse_date("2024-01-10") == datetime.fromisoformat("2024-01-10")
    assert _parse_date("not-a-date") is None


def test_create_job_sets_source_and_salary() -> None:
    extractor = JobExtractor()
    data = {
        "title": "Engineer",
        "company": "Acme",
        "salary_min": 50000,
        "salary_max": 70000,
        "salary_currency": "USD",
    }

    job = extractor._create_job(data, "https://linkedin.com/jobs/123", "raw")

    assert job.source == JobSource.LINKEDIN
    assert job.salary is not None
    assert job.status == JobStatus.EXTRACTED
