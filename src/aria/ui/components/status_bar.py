"""Status bar component - Session status and elapsed time display."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import streamlit as st

from aria.ui.i18n import t


def render_status_bar(
    *,
    status: str,
    domain: str,
    session_id: str,
    started_at: datetime | None = None,
) -> None:
    """Render bottom status bar with session information.

    Args:
        status: Current session status ('idle', 'running', 'paused', etc.)
        domain: Current domain ('job_apply', etc.)
        session_id: Session UUID
        started_at: Session start timestamp

    """
    started_at = started_at or datetime.now(tz=UTC)
    elapsed = datetime.now(tz=UTC) - started_at

    # Status styling
    status_config = {
        "idle": {"icon": "⚪", "color": "var(--color-text-muted)", "label": t("status.idle")},
        "running": {"icon": "🟢", "color": "var(--color-success)", "label": t("status.running")},
        "paused": {"icon": "🟡", "color": "var(--color-warning)", "label": t("status.paused")},
        "waiting_human": {"icon": "🔵", "color": "var(--color-info)", "label": t("status.waiting_human")},
        "completed": {"icon": "✅", "color": "var(--color-success)", "label": t("status.completed")},
        "failed": {"icon": "🔴", "color": "var(--color-error)", "label": t("status.failed")},
        "cancelled": {"icon": "⚫", "color": "var(--color-text-muted)", "label": t("status.cancelled")},
    }

    config = status_config.get(status, status_config["idle"])

    # Render as columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div style="
                display: flex;
                align-items: center;
                gap: var(--space-2);
            ">
                <span>{config['icon']}</span>
                <div>
                    <div style="font-size: var(--font-size-xs); color: var(--color-text-muted);">
                        Status
                    </div>
                    <div style="font-weight: 600; color: {config['color']};">
                        {config['label']}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div>
                <div style="font-size: var(--font-size-xs); color: var(--color-text-muted);">
                    {t('session.domain')}
                </div>
                <div style="font-weight: 600;">
                    {domain}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div>
                <div style="font-size: var(--font-size-xs); color: var(--color-text-muted);">
                    {t('session.id')}
                </div>
                <div style="font-weight: 600; font-family: var(--font-family-mono);">
                    {session_id[:8]}...
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        elapsed_str = _format_timedelta(elapsed)
        st.markdown(
            f"""
            <div>
                <div style="font-size: var(--font-size-xs); color: var(--color-text-muted);">
                    {t('session.elapsed')}
                </div>
                <div style="font-weight: 600; font-family: var(--font-family-mono);">
                    {elapsed_str}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _format_timedelta(delta: timedelta) -> str:
    """Format timedelta as HH:MM:SS string.

    Args:
        delta: Time duration

    Returns:
        Formatted string like "00:05:32"

    """
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
