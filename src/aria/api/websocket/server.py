"""WebSocket server for ARIA UI."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from aria.adapters.kafka import get_event_bus
from aria.adapters.redis import get_state_store
from aria.api.websocket.screenshot_stream import get_screenshot_streamer
from aria.config import get_settings
from aria.core.brain import get_brain
from aria.core.brain.nodes.hitl import submit_hitl_response
from aria.models.events import EventEnvelope, EventType
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manage WebSocket connections and subscriptions."""

    def __init__(self, max_connections: int = 100) -> None:
        """Initialize connection manager with a maximum connection limit."""
        self._max_connections = max_connections
        self.active_connections: dict[WebSocket, str] = {}
        self._subscriptions: dict[WebSocket, set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, session_id: str) -> bool:
        """Accept and register a websocket connection."""
        async with self._lock:
            if len(self.active_connections) >= self._max_connections:
                await websocket.close(code=1001)
                return False

            await websocket.accept()
            self.active_connections[websocket] = session_id
            self._subscriptions[websocket] = set()

        logger.info("WebSocket client connected", session_id=session_id)
        return True

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a websocket connection."""
        session_id = self.active_connections.pop(websocket, None)
        self._subscriptions.pop(websocket, None)
        if session_id:
            logger.info("WebSocket client disconnected", session_id=session_id)

    async def subscribe(self, websocket: WebSocket, topics: list[str]) -> None:
        """Subscribe a websocket to topics."""
        if websocket not in self._subscriptions:
            self._subscriptions[websocket] = set()
        self._subscriptions[websocket].update(topics)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return

        disconnected: list[WebSocket] = []
        for connection in list(self.active_connections.keys()):
            try:
                await connection.send_json(message)
            except (RuntimeError, WebSocketDisconnect):
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)

    async def send_to_session(self, session_id: str, message: dict[str, Any]) -> None:
        """Send a message to a specific session."""
        disconnected: list[WebSocket] = []
        for connection, conn_session in self.active_connections.items():
            if conn_session != session_id:
                continue
            try:
                await connection.send_json(message)
            except (RuntimeError, WebSocketDisconnect):
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)

    async def send_to_subscribers(self, topic: str, message: dict[str, Any]) -> None:
        """Send a message to subscribers of a topic."""
        disconnected: list[WebSocket] = []
        for connection, topics in self._subscriptions.items():
            if topic not in topics and "*" not in topics:
                continue
            try:
                await connection.send_json(message)
            except (RuntimeError, WebSocketDisconnect):
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


settings = get_settings().api.websocket
manager = ConnectionManager(max_connections=settings.max_connections)

app = FastAPI(title="ARIA WebSocket API")

# Global flag for event consumer
_event_consumer_task: asyncio.Task[None] | None = None


async def _event_consumer_loop() -> None:
    """Background task that consumes Kafka events and forwards to WebSocket clients.

    Subscribes to relevant topics and broadcasts events to connected clients.
    """
    logger.info("Starting WebSocket event consumer loop")

    # Topics to consume from
    topics = [
        "aria.brain.events",
        "aria.hand.events",
        "aria.eye.events",
        "aria.session.events",
        "aria.hitl.events",
    ]

    try:
        bus = await get_event_bus()

        async def handle_event(event: EventEnvelope) -> None:
            """Handle incoming Kafka event and forward to WebSocket clients."""
            try:
                # Build WebSocket message
                ws_message = {
                    "type": "event",
                    "event_type": event.event_type.value,
                    "session_id": event.session_id,
                    "timestamp": event.timestamp.isoformat(),
                    "data": event.payload,
                }

                # Handle specific event types
                if event.event_type == EventType.EYE_SCREENSHOT_CAPTURED:
                    ws_message["type"] = "screenshot"
                    ws_message["data"] = {
                        "image": event.payload.get("image_base64"),
                        "page_info": {
                            "url": event.payload.get("url"),
                            "title": event.payload.get("title"),
                        },
                    }
                elif event.event_type == EventType.BRAIN_HITL_REQUESTED:
                    ws_message["type"] = "hitl_request"
                elif event.event_type == EventType.BRAIN_STEP_COMPLETED:
                    ws_message["type"] = "step"
                elif event.event_type in (
                    EventType.SESSION_STARTED,
                    EventType.SESSION_ENDED,
                ):
                    ws_message["type"] = "status"
                    ws_message["data"] = {
                        "status": "running" if event.event_type == EventType.SESSION_STARTED else "completed",
                    }

                # Send to session-specific clients first
                if event.session_id:
                    await manager.send_to_session(event.session_id, ws_message)
                else:
                    # Broadcast to all if no session
                    await manager.broadcast(ws_message)

                # Also send to topic subscribers
                topic = f"aria.{event.event_type.value.split('.')[0]}.events"
                await manager.send_to_subscribers(topic, ws_message)

            except Exception as exc:  # noqa: BLE001
                logger.debug("Failed to forward event to WebSocket", error=str(exc))

        # Subscribe to topics and process events
        for topic in topics:
            try:
                # Subscribe returns an async generator
                asyncio.create_task(  # noqa: RUF006
                    _consume_topic(bus, topic, handle_event),
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to subscribe to topic", topic=topic, error=str(exc))

        # Keep running
        while True:
            await asyncio.sleep(1)

    except Exception as exc:
        logger.error("Event consumer loop error", error=str(exc))


async def _consume_topic(
    bus: Any,  # noqa: ANN401
    topic: str,
    handler: Any,  # noqa: ANN401
) -> None:
    """Consume events from a single topic."""
    try:
        async for event in bus.subscribe(topic, handler):
            pass  # Handler is called by subscribe
    except Exception as exc:  # noqa: BLE001
        logger.debug("Topic consumption stopped", topic=topic, error=str(exc))


async def _handle_client_message(
    websocket: WebSocket,
    session_id: str,
    message: dict[str, Any],
) -> None:
    msg_type = message.get("type", "")
    payload = message.get("data", {})

    if msg_type == "subscribe":
        topics = message.get("topics") or payload.get("topics") or ["*"]
        await manager.subscribe(websocket, topics)
        await websocket.send_json({"type": "subscribed", "topics": list(topics)})
        return

    if msg_type == "ping":
        await websocket.send_json({"type": "pong"})
        return

    if msg_type == "command":
        await _handle_command(session_id, payload)
        await websocket.send_json({"type": "ack", "command": payload.get("command")})
        return

    if msg_type == "hitl_response":
        response = payload.get("response") if isinstance(payload.get("response"), dict) else payload
        await submit_hitl_response(session_id, response)
        await websocket.send_json({"type": "ack", "action": "hitl_response"})
        return

    if msg_type in {"chat", "click", "type"}:
        await _emit_human_action(session_id, msg_type, payload)
        await websocket.send_json({"type": "ack", "action": msg_type})
        return

    await websocket.send_json({"type": "error", "message": "unknown_message"})


async def _handle_command(session_id: str, payload: dict[str, Any]) -> None:
    command = payload.get("command")
    if not command:
        return

    if command == "start":
        goal = payload.get("goal")
        if not goal:
            return
        domain = payload.get("domain", "job_apply")
        brain = await get_brain()
        asyncio.create_task(  # noqa: RUF006
            brain.run(goal=goal, domain=domain, session_id=session_id),
        )
        await _update_status_flag(session_id, "running")

        # Start screenshot streaming
        try:
            streamer = get_screenshot_streamer()
            await streamer.start(session_id)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Failed to start screenshot streaming", error=str(exc))
        return

    if command == "stop":
        await _set_control_flag(session_id, command)
        # Stop screenshot streaming
        try:
            streamer = get_screenshot_streamer()
            await streamer.stop()
        except Exception as exc:  # noqa: BLE001
            logger.debug("Failed to stop screenshot streaming", error=str(exc))
        return

    if command in {"pause", "resume"}:
        await _set_control_flag(session_id, command)


async def _set_control_flag(session_id: str, action: str) -> None:
    store = None
    try:
        store = await asyncio.wait_for(get_state_store(), timeout=0.5)
    except Exception as exc:  # noqa: BLE001
        logger.debug("State store unavailable", error=str(exc))
        return

    if action == "pause":
        await store.set_flag(f"pause:{session_id}", value=True)
    elif action == "resume":
        await store.set_flag(f"pause:{session_id}", value=False)
    elif action == "stop":
        await store.set_flag(f"stop:{session_id}", value=True)


async def _update_status_flag(session_id: str, status: str) -> None:
    store = None
    try:
        store = await asyncio.wait_for(get_state_store(), timeout=0.5)
    except Exception as exc:  # noqa: BLE001
        logger.debug("State store unavailable", error=str(exc))
        return

    current = await store.get_session_state(session_id) or {}
    current.update({"status": status})
    await store.set_session_state(session_id, current)


async def _emit_human_action(
    session_id: str,
    action_type: str,
    payload: dict[str, Any],
) -> None:
    event_payload: dict[str, Any] = {"action_type": action_type}

    if action_type == "click":
        coords = {
            "x": payload.get("x"),
            "y": payload.get("y"),
        }
        event_payload["coordinates"] = coords
        if payload.get("semantic_label"):
            event_payload["semantic_label"] = payload.get("semantic_label")
    elif action_type == "type":
        event_payload["text"] = payload.get("text")
        if payload.get("target_ref"):
            event_payload["semantic_label"] = payload.get("target_ref")
    else:
        event_payload["metadata"] = payload

    event = EventEnvelope(
        event_type=EventType.HUMAN_ACTION_RECEIVED,
        session_id=session_id,
        trace_id=session_id,
        payload=event_payload,
    )

    try:
        bus = await get_event_bus()
        await bus.publish(event)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to publish human action", error=str(exc))


async def _websocket_loop(websocket: WebSocket, session_id: str) -> None:
    connected = await manager.connect(websocket, session_id)
    if not connected:
        return

    await websocket.send_json({"type": "connected", "session_id": session_id})

    try:
        while True:
            raw = await websocket.receive_text()
            message = _parse_message(raw)
            await _handle_client_message(websocket, session_id, message)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.exception("WebSocket error", error=str(exc))
        manager.disconnect(websocket)


def _parse_message(raw: str) -> dict[str, Any]:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"type": "invalid", "raw": raw}


@app.on_event("startup")
async def startup_event_consumer() -> None:
    """Start the Kafka event consumer on app startup."""
    global _event_consumer_task  # noqa: PLW0603
    try:
        _event_consumer_task = asyncio.create_task(_event_consumer_loop())
        logger.info("WebSocket event consumer started")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to start event consumer", error=str(exc))


@app.on_event("shutdown")
async def shutdown_event_consumer() -> None:
    """Stop the event consumer on shutdown."""
    global _event_consumer_task  # noqa: PLW0603
    if _event_consumer_task:
        _event_consumer_task.cancel()
        try:
            await _event_consumer_task
        except asyncio.CancelledError:
            pass
        _event_consumer_task = None
        logger.info("WebSocket event consumer stopped")


@app.websocket("/")
async def websocket_root(websocket: WebSocket) -> None:
    """WebSocket endpoint for mounted app (/ws)."""
    session_id = websocket.query_params.get("session_id") or str(uuid4())
    await _websocket_loop(websocket, session_id)


@app.websocket("/ws")
async def websocket_alias(websocket: WebSocket) -> None:
    """Alias endpoint for direct websocket use."""
    session_id = websocket.query_params.get("session_id") or str(uuid4())
    await _websocket_loop(websocket, session_id)


@app.websocket("/session/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: str) -> None:
    """WebSocket endpoint with explicit session id."""
    await _websocket_loop(websocket, session_id)
