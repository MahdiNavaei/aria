"""Human-in-the-Loop panel component - Bilingual HITL interface."""

from __future__ import annotations

from typing import Any

import streamlit as st

from aria.ui.i18n import t


def render_hitl_panel(request: dict[str, Any] | None) -> dict[str, Any] | None:
    """Render HITL request panel and return response when user acts.

    Args:
        request: HITL request dictionary with 'reason', 'context'

    Returns:
        Response dictionary with 'action' and optional 'reason' if user responded,
        None if no response yet

    """
    if not request:
        return None

    reason = request.get("reason", "unknown")
    context = request.get("context", {})

    # Panel container with attention-grabbing style
    st.markdown(
        f"""
        <div style="
            background: var(--color-warning-bg);
            border: 2px solid var(--color-warning);
            border-radius: var(--radius-lg);
            padding: var(--space-4);
            animation: pulse 2s ease-in-out infinite;
        ">
            <div style="display: flex; align-items: center; gap: var(--space-2); margin-bottom: var(--space-3);">
                <span style="font-size: 1.5rem;">⚠️</span>
                <h3 style="margin: 0; color: var(--color-warning);">{t('hitl.title')}</h3>
            </div>
            <p style="color: var(--color-text-secondary); margin: 0;">
                {t('hitl.subtitle')}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")  # Spacing

    # Reason-specific content
    if reason == "captcha":
        st.error(f"🔐 {t('hitl.reason.captcha')}")
    elif reason == "login":
        st.error(f"🔑 {t('hitl.reason.login')}")
    elif reason == "confirmation":
        st.warning(f"❓ {t('hitl.reason.confirmation')}")
        if context.get("action"):
            st.info(f"📋 **Action:** {context['action']}")
    elif reason == "error":
        error_msg = context.get("error", t("error.generic"))
        st.error(f"❌ {t('hitl.reason.error')}")
        st.code(error_msg)
    else:
        st.info(f"ℹ️ {t('hitl.reason.unknown')}")

    # Screenshot if available
    if context.get("screenshot_ref"):
        with st.expander("📷 Screenshot", expanded=False):
            st.caption(f"Reference: {context['screenshot_ref']}")

    st.write("")  # Spacing

    # Rejection reason input
    reject_reason = st.text_input(
        t("hitl.reject_reason"),
        placeholder=t("hitl.reject_reason_placeholder"),
        key="hitl_reject_reason_input",
    )

    # Action buttons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button(
            f"✅ {t('hitl.action.approve')}",
            type="primary",
            key="hitl_approve",
            use_container_width=True,
        ):
            return {"action": "approve"}

    with col2:
        if st.button(
            f"❌ {t('hitl.action.reject')}",
            key="hitl_reject",
            use_container_width=True,
        ):
            return {"action": "reject", "reason": reject_reason}

    with col3:
        if st.button(
            f"✋ {t('hitl.action.completed')}",
            key="hitl_completed",
            use_container_width=True,
        ):
            return {"action": "completed"}

    with col4:
        if st.button(
            f"🔄 {t('hitl.action.retry')}",
            key="hitl_retry",
            use_container_width=True,
        ):
            return {"action": "retry"}

    return None
