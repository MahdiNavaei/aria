"""Hand service for executing capabilities."""

from __future__ import annotations

import asyncio
from typing import Any

from aria.adapters.browser import BrowserAdapter
from aria.adapters.desktop import DesktopAdapter
from aria.adapters.ml import MLAdapter
from aria.config import get_settings
from aria.core.hand.capability import (
    Capability,
    CapabilityAdapter,
    CapabilityCategory,
    CapabilityResult,
    ExecutionContext,
)
from aria.core.safety import SafetyDecision, get_safety_gate
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class Hand:
    """ARIA Hand - execution component."""

    def __init__(self) -> None:
        """Initialize Hand service."""
        self._adapters: dict[CapabilityCategory, CapabilityAdapter] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize configured adapters."""
        if self._initialized:
            return

        enabled = set(get_settings().hand.adapters)
        if "browser" in enabled:
            self._adapters[CapabilityCategory.WEB] = BrowserAdapter()
        if "desktop" in enabled:
            self._adapters[CapabilityCategory.DESKTOP] = DesktopAdapter()
        if "ml" in enabled:
            self._adapters[CapabilityCategory.ML] = MLAdapter()

        for adapter in self._adapters.values():
            await adapter.initialize()

        self._initialized = True
        logger.info("Hand initialized", adapters=[cat.value for cat in self._adapters])

    async def cleanup(self) -> None:
        """Cleanup all adapters."""
        for adapter in self._adapters.values():
            await adapter.cleanup()
        self._adapters.clear()
        self._initialized = False

    def register_adapter(self, adapter: CapabilityAdapter) -> None:
        """Register a custom adapter."""
        self._adapters[adapter.category] = adapter

    def get_adapter(self, capability: Capability) -> CapabilityAdapter | None:
        """Get adapter for a capability."""
        return self._adapters.get(capability.category)

    async def execute(
        self,
        capability: str | Capability,
        parameters: dict[str, Any],
        context: dict[str, Any] | ExecutionContext | None = None,
    ) -> CapabilityResult:
        """Execute a capability via the appropriate adapter."""
        if not self._initialized:
            await self.initialize()

        if isinstance(capability, str):
            try:
                capability = Capability(capability)
            except ValueError:
                return CapabilityResult.fail(f"Unknown capability: {capability}")

        if context is None:
            context_data: dict[str, Any] = {
                "session_id": "unknown",
                "domain": "unknown",
            }
            context = ExecutionContext(session_id="unknown", domain="unknown")
        elif isinstance(context, dict):
            context_data = dict(context)
            context = ExecutionContext(**context)
        else:
            context_data = context.model_dump()

        adapter = self.get_adapter(capability)
        if adapter is None:
            return CapabilityResult.fail(
                f"No adapter for capability category: {capability.category}",
            )

        safety_gate = get_safety_gate()
        safety_result = await safety_gate.pre_check(
            capability.value,
            parameters,
            context_data,
        )

        if safety_result.decision == SafetyDecision.BLOCK:
            logger.warning(
                "Capability blocked by safety",
                capability=capability.value,
                reason=safety_result.reason,
            )
            return CapabilityResult.fail(
                f"Blocked: {safety_result.reason}",
                data={"safety_decision": safety_result.decision.value},
            )

        if safety_result.decision == SafetyDecision.RATE_LIMITED:
            return CapabilityResult.fail(
                f"Rate limited: {safety_result.reason}",
                data={
                    "safety_decision": safety_result.decision.value,
                    "retry_after": safety_result.rate_limit.retry_after
                    if safety_result.rate_limit
                    else None,
                },
            )

        if safety_result.decision == SafetyDecision.REQUIRE_HUMAN:
            return CapabilityResult.fail(
                "Human confirmation required",
                data={
                    "safety_decision": safety_result.decision.value,
                    "hitl_request": safety_result.hitl_request,
                },
            )

        logger.debug(
            "Executing capability",
            capability=capability.value,
            adapter=adapter.__class__.__name__,
        )

        result = await adapter.execute(capability, parameters, context)
        post_result = await safety_gate.post_check(
            capability.value,
            result.data or {},
            context_data,
        )
        if post_result.get("warnings"):
            result.metadata["safety_warnings"] = post_result["warnings"]

        return result

    async def execute_with_retry(
        self,
        capability: str | Capability,
        parameters: dict[str, Any],
        context: dict[str, Any] | ExecutionContext | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> CapabilityResult:
        """Execute with automatic retry on failure."""
        last_result: CapabilityResult | None = None
        for attempt in range(max_retries):
            result = await self.execute(capability, parameters, context)
            if result.success:
                return result
            last_result = result
            if attempt < max_retries - 1:
                logger.warning(
                    "Capability failed, retrying",
                    capability=(
                        capability if isinstance(capability, str) else capability.value
                    ),
                    attempt=attempt + 1,
                    error=result.error,
                )
                await asyncio.sleep(retry_delay * (attempt + 1))
        return last_result or CapabilityResult.fail("Max retries exceeded")

    @property
    def browser_adapter(self) -> BrowserAdapter | None:
        """Return browser adapter if available."""
        adapter = self._adapters.get(CapabilityCategory.WEB)
        return adapter if isinstance(adapter, BrowserAdapter) else None


_hand: Hand | None = None


async def get_hand() -> Hand:
    """Return singleton Hand instance."""
    global _hand  # noqa: PLW0603
    if _hand is None:
        _hand = Hand()
        await _hand.initialize()
    return _hand
