import asyncio
import json
from datetime import datetime
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections and channel subscriptions for real-time updates."""
    def __init__(self):
        # Map of client IDs to WebSocket connections
        self.active_connections: Dict[str, WebSocket] = {}
        # Map of channels to sets of subscribed client IDs
        self.subscriptions: Dict[str, Set[str]] = {
            "threats": set(),
            "events": set(),
            "alerts": set(),
            "scans": set(),
            "all": set()  # All clients receive messages on "all" channel
        }
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept WebSocket connection and register client."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions["all"].add(client_id)  # Subscribe to all by default
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        """Remove client connection and all subscriptions."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # Remove from all subscription channels
        for channel in self.subscriptions.values():
            channel.discard(client_id)
        
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    def subscribe(self, client_id: str, channel: str):
        """Subscribe client to a specific channel."""
        if channel in self.subscriptions:
            self.subscriptions[channel].add(client_id)
            logger.debug(f"Client {client_id} subscribed to {channel}")
    
    def unsubscribe(self, client_id: str, channel: str):
        """Unsubscribe client from a specific channel."""
        if channel in self.subscriptions:
            self.subscriptions[channel].discard(client_id)
            logger.debug(f"Client {client_id} unsubscribed from {channel}")
    
    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to a specific client."""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to {client_id}: {e}")
                self.disconnect(client_id)  # Remove on error
    
    async def broadcast(self, message: dict, channel: str = "all"):
        """Broadcast message to all clients subscribed to the channel."""
        # Include both channel subscribers and "all" subscribers
        clients = self.subscriptions.get(channel, set()) | self.subscriptions.get("all", set())
        
        # Send to all clients, remove disconnected ones
        for client_id in clients.copy():
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    self.disconnect(client_id)  # Remove on error


manager = ConnectionManager()


@router.websocket("/connect/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates with channel subscription support."""
    await manager.connect(websocket, client_id)
    
    try:
        # Send welcome message on connection
        await manager.send_personal_message({
            "type": "connected",
            "message": "Welcome to CyberNexus real-time feed",
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": client_id
        }, client_id)
        
        # Handle client messages (subscribe, unsubscribe, ping)
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "subscribe":
                # Subscribe to a specific channel
                channel = message.get("channel")
                if channel:
                    manager.subscribe(client_id, channel)
                    await manager.send_personal_message({
                        "type": "subscribed",
                        "channel": channel,
                        "timestamp": datetime.utcnow().isoformat()
                    }, client_id)
            
            elif message.get("action") == "unsubscribe":
                # Unsubscribe from a channel
                channel = message.get("channel")
                if channel:
                    manager.unsubscribe(client_id, channel)
                    await manager.send_personal_message({
                        "type": "unsubscribed",
                        "channel": channel,
                        "timestamp": datetime.utcnow().isoformat()
                    }, client_id)
            
            elif message.get("action") == "ping":
                # Respond to keepalive ping
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
    """Broadcast threat data to clients subscribed to threats channel."""
    await manager.broadcast({
        "type": "threat",
        "data": threat_data,
        "timestamp": datetime.utcnow().isoformat()
    }, "threats")


async def broadcast_event(event_data: dict):
    """Broadcast event data to clients subscribed to events channel."""
    await manager.broadcast({
        "type": "event",
        "data": event_data,
        "timestamp": datetime.utcnow().isoformat()
    }, "events")


async def broadcast_alert(alert_data: dict):
    """Broadcast alert data to clients subscribed to alerts channel."""
    await manager.broadcast({
        "type": "alert",
        "data": alert_data,
        "timestamp": datetime.utcnow().isoformat()
    }, "alerts")


async def broadcast_scan_progress(scan_data: dict):
    """Broadcast scan progress to clients subscribed to scans channel."""
    await manager.broadcast({
        "type": "scan_progress",
        "data": scan_data,
        "timestamp": datetime.utcnow().isoformat()
    }, "scans")


async def send_periodic_stats():
    """Send periodic statistics to all connected clients (every 30 seconds)."""
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


