"""Metrics endpoints for dashboard."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from aria.adapters.redis import get_state_store
from aria.config import get_settings
from aria.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class DashboardMetrics(BaseModel):
    """Dashboard metrics response."""

    tasks_today: int = 0
    tasks_delta: int = 0
    success_rate: float = 0.0
    success_delta: float = 0.0
    hitl_rate: float = 0.0
    hitl_delta: float = 0.0
    jobs_applied: int = 0
    jobs_delta: int = 0
    time_saved_minutes: int = 0


class SystemHealth(BaseModel):
    """System health status."""

    redis: str = "unknown"
    kafka: str = "unknown"
    qdrant: str = "unknown"
    api: str = "healthy"


@router.get("/", response_model=DashboardMetrics)
async def get_metrics() -> DashboardMetrics:
    """Get dashboard metrics."""
    store = await _safe_state_store()

    # Try to get metrics from state store
    if store:
        try:
            metrics = await store.get("metrics:dashboard")
            if metrics:
                return DashboardMetrics(**metrics)
        except Exception as exc:
            logger.debug("Failed to get metrics from store", error=str(exc))

    # Calculate metrics from jobs directory
    jobs_dir = Path(get_settings().job_apply.jobs_dir)
    jobs_applied = 0
    successful = 0
    hitl_required = 0

    if jobs_dir.exists():
        import json

        job_files = list(jobs_dir.glob("*.json"))
        jobs_applied = len(job_files)

        # Count by status and HITL requirement
        for job_file in job_files:
            try:
                data = json.loads(job_file.read_text(encoding="utf-8"))
                status = data.get("status", "")
                if status in ("applied", "interview"):
                    successful += 1
                # Check if HITL was required for this job
                if data.get("hitl_required") or data.get("hitl_count", 0) > 0:
                    hitl_required += 1
            except Exception:  # noqa: BLE001
                pass

    success_rate = (successful / jobs_applied * 100) if jobs_applied > 0 else 0
    hitl_rate = (hitl_required / jobs_applied * 100) if jobs_applied > 0 else 0

    # Try to get historical data for deltas
    tasks_delta = 0
    success_delta = 0.0
    hitl_delta = 0.0
    jobs_delta = 0

    if store:
        try:
            yesterday = await store.get("metrics:yesterday")
            if yesterday:
                tasks_delta = jobs_applied - yesterday.get("tasks_today", jobs_applied)
                success_delta = round(
                    success_rate - yesterday.get("success_rate", success_rate),
                    1,
                )
                hitl_delta = round(
                    hitl_rate - yesterday.get("hitl_rate", hitl_rate),
                    1,
                )
                jobs_delta = jobs_applied - yesterday.get("jobs_applied", jobs_applied)
        except Exception:  # noqa: BLE001
            pass

    return DashboardMetrics(
        tasks_today=jobs_applied,
        tasks_delta=tasks_delta,
        success_rate=round(success_rate, 1),
        success_delta=success_delta,
        hitl_rate=round(hitl_rate, 1),
        hitl_delta=hitl_delta,
        jobs_applied=jobs_applied,
        jobs_delta=jobs_delta,
        time_saved_minutes=jobs_applied * 15,  # Estimate 15 min per job
    )


@router.get("/health", response_model=SystemHealth)
async def get_system_health() -> SystemHealth:
    """Get system component health status."""
    health = SystemHealth()

    # Check Redis
    try:
        store = await asyncio.wait_for(get_state_store(), timeout=1.0)
        if store:
            await store.get("health_check")
            health.redis = "healthy"
    except Exception:  # noqa: BLE001
        health.redis = "unhealthy"

    # Check Kafka
    try:
        from aria.adapters.kafka import get_event_bus

        bus = await asyncio.wait_for(get_event_bus(), timeout=1.0)
        if bus:
            health.kafka = "healthy"
    except Exception:  # noqa: BLE001
        health.kafka = "unhealthy"

    # Check Qdrant
    try:
        from aria.adapters.qdrant import get_vector_store

        vs = await asyncio.wait_for(get_vector_store(), timeout=1.0)
        if vs:
            health.qdrant = "healthy"
    except Exception:  # noqa: BLE001
        health.qdrant = "unhealthy"

    return health


@router.get("/recent-tasks")
async def get_recent_tasks(limit: int = 10) -> list[dict[str, Any]]:
    """Get recent task executions."""
    store = await _safe_state_store()

    if not store:
        return []

    try:
        # Get recent sessions
        sessions = await store.get("sessions:recent") or []
        return sessions[:limit]
    except Exception as exc:
        logger.debug("Failed to get recent tasks", error=str(exc))
        return []


async def _safe_state_store() -> Any | None:
    """Safely get state store with timeout."""
    try:
        return await asyncio.wait_for(get_state_store(), timeout=0.5)
    except Exception:  # noqa: BLE001
        return None
