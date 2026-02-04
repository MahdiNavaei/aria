import pytest

from aria.adapters.browser.adapter import BrowserAdapter
from aria.core.hand.capability import Capability, ExecutionContext


@pytest.mark.asyncio
async def test_execute_without_page_returns_failure() -> None:
    adapter = BrowserAdapter()
    context = ExecutionContext(session_id="sess-1", domain="job_apply")

    result = await adapter._execute_capability(
        Capability.WEB_CLICK,
        {"selector": "#submit"},
        context,
    )

    assert result.success is False
    assert result.error == "Browser page not initialized"


def test_adapter_capabilities_contains_navigation() -> None:
    adapter = BrowserAdapter()
    assert Capability.WEB_NAVIGATE in adapter.capabilities
