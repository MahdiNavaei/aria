"""Internationalization utilities for ARIA UI."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

import streamlit as st

from aria.ui.i18n.translations import TRANSLATIONS

if TYPE_CHECKING:
    from datetime import datetime

# Languages that use RTL direction
RTL_LANGUAGES = {"fa", "ar", "he", "ur"}


def get_language() -> str:
    """Get current language from session state.

    Returns:
        Language code (e.g., 'en', 'fa')

    """
    if "language" not in st.session_state:
        st.session_state.language = "en"
    return st.session_state.language


def set_language(lang: str) -> None:
    """Set current language.

    Args:
        lang: Language code ('en' or 'fa')

    """
    if lang in TRANSLATIONS:
        st.session_state.language = lang


def t(key: str, **kwargs: Any) -> str:
    """Translate a key to current language.

    Args:
        key: Translation key (e.g., 'hitl.title')
        **kwargs: Interpolation variables

    Returns:
        Translated string, or key if not found

    Example:
        >>> t("hitl.title")
        "Human Input Required"  # in English
        "نیاز به ورودی انسان"     # in Persian

        >>> t("metrics.count", count=5)
        "5 items"

    """
    lang = get_language()
    translations = TRANSLATIONS.get(lang, TRANSLATIONS["en"])

    # Get translation or fall back to English, then to key
    text = translations.get(key)
    if text is None:
        text = TRANSLATIONS["en"].get(key, key)
        # #region agent log
        if text == key:
            import json; open(r'd:\Projects\WorkFinder\.cursor\debug.log','a').write(json.dumps({"hypothesisId":"C","location":"i18n/utils.py:t","message":"missing_translation","data":{"key":key,"lang":lang},"timestamp":__import__("time").time()*1000,"sessionId":"debug-session"})+'\n')
        # #endregion

    # Interpolate variables
    if kwargs:
        with contextlib.suppress(KeyError, ValueError):
            text = text.format(**kwargs)

    return text


def is_rtl() -> bool:
    """Check if current language is RTL.

    Returns:
        True if current language is right-to-left

    """
    return get_language() in RTL_LANGUAGES


def get_direction() -> str:
    """Get text direction for current language.

    Returns:
        'rtl' or 'ltr'

    """
    return "rtl" if is_rtl() else "ltr"


def get_font_family() -> str:
    """Get appropriate font family for current language.

    Returns:
        CSS font-family string

    """
    if is_rtl():
        return "'Vazirmatn', 'Tahoma', sans-serif"
    return "'Space Grotesk', 'Inter', system-ui, sans-serif"


def format_number(value: float, locale: str | None = None) -> str:
    """Format a number according to current locale.

    Args:
        value: Number to format
        locale: Override locale (default: current language)

    Returns:
        Formatted number string

    """
    locale = locale or get_language()

    if locale == "fa":
        # Convert to Persian numerals
        persian_numerals = "۰۱۲۳۴۵۶۷۸۹"
        result = str(value)
        for i, digit in enumerate("0123456789"):
            result = result.replace(digit, persian_numerals[i])
        return result

    # Default: return as-is with thousand separators
    if isinstance(value, int):
        return f"{value:,}"
    return f"{value:,.2f}"


def format_date(dt: datetime, format_type: str = "short", locale: str | None = None) -> str:
    """Format a datetime according to current locale.

    Args:
        dt: Datetime to format
        format_type: 'short', 'long', or 'time'
        locale: Override locale (default: current language)

    Returns:
        Formatted date string

    """
    locale = locale or get_language()

    if locale == "fa":
        try:
            import jdatetime
            jdt = jdatetime.datetime.fromgregorian(datetime=dt)

            if format_type == "short":
                return jdt.strftime("%Y/%m/%d")
            if format_type == "long":
                months = [
                    "", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
                ]
                return f"{jdt.day} {months[jdt.month]} {jdt.year}"
            if format_type == "time":
                return jdt.strftime("%H:%M")
            return jdt.strftime("%Y/%m/%d %H:%M")
        except ImportError:
            # Fall back to Gregorian if jdatetime not installed
            pass

    # Default: English/Gregorian format
    if format_type == "short":
        return dt.strftime("%Y-%m-%d")
    if format_type == "long":
        return dt.strftime("%B %d, %Y")
    if format_type == "time":
        return dt.strftime("%H:%M")
    return dt.strftime("%Y-%m-%d %H:%M")


def format_duration(seconds: float, locale: str | None = None) -> str:
    """Format a duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds
        locale: Override locale (default: current language)

    Returns:
        Formatted duration string (e.g., "2h 30m" or "۲ ساعت ۳۰ دقیقه")

    """
    locale = locale or get_language()

    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)

    if locale == "fa":
        parts = []
        if hours > 0:
            parts.append(f"{format_number(hours, 'fa')} ساعت")
        if minutes > 0:
            parts.append(f"{format_number(minutes, 'fa')} دقیقه")
        if secs > 0 and hours == 0:
            parts.append(f"{format_number(secs, 'fa')} ثانیه")
        return " ".join(parts) if parts else "۰ ثانیه"

    # Default: English format
    if hours > 0:
        return f"{hours}h {minutes}m"
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def get_available_languages() -> list[dict[str, str]]:
    """Get list of available languages.

    Returns:
        List of language info dicts with 'code', 'name', 'native_name'

    """
    return [
        {"code": "en", "name": "English", "native_name": "English"},
        {"code": "fa", "name": "Persian", "native_name": "فارسی"},
    ]
