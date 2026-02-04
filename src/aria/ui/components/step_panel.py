"""Step panel component - Current step and plan progress display."""

from __future__ import annotations

from typing import Any

import streamlit as st

from aria.ui.i18n import t


def render_step_panel(
    step_info: dict[str, Any] | None,
    plan: dict[str, Any] | None = None,
) -> None:
    """Render current step panel with progress.

    Args:
        step_info: Current step information dictionary
        plan: Full execution plan dictionary

    """
    st.subheader(t("step.title"))

    if not step_info:
        # Empty state
        st.markdown(
            f"""
            <div style="
                text-align: center;
                padding: var(--space-6) var(--space-4);
                background: var(--color-bg-secondary);
                border-radius: var(--radius-lg);
                border: 1px dashed var(--color-border-medium);
            ">
                <div style="font-size: 2rem; margin-bottom: var(--space-2);">📋</div>
                <p style="color: var(--color-text-secondary); margin: 0;">
                    {t('step.no_step')}
                </p>
                <p style="
                    color: var(--color-text-muted);
                    font-size: var(--font-size-sm);
                    margin-top: var(--space-1);
                ">
                    {t('step.no_step_hint')}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Step info card
    step_name = step_info.get("step", "Unknown")
    step_status = step_info.get("status", "running")
    step_number = step_info.get("step_number", 1)
    total_steps = step_info.get("total_steps", 1)
    confidence = step_info.get("confidence")
    details = step_info.get("details", "")

    # Status styling
    status_styles = {
        "pending": ("⏳", "var(--color-text-muted)"),
        "running": ("🔄", "var(--color-info)"),
        "completed": ("✅", "var(--color-success)"),
        "failed": ("❌", "var(--color-error)"),
        "skipped": ("⏭️", "var(--color-text-muted)"),
    }

    status_icon, status_color = status_styles.get(
        step_status, ("📌", "var(--color-text-secondary)"),
    )

    # Progress calculation
    progress = (step_number / total_steps) * 100 if total_steps > 0 else 0

    # Render card
    st.markdown(
        f"""
        <div style="
            background: var(--color-bg-card);
            border: 1px solid var(--color-border-light);
            border-radius: var(--radius-lg);
            padding: var(--space-4);
            box-shadow: var(--shadow-sm);
        ">
            <!-- Step header -->
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: var(--space-3);
            ">
                <span style="
                    font-size: var(--font-size-sm);
                    color: var(--color-text-muted);
                ">
                    {t('step.of').replace('of', f'{step_number} {t("step.of")} {total_steps}')}
                    {step_number} {t('step.of')} {total_steps}
                </span>
                <span style="color: {status_color};">
                    {status_icon} {t(f'plan.step_{step_status}')}
                </span>
            </div>

            <!-- Step name -->
            <h4 style="margin: 0 0 var(--space-3) 0; color: var(--color-text-primary);">
                {step_name}
            </h4>

            <!-- Progress bar -->
            <div style="
                background: var(--color-bg-secondary);
                border-radius: var(--radius-full);
                height: 8px;
                overflow: hidden;
                margin-bottom: var(--space-3);
            ">
                <div style="
                    background: linear-gradient(90deg, var(--color-accent-primary), var(--color-accent-secondary));
                    height: 100%;
                    width: {progress}%;
                    border-radius: var(--radius-full);
                    transition: width 0.3s ease;
                "></div>
            </div>

            <!-- Details -->
            {f'<p style="color: var(--color-text-secondary); font-size: var(--font-size-sm); margin: 0;">{details}</p>' if details else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Confidence indicator
    if confidence is not None:
        confidence_pct = int(confidence * 100)
        confidence_color = (
            "var(--color-success)" if confidence >= 0.8
            else "var(--color-warning)" if confidence >= 0.5
            else "var(--color-error)"
        )

        st.markdown(
            f"""
            <div style="
                margin-top: var(--space-3);
                display: flex;
                align-items: center;
                gap: var(--space-2);
                font-size: var(--font-size-sm);
            ">
                <span style="color: var(--color-text-muted);">{t('step.confidence')}:</span>
                <span style="color: {confidence_color}; font-weight: 600;">
                    {confidence_pct}%
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Plan steps (if available)
    if plan and plan.get("steps"):
        with st.expander(f"📋 {t('plan.title')}", expanded=False):
            steps = plan.get("steps", [])
            for i, step in enumerate(steps, 1):
                step_status_icon = (
                    "✅" if i < step_number
                    else "🔄" if i == step_number
                    else "⏳"
                )
                step_name_text = step.get("name", f"Step {i}")
                st.markdown(f"{step_status_icon} **{i}.** {step_name_text}")
