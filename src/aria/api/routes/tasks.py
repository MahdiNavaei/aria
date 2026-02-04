"""Task management endpoints."""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from aria.adapters.redis import get_state_store
from aria.core.brain import get_brain
from aria.core.brain.nodes.hitl import submit_hitl_response
from aria.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class TaskCreate(BaseModel):
    """Task creation payload."""

    goal: str
    domain: str = "job_apply"
    auto_execute: bool = False
    user_id: str = "default"


class TaskResponse(BaseModel):
    """Task response payload."""

    task_id: str
    session_id: str
    goal: str
    domain: str
    status: str


class HITLResponse(BaseModel):
    """HITL response payload."""

    action: str  # approve, reject, completed, retry
    reason: str | None = None
    data: dict[str, Any] | None = None


@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate) -> TaskResponse:
    """Create and optionally start a new task."""
    session_id = str(uuid4())
    status = "created"

    if task.auto_execute:
        brain = await get_brain()
        asyncio.create_task(  # noqa: RUF006
            brain.run(
                goal=task.goal,
                domain=task.domain,
                session_id=session_id,
                user_id=task.user_id,
            ),
        )
        status = "running"

    await _store_task_state(
        session_id,
        {
            "status": status,
            "goal": task.goal,
            "domain": task.domain,
            "user_id": task.user_id,
        },
    )

    return TaskResponse(
        task_id=session_id,
        session_id=session_id,
        goal=task.goal,
        domain=task.domain,
        status=status,
    )


@router.get("/{task_id}")
async def get_task(task_id: str) -> dict:
    """Get task status."""
    store = await _safe_state_store()
    if store is None:
        raise HTTPException(status_code=503, detail="State store unavailable")

    state = await store.get_session_state(task_id)
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")

    return state


@router.post("/{task_id}/pause")
async def pause_task(task_id: str) -> dict[str, str]:
    """Pause a running task."""
    await _set_flag(task_id, "pause", value=True)
    return {"status": "paused"}


@router.post("/{task_id}/resume")
async def resume_task(task_id: str) -> dict[str, str]:
    """Resume a paused task."""
    await _set_flag(task_id, "pause", value=False)
    return {"status": "resumed"}


@router.post("/{task_id}/stop")
async def stop_task(task_id: str) -> dict[str, str]:
    """Stop a task."""
    await _set_flag(task_id, "stop", value=True)
    return {"status": "stopped"}


@router.post("/{task_id}/hitl")
async def submit_hitl(task_id: str, response: HITLResponse) -> dict[str, Any]:
    """Submit HITL (Human-in-the-Loop) response for a task.

    Args:
        task_id: The task/session ID
        response: HITL response with action and optional data

    Returns:
        Acknowledgment with status

    """
    try:
        # Build response payload for HITL system
        hitl_payload = {
            "action": response.action,
        }
        if response.reason:
            hitl_payload["reason"] = response.reason
        if response.data:
            hitl_payload.update(response.data)

        # Submit to HITL handler
        await submit_hitl_response(task_id, hitl_payload)

        # Update task state
        store = await _safe_state_store()
        if store:
            current = await store.get_session_state(task_id) or {}
            current["hitl_pending"] = False
            current["hitl_response"] = response.action
            await store.set_session_state(task_id, current)

        logger.info(
            "HITL response submitted",
            task_id=task_id,
            action=response.action,
        )

        return {
            "status": "accepted",
            "action": response.action,
            "task_id": task_id,
        }

    except Exception as exc:
        logger.exception("Failed to submit HITL response", task_id=task_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit HITL response: {exc}",
        ) from exc


async def _safe_state_store() -> Any | None:  # noqa: ANN401
    try:
        return await asyncio.wait_for(get_state_store(), timeout=0.5)
    except Exception as exc:  # noqa: BLE001
        logger.debug("State store unavailable", error=str(exc))
        return None


async def _store_task_state(session_id: str, state: dict[str, Any]) -> None:
    store = await _safe_state_store()
    if store is None:
        return
    await store.set_session_state(session_id, state)


async def _set_flag(session_id: str, flag: str, *, value: bool) -> None:
    store = await _safe_state_store()
    if store is None:
        return
    await store.set_flag(f"{flag}:{session_id}", value=value)
