"""Form filling helper using Eye observations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aria.core.eye import get_eye
from aria.core.hand.capability import CapabilityResult
from aria.utils.logging import get_logger

if TYPE_CHECKING:
    from aria.core.eye import Observation

logger = get_logger(__name__)


class FormFiller:
    """Intelligent form filler using Eye observations."""

    def __init__(self, browser_adapter: Any) -> None:  # noqa: ANN401
        """Initialize form filler with browser adapter."""
        self.browser = browser_adapter
        self._eye = None

    async def fill_form(
        self,
        form_data: dict[str, Any],
        context: dict | None = None,
    ) -> CapabilityResult:
        """Fill form using Eye observations."""
        if self._eye is None:
            self._eye = await get_eye()

        observation = await self._eye.observe(
            domain=context.get("domain", "job_apply") if context else "job_apply",
            source="browser",
        )

        form_fields = self._extract_form_fields(observation)
        field_mapping = self._map_data_to_fields(form_data, form_fields)

        filled_fields: list[str] = []
        errors: list[str] = []

        for field_name, (selector, value) in field_mapping.items():
            try:
                if selector:
                    await self.browser.page.fill(selector, str(value))
                    filled_fields.append(field_name)
                else:
                    result = await self.fill_with_vision(field_name, str(value))
                    if result.success:
                        filled_fields.append(field_name)
                    else:
                        errors.append(result.error or f"{field_name}: vision lookup failed")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{field_name}: {exc}")
                logger.warning("Failed to fill field", field=field_name, error=str(exc))

        if errors and not filled_fields:
            return CapabilityResult.fail("; ".join(errors))
        if errors:
            return CapabilityResult(
                success=True,
                data={"filled": filled_fields, "errors": errors},
            )

        return CapabilityResult.ok({"filled": filled_fields, "total": len(field_mapping)})

    def _extract_form_fields(self, observation: Observation) -> list[dict[str, Any]]:
        """Extract form fields from observation."""
        fields: list[dict[str, Any]] = [
            {
                "type": element.type.value,
                "label": element.text or "",
                "location": element.location,
                "attributes": element.attributes,
            }
            for element in observation.elements
            if element.type.value in {"input", "select", "checkbox", "radio"}
        ]

        if observation.vlm_analysis:
            for elem in observation.vlm_analysis.get("elements", []):
                if (
                    elem.get("type") in {"input", "select", "checkbox", "radio"}
                    and not any(f["label"] == elem.get("label") for f in fields)
                ):
                    fields.append(elem)
        return fields

    def _map_data_to_fields(
        self,
        data: dict[str, Any],
        fields: list[dict[str, Any]],
    ) -> dict[str, tuple[str | None, Any]]:
        """Map form data to field selectors."""
        mapping: dict[str, tuple[str | None, Any]] = {}

        for data_key, value in data.items():
            best_match = None
            best_score = 0

            for field in fields:
                label = str(field.get("label", "")).lower()
                data_key_lower = data_key.lower()

                if data_key_lower in label or label in data_key_lower:
                    score = len(set(data_key_lower) & set(label))
                    if score > best_score:
                        best_score = score
                        best_match = field

            if best_match:
                selector = None
                attributes = best_match.get("attributes", {})
                if attributes.get("id"):
                    selector = f"#{attributes['id']}"
                elif attributes.get("name"):
                    selector = f"[name='{attributes['name']}']"
                mapping[data_key] = (selector, value)
            else:
                mapping[data_key] = (None, value)

        return mapping

    async def fill_with_vision(self, field_description: str, value: str) -> CapabilityResult:
        """Fill form field using vision-based element location."""
        if self._eye is None:
            self._eye = await get_eye()

        element = await self._eye.locate_element(field_description)
        if element and element.location and self.browser.page:
            x, y = element.location.center
            await self.browser.page.mouse.click(x, y)
            await self.browser.page.keyboard.type(value)
            return CapabilityResult.ok(
                {"filled_by_vision": field_description, "location": (x, y)},
            )

        return CapabilityResult.fail(f"Could not locate field: {field_description}")
