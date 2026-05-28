"""
WebSocket connection hub.

Manages all active support agent connections and handles message routing.
Thread-safe under asyncio single-thread execution model.
"""

from fastapi import WebSocket
from typing import Dict, Optional
import json


class WSHub:
    def __init__(self) -> None:
        self._connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        await websocket.accept()
        self._connections[client_id] = websocket

    def disconnect(self, client_id: str) -> None:
        self._connections.pop(client_id, None)

    async def send_to(self, client_id: str, payload: dict) -> None:
        ws = self._connections.get(client_id)
        if ws:
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                self.disconnect(client_id)

    async def broadcast(self, payload: dict) -> None:
        dead = []
        for cid, ws in self._connections.items():
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead.append(cid)
        for cid in dead:
            self.disconnect(cid)

    @property
    def active_count(self) -> int:
        return len(self._connections)


ws_hub = WSHub()
