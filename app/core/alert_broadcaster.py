import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class AlertBroadcaster:
    def __init__(self):
        self._connections: set[asyncio.Queue] = set()

    async def connect(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._connections.add(queue)
        logger.info(f"WebSocket connected. Total: {len(self._connections)}")
        return queue

    def disconnect(self, queue: asyncio.Queue):
        self._connections.discard(queue)
        logger.info(f"WebSocket disconnected. Total: {len(self._connections)}")

    async def broadcast(self, message: dict[str, Any]):
        payload = json.dumps(message, default=str)
        dead: list[asyncio.Queue] = []
        for q in self._connections:
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self.disconnect(q)

    @property
    def active_connections(self) -> int:
        return len(self._connections)


broadcaster = AlertBroadcaster()
