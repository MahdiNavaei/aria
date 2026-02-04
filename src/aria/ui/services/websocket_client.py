"""WebSocket Client for ARIA UI - real-time updates from backend."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from aria.config import get_settings

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket client for real-time updates."""

    def __init__(
        self,
        url: str | None = None,
        on_message: Callable[[dict[str, Any]], None] | None = None,
        on_connect: Callable[[], None] | None = None,
        on_disconnect: Callable[[], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        """Initialize WebSocket client.

        Args:
            url: WebSocket URL. Defaults to settings.
            on_message: Callback for received messages
            on_connect: Callback on connection
            on_disconnect: Callback on disconnection
            on_error: Callback on error

        """
        settings = get_settings()
        self.url = url or f"ws://{settings.api.host}:{settings.api.port}/ws"

        self.on_message = on_message
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_error = on_error

        self._websocket: websockets.WebSocketClientProtocol | None = None
        self._running = False
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10
        self._reconnect_delay = 3  # seconds

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._websocket is not None and self._websocket.open

    async def connect(self) -> None:
        """Connect to WebSocket server."""
        try:
            self._websocket = await websockets.connect(
                self.url,
                ping_interval=30,
                ping_timeout=10,
            )
            self._running = True
            self._reconnect_attempts = 0

            logger.info("WebSocket connected", extra={"url": self.url})

            if self.on_connect:
                self.on_connect()

            # Start listening
            await self._listen()

        except (OSError, WebSocketException) as exc:
            logger.warning(
                "WebSocket connection failed",
                extra={"error": str(exc), "url": self.url},
            )
            if self.on_error:
                self.on_error(exc)
            await self._reconnect()

    async def _listen(self) -> None:
        """Listen for messages."""
        if not self._websocket:
            return

        try:
            async for message in self._websocket:
                try:
                    data = json.loads(message)
                    if self.on_message:
                        self.on_message(data)
                except json.JSONDecodeError as exc:
                    logger.warning(
                        "Invalid JSON message",
                        extra={"error": str(exc), "message": message[:100]},
                    )
        except ConnectionClosed:
            logger.info("WebSocket connection closed")
            if self.on_disconnect:
                self.on_disconnect()
            if self._running:
                await self._reconnect()

    async def _reconnect(self) -> None:
        """Attempt to reconnect."""
        if not self._running:
            return

        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.error("Max reconnect attempts reached")
            self._running = False
            return

        self._reconnect_attempts += 1
        delay = self._reconnect_delay * (2 ** (self._reconnect_attempts - 1))
        delay = min(delay, 60)  # Cap at 60 seconds

        logger.info(
            "Reconnecting",
            extra={
                "attempt": self._reconnect_attempts,
                "delay": delay,
            },
        )

        await asyncio.sleep(delay)
        await self.connect()

    async def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        self._running = False
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
            logger.info("WebSocket disconnected")
            if self.on_disconnect:
                self.on_disconnect()

    async def send(self, message: dict[str, Any]) -> None:
        """Send a message.

        Args:
            message: Message dict to send

        """
        if not self._websocket or not self._websocket.open:
            logger.warning("Cannot send: not connected")
            return

        try:
            await self._websocket.send(json.dumps(message))
        except WebSocketException as exc:
            logger.exception("Failed to send message", extra={"error": str(exc)})
            if self.on_error:
                self.on_error(exc)

    async def subscribe(self, topics: list[str]) -> None:
        """Subscribe to topics.

        Args:
            topics: List of topic names (screenshot, events, hitl, etc.)

        """
        await self.send({
            "type": "subscribe",
            "topics": topics,
        })

    async def send_command(self, command: str, payload: dict[str, Any] | None = None) -> None:
        """Send a command to the agent.

        Args:
            command: Command name (start, pause, resume, stop)
            payload: Optional command payload

        """
        await self.send({
            "type": "command",
            "command": command,
            "payload": payload or {},
        })

    async def send_hitl_response(
        self,
        action: str,
        reason: str | None = None,
    ) -> None:
        """Send HITL response.

        Args:
            action: Response action (approve, reject, completed, retry)
            reason: Optional rejection reason

        """
        await self.send({
            "type": "hitl_response",
            "action": action,
            "reason": reason,
        })

    async def send_chat_message(self, content: str) -> None:
        """Send chat message to agent.

        Args:
            content: Message content

        """
        await self.send({
            "type": "human_action",
            "action": "chat",
            "content": content,
        })


def create_streamlit_ws_handler(
    on_screenshot: Callable[[str], None] | None = None,
    on_event: Callable[[dict[str, Any]], None] | None = None,
    on_hitl_request: Callable[[dict[str, Any]], None] | None = None,
    on_step_update: Callable[[dict[str, Any]], None] | None = None,
    on_status_change: Callable[[str], None] | None = None,
) -> Callable[[dict[str, Any]], None]:
    """Create a message handler for Streamlit UI.

    Args:
        on_screenshot: Handler for screenshot updates
        on_event: Handler for events
        on_hitl_request: Handler for HITL requests
        on_step_update: Handler for step updates
        on_status_change: Handler for status changes

    Returns:
        Message handler function

    """

    def handler(message: dict[str, Any]) -> None:
        msg_type = message.get("type")

        if msg_type == "screenshot" and on_screenshot:
            on_screenshot(message.get("data", ""))

        elif msg_type == "event" and on_event:
            on_event(message.get("data", {}))

        elif msg_type == "hitl_request" and on_hitl_request:
            on_hitl_request(message.get("data", {}))

        elif msg_type == "step_update" and on_step_update:
            on_step_update(message.get("data", {}))

        elif msg_type == "status" and on_status_change:
            on_status_change(message.get("status", "idle"))

    return handler
