"""
SSE (Server-Sent Events) manager — broadcasts XP updates to all connected clients.

Uses threading primitives so that sync FastAPI routes (def, not async def)
can safely broadcast without needing an asyncio event loop.

Usage:
    from sse import sse_manager
    sse_manager.broadcast_sync({"type": "xp_update", "userId": "...", ...})
"""

import json
import threading
import logging

logger = logging.getLogger(__name__)


class SSEClient:
    """A single connected SSE client with a thread-safe message buffer."""

    def __init__(self):
        self.messages: list[str] = []
        self.lock = threading.Lock()
        self.event = threading.Event()

    def put(self, message: str):
        with self.lock:
            self.messages.append(message)
        self.event.set()

    def get_all(self) -> list[str]:
        with self.lock:
            msgs = self.messages[:]
            self.messages.clear()
        self.event.clear()
        return msgs


class SSEManager:
    """Manages connected SSE clients and broadcasts events."""

    def __init__(self):
        self._clients: list[SSEClient] = []
        self._lock = threading.Lock()

    def connect(self) -> SSEClient:
        """Register a new client."""
        client = SSEClient()
        with self._lock:
            self._clients.append(client)
            count = len(self._clients)
        logger.info(f"SSE client connected — {count} total")
        return client

    def disconnect(self, client: SSEClient):
        """Unregister a client."""
        with self._lock:
            if client in self._clients:
                self._clients.remove(client)
            count = len(self._clients)
        logger.info(f"SSE client disconnected — {count} total")

    def broadcast_sync(self, data: dict):
        """Send an event to all connected clients. Safe to call from sync code."""
        message = json.dumps(data)
        with self._lock:
            for client in self._clients:
                client.put(message)
        logger.info(f"SSE broadcast to {len(self._clients)} clients: {data.get('type', '?')}")


# Singleton
sse_manager = SSEManager()

