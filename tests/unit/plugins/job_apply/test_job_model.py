from aria.plugins.job_apply.models.job import Job, JobStatus, SalaryInfo


def test_salary_info_str() -> None:
    salary = SalaryInfo(min_amount=50000, max_amount=70000, currency="USD")
    assert "50,000" in str(salary)

    salary = SalaryInfo(min_amount=80000, max_amount=None, currency="USD")
    assert "80,000" in str(salary)


def test_job_update_match_sets_status() -> None:
    job = Job(url="https://example.com", title="Engineer", company="Acme")
    job.update_match(80, ["fit"], min_score=70)
    assert job.status == JobStatus.MATCHED

    job.update_match(40, ["low"], min_score=70)
    assert job.status == JobStatus.REJECTED


def test_job_mark_applied_and_failed() -> None:
    job = Job(url="https://example.com", title="Engineer", company="Acme")
    job.mark_applied(method="auto")
    assert job.status == JobStatus.APPLIED
    assert job.application_method == "auto"
    assert job.applied_at is not None

    job.mark_failed("form error")
    assert job.status == JobStatus.FAILED
    assert "form error" in job.rejection_reasons
