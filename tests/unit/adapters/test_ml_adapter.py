import pytest

from aria.adapters.ml.adapter import MLAdapter
from aria.core.hand.capability import Capability, ExecutionContext
from aria.core.llm.base import LLMResponse


class FakeLLM:
    def __init__(self, content: str) -> None:
        self.content = content

    async def generate(self, messages, role=None, **kwargs):
        _ = messages
        _ = role
        _ = kwargs
        return LLMResponse(content=self.content, model="fake")


@pytest.mark.asyncio
async def test_match_job_parses_json() -> None:
    adapter = MLAdapter()
    adapter.llm = FakeLLM('{"score": 88, "reasons": ["fit"]}')

    result = await adapter.execute(
        Capability.ML_MATCH_JOB,
        {"job_data": {"title": "Dev"}, "profile": {"skills": ["Python"]}},
        ExecutionContext(session_id="s1", domain="job_apply"),
    )

    assert result.success
    assert result.data["score"] == 88


@pytest.mark.asyncio
async def test_match_job_fallback_on_invalid_json() -> None:
    adapter = MLAdapter()
    adapter.llm = FakeLLM("not json")

    result = await adapter.execute(
        Capability.ML_MATCH_JOB,
        {"job_data": {"title": "Dev"}, "profile": {}},
        ExecutionContext(session_id="s1", domain="job_apply"),
    )

    assert result.success
    assert result.data["score"] == 50


@pytest.mark.asyncio
async def test_unknown_capability_returns_failure() -> None:
    adapter = MLAdapter()

    result = await adapter.execute(
        Capability.WEB_CLICK,
        {},
        ExecutionContext(session_id="s1", domain="job_apply"),
    )

    assert result.success is False
    assert result.error is not None
