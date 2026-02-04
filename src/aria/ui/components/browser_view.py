"""Browser view component - Live browser preview with controls."""

from __future__ import annotations

import base64
import io
import logging
from typing import Any

import streamlit as st
from PIL import Image

from aria.ui.i18n import t

logger = logging.getLogger(__name__)


def _try_fetch_screenshot() -> tuple[str | None, dict[str, Any] | None]:
    """Try to fetch screenshot from WebSocket or API.

    Returns:
        Tuple of (screenshot_base64, page_info) or (None, None)

    """
    try:
        from aria.ui.hooks.use_websocket import connect_websocket, handle_ws_message

        # Try WebSocket first
        message = connect_websocket(
            session_id=st.session_state.get("session_id"),
            key="browser_ws",
        )

        if message:
            handle_ws_message(message)
            return (
                st.session_state.get("screenshot_base64"),
                st.session_state.get("page_info"),
            )
    except Exception as exc:
        logger.debug("WebSocket screenshot fetch failed", exc_info=exc)

    return None, None


def render_browser_view(
    screenshot_base64: str | None,
    page_info: dict[str, Any] | None = None,
    auto_refresh: bool = False,
) -> None:
    """Render live browser view with screenshot.

    Args:
        screenshot_base64: Base64 encoded screenshot image
        page_info: Dictionary with page information (url, title, etc.)
        auto_refresh: Whether to auto-fetch updates via WebSocket

    """
    st.subheader(t("browser.title"))

    # Try to get fresh screenshot if auto_refresh enabled
    if auto_refresh and st.session_state.get("status") == "running":
        fresh_screenshot, fresh_page_info = _try_fetch_screenshot()
        if fresh_screenshot:
            screenshot_base64 = fresh_screenshot
            page_info = fresh_page_info

    # URL bar
    if page_info:
        url = page_info.get("url", "")
        title = page_info.get("title", "")

        st.markdown(
            f"""
            <div style="
                background: var(--color-bg-secondary);
                border: 1px solid var(--color-border-light);
                border-radius: var(--radius-md);
                padding: var(--space-2) var(--space-3);
                margin-bottom: var(--space-3);
                display: flex;
                align-items: center;
                gap: var(--space-2);
            ">
                <span style="color: var(--color-success);">🔒</span>
                <span style="
                    color: var(--color-text-secondary);
                    font-size: var(--font-size-sm);
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    direction: ltr;
                ">{url or t('browser.no_view')}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if title:
            st.caption(f"📄 {title}")

    # Screenshot container
    if screenshot_base64:
        try:
            img_data = base64.b64decode(screenshot_base64)
            img = Image.open(io.BytesIO(img_data))

            # Display with border and shadow
            st.markdown(
                """
                <style>
                .browser-screenshot img {
                    border: 1px solid var(--color-border-light);
                    border-radius: var(--radius-lg);
                    box-shadow: var(--shadow-lg);
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

            st.image(
                img,
                use_container_width=True,
                caption=None,
            )

        except Exception as exc:  # noqa: BLE001
            st.error(f"❌ {t('error.generic')}: {exc}")
    else:
        # Empty state
        st.markdown(
            f"""
            <div style="
                background: var(--color-bg-secondary);
                border: 2px dashed var(--color-border-medium);
                border-radius: var(--radius-lg);
                padding: var(--space-12) var(--space-6);
                text-align: center;
            ">
                <div style="font-size: 3rem; margin-bottom: var(--space-3);">🌐</div>
                <p style="color: var(--color-text-secondary); margin: 0;">
                    {t('browser.no_view')}
                </p>
                <p style="color: var(--color-text-muted); font-size: var(--font-size-sm); margin-top: var(--space-2);">
                    {t('browser.no_view_hint')}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_browser_controls() -> tuple[str, str] | str | None:
    """Render browser control buttons.

    Returns:
        Action string or tuple (action, value) if user clicked a button

    """
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 3, 1])

    with col1:
        if st.button(
            "🔄",
            key="browser_refresh",
            help=t("browser.refresh"),
            use_container_width=True,
        ):
            return "refresh"

    with col2:
        if st.button(
            "◀️",
            key="browser_back",
            help=t("browser.back"),
            use_container_width=True,
        ):
            return "back"

    with col3:
        if st.button(
            "▶️",
            key="browser_forward",
            help=t("browser.forward"),
            use_container_width=True,
        ):
            return "forward"

    with col4:
        url = st.text_input(
            "URL",
            placeholder=t("browser.url_placeholder"),
            key="browser_url_input",
            label_visibility="collapsed",
        )
        if url:
            return ("navigate", url)

    with col5:
        if st.button(
            "📷",
            key="browser_screenshot",
            help=t("browser.screenshot"),
            use_container_width=True,
        ):
            return "screenshot"

    return None
