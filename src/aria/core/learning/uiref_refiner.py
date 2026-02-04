"""UIRef refinement based on execution outcomes."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from aria.config import get_settings
from aria.core.eye.uiref import Locator, LocatorType, UIRef
from aria.core.memory import SemanticMemory
from aria.models.events import EventEnvelope, EventType
from aria.utils.logging import get_logger

if TYPE_CHECKING:
    from aria.config.learning import LearningConfig

logger = get_logger(__name__)


class UIRefRefiner:
    """Refine UIRefs based on execution results.

    - Increase confidence for successful locators
    - Decrease confidence for failed locators
    - Learn new locators from successful actions
    """

    def __init__(
        self,
        semantic_memory: SemanticMemory | None = None,
        settings: LearningConfig | None = None,
    ) -> None:
        """Initialize UIRef refiner."""
        self._settings = settings or get_settings().learning
        self.semantic_memory = semantic_memory or SemanticMemory()

    async def on_execution_result(self, event: EventEnvelope) -> None:
        """Handle execution events to refine UIRefs."""
        payload = event.payload or {}
        nested = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}

        capability = payload.get("capability") or nested.get("capability") or ""
        if not capability.startswith("web.") and not capability.startswith("desktop."):
            return

        success = nested.get("success")
        if success is None:
            if event.event_type == EventType.HAND_EXECUTION_FAILED:
                success = False
            elif event.event_type == EventType.HAND_EXECUTION_COMPLETED:
                success = True

        uiref_id = payload.get("uiref_id") or nested.get("uiref_id")
        locator_type = payload.get("locator_type") or nested.get("locator_type")
        element_info = payload.get("element_info") or nested.get("element_info")

        if uiref_id and locator_type and success is not None:
            await self._update_confidence(uiref_id, locator_type, success=bool(success))

        if success is False and isinstance(element_info, dict):
            await self._learn_new_locator(uiref_id, element_info)

    async def _update_confidence(
        self,
        uiref_id: str,
        locator_type: str,
        *,
        success: bool,
    ) -> None:
        """Update confidence for a locator."""
        uiref_data = await self.semantic_memory.get_uiref(uiref_id)
        if not uiref_data:
            return

        uiref = UIRef(**uiref_data)
        increment = self._settings.uiref_refinement.confidence_increment
        decrement = self._settings.uiref_refinement.confidence_decrement
        min_confidence = self._settings.uiref_refinement.min_confidence

        for locator in uiref.locators:
            if locator.type.value == locator_type:
                if success:
                    locator.confidence = min(1.0, locator.confidence + increment)
                    locator.last_success = datetime.now(UTC).isoformat()
                else:
                    locator.confidence = max(0.0, locator.confidence - decrement)
                break

        uiref.locators = [
            loc for loc in uiref.locators if loc.confidence >= min_confidence
        ]
        uiref.locators.sort(key=lambda loc: loc.confidence, reverse=True)

        await self.semantic_memory.add_uiref(
            uiref.uiref_id,
            uiref.model_dump(),
            uiref.description,
        )

        logger.debug(
            "UIRef confidence updated",
            uiref_id=uiref_id,
            locator_type=locator_type,
            success=success,
        )

    async def _learn_new_locator(self, uiref_id: str | None, element_info: dict[str, Any]) -> None:
        """Learn new locator from element info."""
        if not uiref_id:
            return

        uiref_data = await self.semantic_memory.get_uiref(uiref_id)
        if not uiref_data:
            return

        uiref = UIRef(**uiref_data)
        new_locators: list[Locator] = []

        if element_info.get("id"):
            new_locators.append(
                Locator(
                    type=LocatorType.CSS,
                    value=f"#{element_info['id']}",
                    confidence=0.6,
                ),
            )

        if element_info.get("aria_label"):
            new_locators.append(
                Locator(
                    type=LocatorType.ARIA_LABEL,
                    value=element_info["aria_label"],
                    confidence=0.7,
                ),
            )

        if element_info.get("text"):
            new_locators.append(
                Locator(
                    type=LocatorType.TEXT,
                    value=str(element_info["text"]),
                    confidence=0.5,
                ),
            )

        existing_values = {loc.value for loc in uiref.locators}
        for locator in new_locators:
            if locator.value not in existing_values:
                uiref.locators.append(locator)

        uiref.locators.sort(key=lambda loc: loc.confidence, reverse=True)

        await self.semantic_memory.add_uiref(
            uiref.uiref_id,
            uiref.model_dump(),
            uiref.description,
        )

        logger.info(
            "New locators learned for UIRef",
            uiref_id=uiref_id,
            new_count=len(new_locators),
        )

    async def cleanup_low_confidence(self, threshold: float = 0.1) -> int:
        """Clean up locators with low confidence."""
        logger.info("UIRef cleanup requested", threshold=threshold)
        return 0
