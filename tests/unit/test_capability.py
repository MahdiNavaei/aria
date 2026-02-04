from aria.core.hand.capability import (
    Capability,
    CapabilityCategory,
    CapabilityResult,
    ExecutionContext,
)


def test_capability_category() -> None:
    assert Capability.WEB_NAVIGATE.category == CapabilityCategory.WEB
    assert Capability.DESKTOP_CLICK.category == CapabilityCategory.DESKTOP
    assert Capability.ML_MATCH_JOB.category == CapabilityCategory.ML


def test_capability_result_helpers() -> None:
    ok = CapabilityResult.ok({"value": 1})
    fail = CapabilityResult.fail("boom")

    assert ok.success is True
    assert ok.data == {"value": 1}
    assert fail.success is False
    assert fail.error == "boom"


def test_execution_context_defaults() -> None:
    ctx = ExecutionContext(session_id="sess", domain="job_apply")
    assert ctx.timeout == 30
    assert ctx.retry_count == 0
