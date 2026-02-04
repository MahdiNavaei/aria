"""WebSocket helper for Streamlit real-time updates.

This module provides WebSocket connectivity for Streamlit apps.
It uses streamlit-websocket-client if available, otherwise falls back to polling.
"""

from __future__ import annotations

import json
import logging
import queue
import threading
import time
from typing import Any

import streamlit as st

from aria.config import get_settings

logger = logging.getLogger(__name__)

# Try to import streamlit-websocket-client
_WS_CLIENT_AVAILABLE = False
try:
    from streamlit_ws_client import ws_client

    _WS_CLIENT_AVAILABLE = True
except ImportError:
    logger.info("streamlit-websocket-client not installed. Using polling fallback.")


def get_ws_url(session_id: str | None = None) -> str:
    """Get WebSocket URL for connection.

    Args:
        session_id: Optional session ID to include in URL

    Returns:
        WebSocket URL string

    """
    settings = get_settings()
    host = settings.api.host
    port = settings.api.port

    url = f"ws://{host}:{port}/ws"
    if session_id:
        url = f"{url}?session_id={session_id}"

    return url


def connect_websocket(
    session_id: str | None = None,
    key: str = "aria_ws",
) -> dict[str, Any] | None:
    """Connect to WebSocket and get latest message.

    Args:
        session_id: Session ID for filtering messages
        key: Streamlit component key

    Returns:
        Latest message from WebSocket or None

    """
    if _WS_CLIENT_AVAILABLE:
        return _connect_native(session_id, key)

    return _connect_polling(session_id, key)


def _connect_native(
    session_id: str | None,
    key: str,
) -> dict[str, Any] | None:
    """Connect using native WebSocket client.

    Args:
        session_id: Session ID
        key: Component key

    Returns:
        Latest message or None

    """
    url = get_ws_url(session_id)

    try:
        message = ws_client(url=url, key=key)

        if message:
            # Parse JSON message
            if isinstance(message, str):
                return json.loads(message)
            return message
    except Exception as exc:
        logger.debug("WebSocket connection failed", exc_info=exc)

    return None


def _connect_polling(
    session_id: str | None,
    key: str,
) -> dict[str, Any] | None:
    """Fallback: Poll API for updates instead of WebSocket.

    Args:
        session_id: Session ID
        key: State key

    Returns:
        Latest update or None

    """
    # Store last poll time in session state
    poll_key = f"{key}_last_poll"
    if poll_key not in st.session_state:
        st.session_state[poll_key] = 0

    # Only poll every 2 seconds
    now = time.time()
    if now - st.session_state[poll_key] < 2:
        return st.session_state.get(f"{key}_last_message")

    st.session_state[poll_key] = now

    try:
        from aria.ui.services.api_client import APIClient

        client = APIClient()

        # Get task status if we have a task ID
        if session_id and st.session_state.get("task_id"):
            task = client.get_task(st.session_state.task_id)
            if task and not task.get("error"):
                message = {
                    "type": "task_update",
                    "data": task,
                }
                st.session_state[f"{key}_last_message"] = message
                return message
    except Exception as exc:
        logger.debug("Polling fallback failed", exc_info=exc)

    return None


def send_ws_message(
    message: dict[str, Any],
    key: str = "aria_ws",
) -> bool:
    """Send message through WebSocket.

    Args:
        message: Message to send
        key: WebSocket key

    Returns:
        True if sent successfully

    """
    if not _WS_CLIENT_AVAILABLE:
        # Fallback: send via API
        return _send_via_api(message)

    # Native WebSocket send would go here
    # streamlit-websocket-client doesn't support sending directly
    # So we fallback to API
    return _send_via_api(message)


def _send_via_api(message: dict[str, Any]) -> bool:
    """Send message via REST API fallback.

    Args:
        message: Message to send

    Returns:
        True if successful

    """
    try:
        from aria.ui.services.api_client import APIClient

        client = APIClient()
        msg_type = message.get("type", "")

        if msg_type == "command":
            cmd = message.get("command", "")
            task_id = st.session_state.get("task_id")

            if cmd == "pause" and task_id:
                result = client.pause_task(task_id)
                return not result.get("error")
            elif cmd == "resume" and task_id:
                result = client.resume_task(task_id)
                return not result.get("error")
            elif cmd == "stop" and task_id:
                result = client.stop_task(task_id)
                return not result.get("error")

        elif msg_type == "hitl_response":
            task_id = st.session_state.get("task_id")
            if task_id:
                result = client.submit_hitl_response(
                    task_id,
                    message.get("action", "approve"),
                    message.get("data"),
                )
                return not result.get("error")

        return False

    except Exception as exc:
        logger.error("Failed to send via API", exc_info=exc)
        return False


def disconnect_websocket(key: str = "aria_ws") -> None:
    """Disconnect WebSocket.

    Args:
        key: WebSocket key

    """
    # Clean up session state
    for state_key in list(st.session_state.keys()):
        if state_key.startswith(f"{key}_"):
            del st.session_state[state_key]


def is_ws_connected(key: str = "aria_ws") -> bool:
    """Check if WebSocket is connected.

    Args:
        key: WebSocket key

    Returns:
        True if connected

    """
    return st.session_state.get(f"{key}_connected", False)


def get_ws_message(key: str = "aria_ws") -> dict[str, Any] | None:
    """Get the last WebSocket message.

    Args:
        key: WebSocket key

    Returns:
        Last message or None

    """
    return st.session_state.get(f"{key}_last_message")


def handle_ws_message(
    message: dict[str, Any],
    handlers: dict[str, Any] | None = None,
) -> None:
    """Handle incoming WebSocket message.

    Args:
        message: WebSocket message
        handlers: Optional dict of type -> handler function

    """
    if not message:
        return

    msg_type = message.get("type", "")

    # Update session state based on message type
    if msg_type == "screenshot":
        st.session_state.screenshot_base64 = message.get("data", {}).get("image")
        st.session_state.page_info = message.get("data", {}).get("page_info")

    elif msg_type == "event":
        event = message.get("data", {})
        if "events" not in st.session_state:
            st.session_state.events = []
        st.session_state.events.insert(0, event)
        st.session_state.events = st.session_state.events[:50]  # Keep last 50

    elif msg_type == "hitl_request":
        st.session_state.hitl_request = message.get("data")

    elif msg_type == "status":
        st.session_state.status = message.get("data", {}).get("status", "idle")

    elif msg_type == "step":
        st.session_state.current_step = message.get("data")

    elif msg_type == "task_update":
        data = message.get("data", {})
        st.session_state.status = data.get("status", "idle")
        if data.get("current_step"):
            st.session_state.current_step = data["current_step"]
        if data.get("hitl_request"):
            st.session_state.hitl_request = data["hitl_request"]

    # Call custom handlers
    if handlers and msg_type in handlers:
        handlers[msg_type](message.get("data"))
