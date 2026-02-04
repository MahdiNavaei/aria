"""Internationalization system for ARIA UI."""

from aria.ui.i18n.translations import TRANSLATIONS
from aria.ui.i18n.utils import (
    format_date,
    format_duration,
    format_number,
    get_available_languages,
    get_direction,
    get_font_family,
    get_language,
    is_rtl,
    set_language,
    t,
)

__all__ = [
    "TRANSLATIONS",
    "format_date",
    "format_duration",
    "format_number",
    "get_available_languages",
    "get_direction",
    "get_font_family",
    "get_language",
    "is_rtl",
    "set_language",
    "t",
]
