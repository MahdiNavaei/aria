"""API Client for ARIA UI - connects to FastAPI backend."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from aria.config import get_settings

# Suppress httpx INFO logs (connection errors)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class APIClient:
    """HTTP client for ARIA API."""

    def __init__(self, base_url: str | None = None) -> None:
        """Initialize API client.

        Args:
            base_url: API base URL. Defaults to settings.

        """
        settings = get_settings()
        self.base_url = base_url or f"http://{settings.api.host}:{settings.api.port}"
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=30.0,
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    # =========================================================================
    # Health
    # =========================================================================

    def health_check(self) -> dict[str, Any]:
        """Check API health.

        Returns:
            Health status dict

        """
        try:
            response = self.client.get("/health")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            # Silently return unhealthy - API may not be running
            return {"status": "unhealthy"}

    # =========================================================================
    # Tasks
    # =========================================================================

    def start_task(self, goal: str, domain: str = "job_apply") -> dict[str, Any]:
        """Start a new task.

        Args:
            goal: Task goal/objective
            domain: Domain plugin to use

        Returns:
            Task info dict with task_id

        """
        try:
            response = self.client.post(
                "/api/tasks",
                json={"goal": goal, "domain": domain},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.exception("Failed to start task", extra={"error": str(exc)})
            return {"error": str(exc)}

    def get_task(self, task_id: str) -> dict[str, Any]:
        """Get task status.

        Args:
            task_id: Task ID

        Returns:
            Task status dict

        """
        try:
            response = self.client.get(f"/api/tasks/{task_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.warning("Failed to get task", extra={"error": str(exc)})
            return {"error": str(exc)}

    def pause_task(self, task_id: str) -> dict[str, Any]:
        """Pause a running task.

        Args:
            task_id: Task ID

        Returns:
            Updated task status

        """
        try:
            response = self.client.post(f"/api/tasks/{task_id}/pause")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.exception("Failed to pause task", extra={"error": str(exc)})
            return {"error": str(exc)}

    def resume_task(self, task_id: str) -> dict[str, Any]:
        """Resume a paused task.

        Args:
            task_id: Task ID

        Returns:
            Updated task status

        """
        try:
            response = self.client.post(f"/api/tasks/{task_id}/resume")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.exception("Failed to resume task", extra={"error": str(exc)})
            return {"error": str(exc)}

    def stop_task(self, task_id: str) -> dict[str, Any]:
        """Stop a running task.

        Args:
            task_id: Task ID

        Returns:
            Updated task status

        """
        try:
            response = self.client.post(f"/api/tasks/{task_id}/stop")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.exception("Failed to stop task", extra={"error": str(exc)})
            return {"error": str(exc)}

    # =========================================================================
    # HITL
    # =========================================================================

    def submit_hitl_response(
        self,
        task_id: str,
        action: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Submit HITL response.

        Args:
            task_id: Task ID
            action: Response action (approve, reject, completed, retry)
            reason: Optional rejection reason

        Returns:
            Response confirmation

        """
        try:
            response = self.client.post(
                f"/api/tasks/{task_id}/hitl",
                json={"action": action, "reason": reason},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.exception("Failed to submit HITL response", extra={"error": str(exc)})
            return {"error": str(exc)}

    # =========================================================================
    # Jobs
    # =========================================================================

    def get_jobs(self, status: str | None = None) -> list[dict[str, Any]]:
        """Get all jobs.

        Args:
            status: Filter by status

        Returns:
            List of job dicts

        """
        try:
            params = {"status": status} if status else {}
            response = self.client.get("/api/jobs", params=params)
            response.raise_for_status()
            data = response.json()
            # Handle both list and {"jobs": [...]} formats
            if isinstance(data, list):
                return data
            return data.get("jobs", [])
        except httpx.HTTPError as exc:
            logger.warning("Failed to get jobs", extra={"error": str(exc)})
            return []

    def extract_job(self, url: str) -> dict[str, Any]:
        """Extract job from URL.

        Args:
            url: Job posting URL

        Returns:
            Extracted job data

        """
        try:
            response = self.client.post(
                "/api/jobs/extract",
                json={"url": url},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.exception("Failed to extract job", extra={"error": str(exc)})
            return {"error": str(exc)}

    # =========================================================================
    # Metrics
    # =========================================================================

    def get_metrics(self) -> dict[str, Any]:
        """Get dashboard metrics.

        Returns:
            Metrics dict

        """
        try:
            response = self.client.get("/api/metrics")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            # Silently return defaults - API may not be running
            return {
                "tasks_today": 0,
                "success_rate": 0,
                "hitl_rate": 0,
                "time_saved_minutes": 0,
            }

    # =========================================================================
    # Analytics
    # =========================================================================

    def get_analytics(self, period: str = "week") -> dict[str, Any]:
        """Get analytics data.

        Args:
            period: Time period (today, week, month, all)

        Returns:
            Analytics data dict

        """
        try:
            response = self.client.get(
                "/api/analytics",
                params={"period": period},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.warning("Failed to get analytics", extra={"error": str(exc)})
            return {}
