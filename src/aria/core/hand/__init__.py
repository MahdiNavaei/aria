"""Hand component exports."""

from __future__ import annotations

from typing import Any

from aria.core.hand.capability import (
    Capability,
    CapabilityAdapter,
    CapabilityCategory,
    CapabilityResult,
    ExecutionContext,
)

__all__ = [
    "BrowserAdapter",
    "Capability",
    "CapabilityAdapter",
    "CapabilityCategory",
    "CapabilityResult",
    "DesktopAdapter",
    "ExecutionContext",
    "FormFiller",
    "Hand",
    "MLAdapter",
    "get_hand",
]


def __getattr__(name: str) -> Any:  # noqa: ANN401, pragma: no cover - lazy imports
    if name == "BrowserAdapter":
        from aria.adapters.browser import BrowserAdapter  # noqa: PLC0415

        return BrowserAdapter
    if name == "FormFiller":
        from aria.adapters.browser import FormFiller  # noqa: PLC0415

        return FormFiller
    if name == "DesktopAdapter":
        from aria.adapters.desktop import DesktopAdapter  # noqa: PLC0415

        return DesktopAdapter
    if name == "MLAdapter":
        from aria.adapters.ml import MLAdapter  # noqa: PLC0415

        return MLAdapter
    if name == "Hand":
        from aria.core.hand.hand import Hand  # noqa: PLC0415

        return Hand
    if name == "get_hand":
        from aria.core.hand.hand import get_hand  # noqa: PLC0415

        return get_hand
    raise AttributeError(name)
