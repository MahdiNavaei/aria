from fastapi.testclient import TestClient

from aria.api.websocket.server import app


def test_websocket_connect() -> None:
    with TestClient(app) as client, client.websocket_connect("/ws") as websocket:
        connected = websocket.receive_json()
        assert connected.get("type") == "connected"

        websocket.send_json({"type": "subscribe", "topics": ["*"]})
        response = websocket.receive_json()
        assert response.get("type") == "subscribed"
