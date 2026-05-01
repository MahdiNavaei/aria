"""Tests for the public replay trace contract."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aria.core.replay import ReplayMode, ReplayRequest, StepRecord, TraceEnvelope


def test_trace_hash_is_deterministic() -> None:
    """Equivalent traces must produce the same content hash."""

    timestamp = datetime(2026, 2, 28, 12, 0, tzinfo=UTC)
    step = StepRecord(
        step_id="step_1",
        capability="web.navigate",
        status="succeeded",
        inputs={"url": "https://example.com"},
        outputs={"status_code": 200},
        started_at=timestamp,
        completed_at=timestamp,
    )

    trace_a = TraceEnvelope(
        execution_id="exec_public_preview",
        goal="Open a safe page",
        status="completed",
        created_at=timestamp,
        completed_at=timestamp,
        steps=[step],
        metadata={"release": "v0.2"},
    )
    trace_b = TraceEnvelope.model_validate(trace_a.model_dump(mode="json"))

    assert trace_a.content_hash() == trace_b.content_hash()


def test_replay_request_integrity_check() -> None:
    """Replay requests can verify a caller-provided integrity hash."""

    timestamp = datetime(2026, 2, 28, 12, 0, tzinfo=UTC)
    trace = TraceEnvelope(
        execution_id="exec_integrity",
        goal="Verify replay contract",
        status="completed",
        created_at=timestamp,
        completed_at=timestamp,
    )

    assert ReplayRequest(trace=trace, require_hash=trace.content_hash()).verify_integrity()
    assert not ReplayRequest(trace=trace, require_hash="not-a-real-hash").verify_integrity()
    assert ReplayRequest(trace=trace, mode=ReplayMode.VERIFY).verify_integrity()


def test_failed_step_requires_error() -> None:
    """A failed step without an error is rejected at the contract boundary."""

    timestamp = datetime(2026, 2, 28, 12, 0, tzinfo=UTC)

    with pytest.raises(ValidationError):
        StepRecord(
            step_id="step_1",
            capability="web.click",
            status="failed",
            started_at=timestamp,
            completed_at=timestamp,
        )


def test_duplicate_step_ids_are_rejected() -> None:
    """Trace envelopes must keep step ids unique for replay safety."""

    timestamp = datetime(2026, 2, 28, 12, 0, tzinfo=UTC)
    step = StepRecord(
        step_id="step_1",
        capability="web.navigate",
        status="succeeded",
        started_at=timestamp,
        completed_at=timestamp,
    )

    with pytest.raises(ValidationError):
        TraceEnvelope(
            execution_id="exec_duplicate",
            goal="Reject duplicate steps",
            status="completed",
            created_at=timestamp,
            completed_at=timestamp,
            steps=[step, step],
        )
