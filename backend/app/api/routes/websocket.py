import asyncio
import json
from datetime import datetime
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {
            "threats": set(),
            "events": set(),
            "alerts": set(),
            "scans": set(),
            "all": set()
        }
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions["all"].add(client_id)
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        for channel in self.subscriptions.values():
            channel.discard(client_id)
        
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    def subscribe(self, client_id: str, channel: str):
        if channel in self.subscriptions:
            self.subscriptions[channel].add(client_id)
            logger.debug(f"Client {client_id} subscribed to {channel}")
    
    def unsubscribe(self, client_id: str, channel: str):
        if channel in self.subscriptions:
            self.subscriptions[channel].discard(client_id)
            logger.debug(f"Client {client_id} unsubscribed from {channel}")
    
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: dict, channel: str = "all"):
        clients = self.subscriptions.get(channel, set()) | self.subscriptions.get("all", set())
        
        for client_id in clients.copy():
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    self.disconnect(client_id)


manager = ConnectionManager()


@router.websocket("/connect/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    try:
        await manager.send_personal_message({
            "type": "connected",
            "message": "Welcome to CyberNexus real-time feed",
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": client_id
        }, client_id)
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "subscribe":
                channel = message.get("channel")
                if channel:
                    manager.subscribe(client_id, channel)
                    await manager.send_personal_message({
                        "type": "subscribed",
                        "channel": channel,
                        "timestamp": datetime.utcnow().isoformat()
                    }, client_id)
            
            elif message.get("action") == "unsubscribe":
                channel = message.get("channel")
                if channel:
                    manager.unsubscribe(client_id, channel)
                    await manager.send_personal_message({
                        "type": "unsubscribed",
                        "channel": channel,
                        "timestamp": datetime.utcnow().isoformat()
                    }, client_id)
            
            elif message.get("action") == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }, client_id)
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)


async def broadcast_threat(threat_data: dict):
    await manager.broadcast({
        "type": "threat",
        "data": threat_data,
        "timestamp": datetime.utcnow().isoformat()
    }, "threats")


async def broadcast_event(event_data: dict):
    await manager.broadcast({
        "type": "event",
        "data": event_data,
        "timestamp": datetime.utcnow().isoformat()
    }, "events")


async def broadcast_alert(alert_data: dict):
    await manager.broadcast({
        "type": "alert",
        "data": alert_data,
        "timestamp": datetime.utcnow().isoformat()
    }, "alerts")


async def broadcast_scan_progress(scan_data: dict):
    await manager.broadcast({
        "type": "scan_progress",
        "data": scan_data,
        "timestamp": datetime.utcnow().isoformat()
    }, "scans")


async def send_periodic_stats():
    while True:
        await asyncio.sleep(30)
        
        stats = {
            "type": "stats",
            "data": {
                "connected_clients": len(manager.active_connections),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        await manager.broadcast(stats)


