"""Jobs page - Job management and application tracking."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import streamlit as st

from aria.config import get_settings
from aria.ui.i18n import format_number, t

logger = logging.getLogger(__name__)


def _load_jobs() -> list[dict[str, Any]]:
    """Load jobs from API or local storage.

    Returns:
        List of job dictionaries

    """
    # Try API first
    try:
        from aria.ui.services.api_client import APIClient

        client = APIClient()
        jobs = client.get_jobs()

        if jobs and not isinstance(jobs, dict):  # Not an error response
            return jobs
    except Exception as exc:
        logger.debug("Failed to load jobs from API", exc_info=exc)

    # Fallback to local storage
    return _load_jobs_local()


def _load_jobs_local() -> list[dict[str, Any]]:
    """Load jobs from local storage.

    Returns:
        List of job dictionaries

    """
    try:
        from aria.plugins.job_apply.models.job import Job

        jobs_dir = Path(get_settings().job_apply.jobs_dir)
        jobs_dir.mkdir(parents=True, exist_ok=True)

        jobs: list[dict[str, Any]] = []

        for path in jobs_dir.glob("*.json"):
            try:
                job = Job.model_validate_json(path.read_text(encoding="utf-8"))
                jobs.append({
                    "job_id": job.job_id,
                    "title": job.title,
                    "company": job.company,
                    "location": getattr(job, "location", "Remote"),
                    "status": job.status.value if hasattr(job.status, "value") else str(job.status),
                    "match_score": getattr(job, "match_score", 0),
                    "applied_at": getattr(job, "applied_at", None),
                    "url": getattr(job, "url", ""),
                })
            except Exception as exc:  # noqa: BLE001
                logger.debug("Failed to parse job file", extra={"path": str(path), "error": str(exc)})

        return jobs

    except ImportError:
        # Return mock data if Job model not available
        return _get_mock_jobs()


def _extract_job(url: str) -> dict[str, Any]:
    """Extract job information from URL.

    Args:
        url: Job posting URL

    Returns:
        Extracted job data or error dict

    """
    try:
        from aria.ui.services.api_client import APIClient

        client = APIClient()
        result = client.extract_job(url)
        return result
    except Exception as exc:
        logger.error("Failed to extract job", exc_info=exc)
        return {"error": str(exc)}


def _get_mock_jobs() -> list[dict[str, Any]]:
    """Get mock job data for demonstration."""
    now = datetime.now(tz=UTC)
    return [
        {
            "job_id": "job_001",
            "title": "Senior Python Developer",
            "company": "TechCorp",
            "location": "San Francisco, CA",
            "status": "applied",
            "match_score": 92,
            "applied_at": now,
            "url": "https://example.com/job/001",
        },
        {
            "job_id": "job_002",
            "title": "ML Engineer",
            "company": "AI Startup",
            "location": "Remote",
            "status": "matched",
            "match_score": 85,
            "applied_at": None,
            "url": "https://example.com/job/002",
        },
        {
            "job_id": "job_003",
            "title": "Backend Engineer",
            "company": "BigTech Inc",
            "location": "New York, NY",
            "status": "interview",
            "match_score": 88,
            "applied_at": now,
            "url": "https://example.com/job/003",
        },
    ]


def _render_job_card(job: dict[str, Any]) -> None:
    """Render a single job card."""
    status = job.get("status", "new")
    match_score = job.get("match_score", 0)

    # Status styling
    status_config = {
        "new": ("🆕", "var(--color-info)"),
        "matched": ("🎯", "var(--color-accent-primary)"),
        "applied": ("📤", "var(--color-success)"),
        "rejected": ("❌", "var(--color-error)"),
        "interview": ("🎉", "var(--color-accent-tertiary)"),
    }

    status_icon, status_color = status_config.get(status, ("📋", "var(--color-text-muted)"))

    # Match score color
    match_color = (
        "var(--color-success)" if match_score >= 80
        else "var(--color-warning)" if match_score >= 60
        else "var(--color-error)"
    )

    st.markdown(
        f"""
        <div style="
            background: var(--color-bg-card);
            border: 1px solid var(--color-border-light);
            border-radius: var(--radius-lg);
            padding: var(--space-4);
            margin-bottom: var(--space-3);
            transition: box-shadow 0.2s ease, transform 0.2s ease;
        ">
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: var(--space-2);
            ">
                <div>
                    <h4 style="margin: 0; color: var(--color-text-primary);">
                        {job.get('title', 'Unknown')}
                    </h4>
                    <p style="
                        margin: var(--space-1) 0 0 0;
                        color: var(--color-text-secondary);
                        font-size: var(--font-size-sm);
                    ">
                        🏢 {job.get('company', 'Unknown')} • 📍 {job.get('location', 'Unknown')}
                    </p>
                </div>
                <div style="
                    background: {match_color};
                    color: white;
                    padding: var(--space-1) var(--space-2);
                    border-radius: var(--radius-full);
                    font-size: var(--font-size-sm);
                    font-weight: 600;
                ">
                    {match_score}%
                </div>
            </div>
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: var(--space-3);
            ">
                <span style="
                    display: inline-flex;
                    align-items: center;
                    gap: var(--space-1);
                    color: {status_color};
                    font-size: var(--font-size-sm);
                    font-weight: 500;
                ">
                    {status_icon} {t(f'jobs.status.{status}')}
                </span>
                <span style="
                    font-size: var(--font-size-xs);
                    color: var(--color-text-muted);
                ">
                    ID: {job.get('job_id', 'N/A')[:8]}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Render the jobs page."""
    st.title(t("jobs.title"))
    st.caption(t("jobs.subtitle"))

    # Controls row
    col_search, col_filter, col_actions = st.columns([2, 1, 1])

    with col_search:
        search = st.text_input(
            t("jobs.search"),
            placeholder=t("jobs.search"),
            key="jobs_search",
            label_visibility="collapsed",
        )

    with col_filter:
        status_options = [
            t("jobs.status.all"),
            t("jobs.status.new"),
            t("jobs.status.matched"),
            t("jobs.status.applied"),
            t("jobs.status.interview"),
            t("jobs.status.rejected"),
        ]
        status_filter = st.selectbox(
            t("jobs.filter_status"),
            status_options,
            key="jobs_status_filter",
            label_visibility="collapsed",
        )

    with col_actions:
        col_add, col_refresh = st.columns(2)
        with col_add:
            if st.button("➕", help=t("jobs.add_url"), use_container_width=True):
                st.session_state.show_add_job = True
        with col_refresh:
            if st.button("🔄", help=t("jobs.refresh"), use_container_width=True):
                st.rerun()

    # Add job dialog
    if st.session_state.get("show_add_job"):
        with st.expander("➕ Add Job URL", expanded=True):
            job_url = st.text_input("Job URL", placeholder="https://...")
            col_extract, col_cancel = st.columns(2)

            with col_extract:
                if st.button("Extract Job", type="primary", use_container_width=True):
                    if job_url:
                        with st.spinner("Extracting job information..."):
                            result = _extract_job(job_url)
                            if result and not result.get("error"):
                                st.success(f"✅ Job added: {result.get('title', 'Unknown')}")
                                st.session_state.show_add_job = False
                                st.rerun()
                            else:
                                st.error(f"❌ Failed: {result.get('error', 'Unknown error')}")
                    else:
                        st.warning("Please enter a job URL")

            with col_cancel:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.show_add_job = False
                    st.rerun()

    st.divider()

    # Load jobs
    jobs = _load_jobs()

    # Filter jobs
    if search:
        search_lower = search.lower()
        jobs = [
            j for j in jobs
            if search_lower in j.get("title", "").lower()
            or search_lower in j.get("company", "").lower()
        ]

    # Map filter back to status
    status_map = {
        t("jobs.status.all"): None,
        t("jobs.status.new"): "new",
        t("jobs.status.matched"): "matched",
        t("jobs.status.applied"): "applied",
        t("jobs.status.interview"): "interview",
        t("jobs.status.rejected"): "rejected",
    }

    filter_status = status_map.get(status_filter)
    if filter_status:
        jobs = [j for j in jobs if j.get("status") == filter_status]

    # Display jobs
    if not jobs:
        st.markdown(
            f"""
            <div style="
                text-align: center;
                padding: var(--space-12) var(--space-6);
                color: var(--color-text-muted);
            ">
                <div style="font-size: 4rem; margin-bottom: var(--space-4);">💼</div>
                <h3 style="color: var(--color-text-secondary);">{t('jobs.no_jobs')}</h3>
                <p>{t('jobs.no_jobs_hint')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Stats
    st.markdown(
        f"""
        <div style="
            display: flex;
            gap: var(--space-4);
            margin-bottom: var(--space-4);
            font-size: var(--font-size-sm);
            color: var(--color-text-muted);
        ">
            <span>📊 {format_number(len(jobs))} jobs</span>
            <span>✅ {format_number(len([j for j in jobs if j.get('status') == 'applied']))} applied</span>
            <span>🎉 {format_number(len([j for j in jobs if j.get('status') == 'interview']))} interviews</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Job cards
    for job in jobs:
        _render_job_card(job)


if __name__ == "__main__":
    main()
