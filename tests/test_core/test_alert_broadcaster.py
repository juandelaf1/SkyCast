import asyncio
import json
from app.core.alert_broadcaster import AlertBroadcaster


class TestAlertBroadcaster:
    def test_connect_disconnect(self):
        b = AlertBroadcaster()
        queue = asyncio.Queue()
        b._connections.add(queue)
        assert b.active_connections == 1
        b.disconnect(queue)
        assert b.active_connections == 0

    def test_broadcast_delivers_to_all(self):
        b = AlertBroadcaster()
        q1 = asyncio.Queue()
        q2 = asyncio.Queue()
        b._connections.add(q1)
        b._connections.add(q2)

        asyncio.run(b.broadcast({"tipo": "alerta", "nivel": "rojo"}))

        msg1 = asyncio.run(q1.get())
        msg2 = asyncio.run(q2.get())
        assert json.loads(msg1)["nivel"] == "rojo"
        assert json.loads(msg2)["nivel"] == "rojo"

    def test_connect_returns_queue(self):
        b = AlertBroadcaster()
        result = asyncio.run(b.connect())
        assert isinstance(result, asyncio.Queue)
        assert b.active_connections == 1

    def test_broadcast_empty_no_crash(self):
        b = AlertBroadcaster()
        asyncio.run(b.broadcast({"msg": "sin conexiones"}))

    def test_disconnect_unknown_no_crash(self):
        b = AlertBroadcaster()
        b.disconnect(asyncio.Queue())
