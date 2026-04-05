from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Dict, Set

from fastapi import WebSocket


class WSManager:
    def __init__(self):
        self._clients: Dict[str, Set[WebSocket]] = defaultdict(set)

    async def connect(self, company_id: str, websocket: WebSocket):
        await websocket.accept()
        self._clients[company_id].add(websocket)

    def disconnect(self, company_id: str, websocket: WebSocket):
        if company_id in self._clients and websocket in self._clients[company_id]:
            self._clients[company_id].remove(websocket)
        if company_id in self._clients and not self._clients[company_id]:
            self._clients.pop(company_id, None)

    async def send_json(self, company_id: str, payload: dict):
        clients = list(self._clients.get(company_id, set()))
        stale = []
        for ws in clients:
            try:
                await ws.send_json(payload)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(company_id, ws)

    def publish_alert(self, company_id: str, payload: dict):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.send_json(company_id, payload))
                return
        except RuntimeError:
            pass


manager = WSManager()
