"""Activity log component - Bilingual event log with filtering."""

from __future__ import annotations

from typing import Any

import streamlit as st

from aria.ui.i18n import t


def render_activity_log(
    events: list[dict[str, Any]],
    max_display: int = 50,
) -> None:
    """Render activity log with filtering and search.

    Args:
        events: List of event dictionaries with 'time', 'type', 'message'
        max_display: Maximum number of events to display

    """
    st.subheader(t("log.title"))

    # Filter controls
    col_filter, col_search = st.columns([1, 2])

    with col_filter:
        filter_options = [
            t("log.filter.all"),
            t("log.filter.brain"),
            t("log.filter.hand"),
            t("log.filter.eye"),
            t("log.filter.human"),
            t("log.filter.error"),
        ]
        filter_type = st.selectbox(
            t("log.filter"),
            filter_options,
            key="log_filter_select",
            label_visibility="collapsed",
        )

    with col_search:
        search = st.text_input(
            t("log.search"),
            placeholder=t("log.search"),
            key="log_search_input",
            label_visibility="collapsed",
        )

    # Filter events
    filtered = events[-max_display:]

    # Map translated filter back to type
    filter_map = {
        t("log.filter.all"): None,
        t("log.filter.brain"): "brain",
        t("log.filter.hand"): "hand",
        t("log.filter.eye"): "eye",
        t("log.filter.human"): "human",
        t("log.filter.error"): "error",
    }

    filter_key = filter_map.get(filter_type)
    if filter_key:
        filtered = [
            event
            for event in filtered
            if filter_key in event.get("type", "").lower()
        ]

    if search:
        search_lower = search.lower()
        filtered = [
            event
            for event in filtered
            if search_lower in str(event).lower()
        ]

    # Display events
    if not filtered:
        st.markdown(
            f"""
            <div style="
                text-align: center;
                padding: var(--space-8) var(--space-4);
                color: var(--color-text-muted);
            ">
                <div style="font-size: 2rem; margin-bottom: var(--space-2);">📋</div>
                <p style="margin: 0;">{t('log.empty')}</p>
                <p style="font-size: var(--font-size-sm); margin-top: var(--space-1);">
                    {t('log.empty_hint')}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Event list with scroll
    with st.container(height=280):
        for event in reversed(filtered):
            icon = _get_event_icon(event.get("type", ""))
            timestamp = event.get("time", "")
            message = event.get("message", "")
            event_type = event.get("type", "").lower()

            # Determine style based on type
            if "error" in event_type:
                st.error(f"{icon} `{timestamp}` {message}")
            elif "success" in event_type:
                st.success(f"{icon} `{timestamp}` {message}")
            elif "warning" in event_type:
                st.warning(f"{icon} `{timestamp}` {message}")
            else:
                st.markdown(
                    f"""
                    <div style="
                        padding: var(--space-2);
                        border-bottom: 1px solid var(--color-border-light);
                        font-size: var(--font-size-sm);
                    ">
                        <span style="margin-inline-end: var(--space-2);">{icon}</span>
                        <code style="color: var(--color-text-muted);">{timestamp}</code>
                        <span style="color: var(--color-text-secondary);">{message}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def _get_event_icon(event_type: str) -> str:
    """Get emoji icon for event type.

    Args:
        event_type: Event type string

    Returns:
        Emoji icon string

    """
    icons = {
        "brain": "🧠",
        "hand": "✋",
        "eye": "👁️",
        "human": "👤",
        "error": "❌",
        "success": "✅",
        "warning": "⚠️",
        "info": "ℹ️",
        "system": "⚙️",
        "chat": "💬",
        "hitl": "🤝",
        "browser": "🌐",
    }

    event_lower = event_type.lower()
    for key, icon in icons.items():
        if key in event_lower:
            return icon

    return "📌"
