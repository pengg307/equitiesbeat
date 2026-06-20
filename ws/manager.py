"""WebSocket connection manager"""
import asyncio
import json
import logging
from fastapi import WebSocket

log = logging.getLogger(__name__)


class ConnectionManager:
    
    def __init__(self):
        self.active = set()
        self.subscriptions = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, ws):
        await ws.accept()
        async with self._lock:
            self.active.add(ws)
        log.info("WS connected. Total: " + str(len(self.active)))
    
    async def disconnect(self, ws):
        async with self._lock:
            self.active.discard(ws)
            for subs in self.subscriptions.values():
                subs.discard(ws)
        log.info("WS disconnected. Total: " + str(len(self.active)))
    
    async def subscribe(self, ws, market_key):
        async with self._lock:
            if market_key not in self.subscriptions:
                self.subscriptions[market_key] = set()
            for k, subs in self.subscriptions.items():
                if k != market_key:
                    subs.discard(ws)
            self.subscriptions[market_key].add(ws)
        log.info("WS subscribed to " + market_key)
    
    async def broadcast_to_market(self, market_key, message):
        if market_key not in self.subscriptions:
            return
        data = json.dumps(message)
        dead = []
        for ws in list(self.subscriptions[market_key]):
            try:
                await ws.send_text(data)
            except Exception as e:
                log.debug("WS send error: " + str(e))
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)
    
    @property
    def total_connections(self):
        return len(self.active)
