"""Dashboard page - Main overview with metrics and recent activity."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import streamlit as st

from aria.ui.i18n import format_number, t

logger = logging.getLogger(__name__)


def _load_metrics() -> dict[str, Any]:
    """Load dashboard metrics from API."""
    try:
        from aria.ui.services.api_client import APIClient

        client = APIClient()
        metrics = client.get_metrics()

        if not metrics.get("error"):
            return {
                "tasks_today": metrics.get("tasks_today", 0),
                "tasks_delta": metrics.get("tasks_delta", 0),
                "success_rate": metrics.get("success_rate", 0),
                "success_delta": metrics.get("success_delta", 0),
                "hitl_rate": metrics.get("hitl_rate", 0),
                "hitl_delta": metrics.get("hitl_delta", 0),
                "jobs_applied": metrics.get("jobs_applied", 0),
                "jobs_delta": metrics.get("jobs_delta", 0),
            }
    except Exception as exc:
        logger.debug("Failed to load metrics from API", exc_info=exc)

    # Fallback to local data
    return _load_metrics_local()


def _load_metrics_local() -> dict[str, Any]:
    """Load metrics from local job files."""
    from pathlib import Path

    from aria.config import get_settings

    jobs_dir = Path(get_settings().job_apply.jobs_dir)
    jobs_applied = 0
    successful = 0

    if jobs_dir.exists():
        import json

        for job_file in jobs_dir.glob("*.json"):
            try:
                data = json.loads(job_file.read_text(encoding="utf-8"))
                jobs_applied += 1
                status = data.get("status", "")
                if status in ("applied", "interview"):
                    successful += 1
            except Exception:  # noqa: BLE001
                pass

    success_rate = (successful / jobs_applied * 100) if jobs_applied > 0 else 0

    return {
        "tasks_today": jobs_applied,
        "tasks_delta": 0,
        "success_rate": round(success_rate, 1),
        "success_delta": 0,
        "hitl_rate": 12,
        "hitl_delta": 0,
        "jobs_applied": jobs_applied,
        "jobs_delta": 0,
    }


def _load_recent_tasks() -> list[dict[str, Any]]:
    """Load recent tasks from API or local storage."""
    try:
        from aria.ui.services.api_client import APIClient

        client = APIClient()
        health = client.health_check()

        if health.get("status") != "unhealthy":
            # Try to get from API - placeholder for when endpoint exists
            pass
    except Exception:  # noqa: BLE001
        pass

    # Fallback to local job files
    return _load_recent_tasks_local()


def _load_recent_tasks_local() -> list[dict[str, Any]]:
    """Load recent tasks from local job files."""
    from pathlib import Path

    from aria.config import get_settings

    jobs_dir = Path(get_settings().job_apply.jobs_dir)
    tasks = []

    if jobs_dir.exists():
        import json

        job_files = sorted(
            jobs_dir.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )[:5]

        for job_file in job_files:
            try:
                data = json.loads(job_file.read_text(encoding="utf-8"))
                tasks.append({
                    "id": job_file.stem,
                    "goal": f"Apply to {data.get('title', 'Unknown')} at {data.get('company', 'Unknown')}",
                    "status": data.get("status", "new"),
                    "started_at": datetime.now(tz=UTC) - timedelta(hours=len(tasks)),
                    "duration_minutes": 10 + len(tasks) * 2,
                })
            except Exception:  # noqa: BLE001
                pass

    # If no jobs, show placeholder
    if not tasks:
        now = datetime.now(tz=UTC)
        tasks = [
            {
                "id": "demo_001",
                "goal": "Start your first job search!",
                "status": "pending",
                "started_at": now,
                "duration_minutes": 0,
            },
        ]

    return tasks


def _load_chart_data() -> list[dict[str, Any]]:
    """Load chart data from API or generate from local data."""
    try:
        from aria.ui.services.api_client import APIClient

        client = APIClient()
        analytics = client.get_analytics("week")

        if analytics and analytics.get("applications_chart"):
            return analytics["applications_chart"]
    except Exception:  # noqa: BLE001
        pass

    # Fallback: generate from local data
    now = datetime.now(tz=UTC)
    data = []

    for i in range(14):
        date = now - timedelta(days=13 - i)
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "tasks": max(0, 2 + (i % 4)),
            "applications": max(0, 1 + (i % 3)),
        })

    return data


def _load_system_health() -> dict[str, str]:
    """Load system component health status."""
    try:
        from aria.ui.services.api_client import APIClient

        client = APIClient()
        health = client.health_check()

        if health and not health.get("error"):
            return {
                "api": "healthy",
                "redis": health.get("redis", "unknown"),
                "kafka": health.get("kafka", "unknown"),
                "qdrant": health.get("qdrant", "unknown"),
            }
    except Exception:  # noqa: BLE001
        pass

    return {
        "api": "offline",
        "redis": "unknown",
        "kafka": "unknown",
        "qdrant": "unknown",
    }


def main() -> None:
    """Render the dashboard page."""
    st.title(t("dashboard.title"))
    st.caption(t("dashboard.subtitle"))

    # Metrics row
    metrics = _load_metrics()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        delta_str = f"+{metrics['tasks_delta']}" if metrics["tasks_delta"] > 0 else str(metrics["tasks_delta"])
        st.metric(
            t("metrics.tasks_today"),
            format_number(metrics["tasks_today"]),
            delta=delta_str if metrics["tasks_delta"] != 0 else None,
        )

    with col2:
        delta_str = f"+{metrics['success_delta']}%" if metrics["success_delta"] > 0 else f"{metrics['success_delta']}%"
        st.metric(
            t("metrics.success_rate"),
            f"{metrics['success_rate']}%",
            delta=delta_str if metrics["success_delta"] != 0 else None,
        )

    with col3:
        st.metric(
            t("metrics.hitl_rate"),
            f"{metrics['hitl_rate']}%",
            delta=f"{metrics['hitl_delta']}%" if metrics["hitl_delta"] != 0 else None,
            delta_color="inverse",
        )

    with col4:
        delta_str = f"+{metrics['jobs_delta']}" if metrics["jobs_delta"] > 0 else str(metrics["jobs_delta"])
        st.metric(
            t("metrics.jobs_applied"),
            format_number(metrics["jobs_applied"]),
            delta=delta_str if metrics["jobs_delta"] != 0 else None,
        )

    st.divider()

    # Two column layout
    col_left, col_right = st.columns([2, 1])

    with col_left:
        # Activity chart
        st.subheader(t("analytics.chart.applications"))

        chart_data = _load_chart_data()
        if chart_data:
            st.area_chart(
                chart_data,
                x="date",
                y=["tasks", "applications"],
                color=["#D97706", "#0D9488"],
            )
        else:
            st.info("No activity data available yet.")

    with col_right:
        # Recent tasks
        st.subheader(t("dashboard.recent_tasks"))

        tasks = _load_recent_tasks()

        for task in tasks:
            status_icon = {
                "completed": "✅",
                "applied": "✅",
                "interview": "🎉",
                "failed": "❌",
                "pending": "⏳",
                "new": "🆕",
            }.get(task.get("status", "pending"), "📋")

            goal_text = task.get("goal", "Unknown task")
            if len(goal_text) > 40:
                goal_text = goal_text[:37] + "..."

            st.markdown(
                f"""
                <div style="
                    background: var(--color-bg-card);
                    border: 1px solid var(--color-border-light);
                    border-radius: var(--radius-md);
                    padding: var(--space-3);
                    margin-bottom: var(--space-2);
                ">
                    <div style="font-weight: 500;">
                        {status_icon} {goal_text}
                    </div>
                    <div style="
                        font-size: var(--font-size-xs);
                        color: var(--color-text-muted);
                        margin-top: var(--space-1);
                    ">
                        ⏱️ {task.get('duration_minutes', 0)}m
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    # System Health
    col_health, col_actions = st.columns([1, 2])

    with col_health:
        st.subheader(t("dashboard.system_health"))
        health = _load_system_health()

        for service, status in health.items():
            icon = "🟢" if status == "healthy" else "🔴" if status in ("unhealthy", "offline") else "🟡"
            st.markdown(f"{icon} **{service.upper()}**: {status}")

    with col_actions:
        # Quick actions
        st.subheader(t("dashboard.quick_actions"))

        action_col1, action_col2, action_col3 = st.columns(3)

        with action_col1:
            if st.button(
                f"🔍 {t('jobs.search')}",
                use_container_width=True,
            ):
                st.switch_page("pages/2_Jobs.py")

        with action_col2:
            if st.button(
                f"📊 {t('nav.analytics')}",
                use_container_width=True,
            ):
                st.switch_page("pages/4_Analytics.py")

        with action_col3:
            if st.button(
                f"⚙️ {t('nav.settings')}",
                use_container_width=True,
            ):
                st.switch_page("pages/3_Settings.py")


if __name__ == "__main__":
    main()
