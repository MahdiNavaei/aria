"""Chat component - Bilingual chat interface with voice support."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import streamlit as st

from aria.ui.i18n import t

if TYPE_CHECKING:
    from collections.abc import Callable


def render_chat(
    messages: list[dict[str, Any]],
    on_send: Callable[[str], None] | None = None,
    enable_voice: bool = True,
) -> str | None:
    """Render chat interface with message history.

    Args:
        messages: List of message dictionaries with 'role', 'content', 'timestamp'
        on_send: Callback function when user sends a message
        enable_voice: Enable voice input (requires streamlit-mic-recorder)

    Returns:
        User input if submitted, None otherwise

    """
    st.subheader(t("chat.title"))

    # Welcome message if no messages
    if not messages:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, 
                    var(--color-accent-primary), var(--color-accent-secondary));
                color: white;
                padding: var(--space-4);
                border-radius: var(--radius-lg);
                margin-bottom: var(--space-4);
            ">
                <p style="margin: 0 0 var(--space-2) 0; font-weight: 600;">
                    👋 {t('chat.welcome')}
                </p>
                <p style="margin: 0; opacity: 0.9; font-size: var(--font-size-sm);">
                    💡 {t('chat.welcome_hint')}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Message container with scroll
    with st.container(height=350):
        for msg in messages:
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")

            # Determine avatar
            if role == "user":
                avatar = "👤"
            elif role == "assistant":
                avatar = "🤖"
            else:
                avatar = "ℹ️"

            with st.chat_message(role, avatar=avatar):
                st.markdown(content)
                if timestamp:
                    st.caption(f"🕐 {timestamp}")

    # Input area
    prompt = None
    voice_text = None

    if enable_voice:
        col_input, col_voice = st.columns([8, 2])

        with col_input:
            prompt = st.chat_input(
                placeholder=t("chat.placeholder"),
                key="chat_input",
            )

        with col_voice:
            voice_text = _render_voice_input()
    else:
        prompt = st.chat_input(
            placeholder=t("chat.placeholder"),
            key="chat_input",
        )

    # Handle text or voice submission
    final_input = voice_text or prompt

    if final_input and on_send:
        on_send(final_input)

    return final_input


def _render_voice_input() -> str | None:
    """Render voice input with fallback.

    Returns:
        Transcribed text if available
    """
    # Try to use the full voice input component
    try:
        from aria.ui.components.voice_input import is_voice_available, render_voice_input

        if is_voice_available():
            return render_voice_input(key="chat_voice")

        # Fallback: simple button with toast
        if st.button(
            "🎤",
            key="voice_btn_fallback",
            help=t("chat.voice_button"),
            use_container_width=True,
        ):
            st.toast(
                "Install: pip install streamlit-mic-recorder",
                icon="ℹ️",
            )
        return None

    except ImportError:
        # Simple fallback button
        if st.button(
            "🎤",
            key="voice_btn",
            help=t("chat.voice_button"),
            use_container_width=True,
        ):
            st.toast(t("chat.voice_listening"), icon="🎤")
        return None


def add_message(
    messages: list[dict[str, Any]],
    role: str,
    content: str,
) -> list[dict[str, Any]]:
    """Add a message to the message list.

    Args:
        messages: Existing message list
        role: Message role ('user', 'assistant', 'system')
        content: Message content

    Returns:
        Updated message list

    """
    messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now(tz=UTC).strftime("%H:%M"),
    })
    return messages
