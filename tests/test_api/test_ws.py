from fastapi.testclient import TestClient
from app.main import app


class TestWebSocket:
    def test_websocket_connect(self):
        client = TestClient(app)
        with client.websocket_connect("/alertas") as ws:
            assert ws
