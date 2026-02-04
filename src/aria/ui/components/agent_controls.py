"""Agent control buttons - Start, Pause, Resume, Stop."""

from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    from collections.abc import Callable

from aria.ui.i18n import t


def render_agent_controls(  # noqa: C901, PLR0912, PLR0913, PLR0915
    status: str,
    on_start: Callable[[], None] | None = None,
    on_pause: Callable[[], None] | None = None,
    on_resume: Callable[[], None] | None = None,
    on_stop: Callable[[], None] | None = None,
    *,
    compact: bool = False,
) -> str | None:
    """Render agent control buttons.

    Args:
        status: Current agent status (idle, running, paused, etc.)
        on_start: Callback for start button
        on_pause: Callback for pause button
        on_resume: Callback for resume button
        on_stop: Callback for stop button
        compact: If True, use vertical layout for narrow spaces (sidebar)

    Returns:
        Action taken ('start', 'pause', 'resume', 'stop') or None

    """
    action = None

    if compact:
        # Vertical layout for sidebar - 2 rows of 2 buttons
        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)

        # Start button
        start_disabled = status not in ("idle", "completed", "failed", "cancelled")
        with row1_col1:
            if st.button(
                "▶️",
                key="ctrl_start",
                disabled=start_disabled,
                use_container_width=True,
                type="primary" if not start_disabled else "secondary",
                help=t("controls.start"),
            ):
                if on_start:
                    on_start()
                action = "start"

        # Pause button
        pause_disabled = status != "running"
        with row1_col2:
            if st.button(
                "⏸️",
                key="ctrl_pause",
                disabled=pause_disabled,
                use_container_width=True,
                help=t("controls.pause"),
            ):
                if on_pause:
                    on_pause()
                action = "pause"

        # Resume button
        resume_disabled = status != "paused"
        with row2_col1:
            if st.button(
                "⏯️",
                key="ctrl_resume",
                disabled=resume_disabled,
                use_container_width=True,
                help=t("controls.resume"),
            ):
                if on_resume:
                    on_resume()
                action = "resume"

        # Stop button
        stop_disabled = status not in ("running", "paused", "waiting_human")
        with row2_col2:
            if st.button(
                "⏹️",
                key="ctrl_stop",
                disabled=stop_disabled,
                use_container_width=True,
                help=t("controls.stop"),
            ):
                if on_stop:
                    on_stop()
                action = "stop"

    else:
        # Horizontal layout for main area
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            start_disabled = status not in ("idle", "completed", "failed", "cancelled")
            if st.button(
                f"▶️ {t('controls.start')}",
                key="ctrl_start",
                disabled=start_disabled,
                use_container_width=True,
                type="primary" if not start_disabled else "secondary",
            ):
                if on_start:
                    on_start()
                action = "start"

        with col2:
            pause_disabled = status != "running"
            if st.button(
                f"⏸️ {t('controls.pause')}",
                key="ctrl_pause",
                disabled=pause_disabled,
                use_container_width=True,
            ):
                if on_pause:
                    on_pause()
                action = "pause"

        with col3:
            resume_disabled = status != "paused"
            if st.button(
                f"▶️ {t('controls.resume')}",
                key="ctrl_resume",
                disabled=resume_disabled,
                use_container_width=True,
            ):
                if on_resume:
                    on_resume()
                action = "resume"

        with col4:
            stop_disabled = status not in ("running", "paused", "waiting_human")
            if st.button(
                f"⏹️ {t('controls.stop')}",
                key="ctrl_stop",
                disabled=stop_disabled,
                use_container_width=True,
            ):
                if on_stop:
                    on_stop()
                action = "stop"

    return action


def render_goal_input() -> str | None:
    """Render goal input field with submit button.

    Returns:
        Goal string if submitted, None otherwise

    """
    # Full width input
    goal = st.text_input(
        t("chat.placeholder"),
        placeholder=t("chat.placeholder"),
        key="goal_input",
        label_visibility="collapsed",
    )

    # Submit button below input
    submitted = st.button(
        f"▶️ {t('controls.start')}",
        key="goal_submit",
        type="primary",
        use_container_width=True,
    )

    if submitted and goal:
        return goal
    return None
