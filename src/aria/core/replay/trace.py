"""Minimal deterministic trace contracts for public replay previews.

This module is intentionally small: it introduces the public v0.2 contract
surface without pulling the private workspace's full replay implementation into
the public repository.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TraceStatus = Literal["running", "completed", "failed", "cancelled"]
StepStatus = Literal["pending", "running", "succeeded", "failed", "skipped"]

_ERR_DUPLICATE_STEP = "duplicate step_id"
_ERR_EMPTY_GOAL = "goal must not be empty"
_ERR_EMPTY_VALUE = "value must not be empty"
_ERR_FAILED_STEP = "failed steps must include error"
_ERR_TERMINAL_STEP = "terminal steps must include completed_at"
_ERR_TERMINAL_TRACE = "terminal traces must include completed_at"


class ReplayMode(StrEnum):
    """Replay execution mode."""

    DRY_RUN = "dry_run"
    VERIFY = "verify"
    APPLY = "apply"


class StepRecord(BaseModel):
    """A single auditable execution step."""

    model_config = ConfigDict(extra="forbid")

    step_id: str
    capability: str
    status: StepStatus = "pending"
    attempt: int = Field(default=1, ge=1)
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    @field_validator("step_id", "capability")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(_ERR_EMPTY_VALUE)
        return value

    @model_validator(mode="after")
    def _validate_terminal_step(self) -> StepRecord:
        if self.status in {"succeeded", "failed", "skipped"} and self.completed_at is None:
            raise ValueError(_ERR_TERMINAL_STEP)
        if self.status == "failed" and not self.error:
            raise ValueError(_ERR_FAILED_STEP)
        return self


class TraceEnvelope(BaseModel):
    """Versioned trace envelope used for deterministic replay and audit."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "replay.trace.v1"
    execution_id: str = Field(default_factory=lambda: f"exec_{uuid4().hex[:12]}")
    goal: str
    status: TraceStatus = "running"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    steps: list[StepRecord] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("goal")
    @classmethod
    def _goal_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(_ERR_EMPTY_GOAL)
        return value

    @model_validator(mode="after")
    def _validate_trace_state(self) -> TraceEnvelope:
        seen: set[str] = set()
        for step in self.steps:
            if step.step_id in seen:
                raise ValueError(_ERR_DUPLICATE_STEP)
            seen.add(step.step_id)

        if self.status in {"completed", "failed", "cancelled"} and self.completed_at is None:
            raise ValueError(_ERR_TERMINAL_TRACE)
        return self

    def canonical_payload(self) -> dict[str, Any]:
        """Return a stable JSON-compatible representation."""
        return self.model_dump(mode="json", exclude_none=True)

    def content_hash(self) -> str:
        """Compute a deterministic SHA-256 hash for trace integrity checks."""
        payload = json.dumps(
            self.canonical_payload(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return sha256(payload.encode("utf-8")).hexdigest()


class ReplayRequest(BaseModel):
    """Request to replay or verify a stored trace."""

    model_config = ConfigDict(extra="forbid")

    trace: TraceEnvelope
    mode: ReplayMode = ReplayMode.DRY_RUN
    requested_by: str = "local"
    require_hash: str | None = None

    def verify_integrity(self) -> bool:
        """Return whether the requested hash matches the trace hash."""
        if self.require_hash is None:
            return True
        return self.trace.content_hash() == self.require_hash
