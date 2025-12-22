from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from app.middleware.network_logger import get_network_logger_middleware


router = APIRouter()


@router.websocket("/ws")
async def network_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time network log streaming to connected clients."""
    await websocket.accept()
    
    # Register client with network logger middleware
    middleware = get_network_logger_middleware()
    if middleware:
        middleware.register_websocket_client(websocket)
        logger.info(f"Network WebSocket client connected. Total clients: {len(middleware.websocket_clients)}")
    else:
        logger.warning("Network logger middleware not available")
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to network monitoring stream"
        })
        
        # Handle client messages (subscribe, ping/pong)
        while True:
            try:
                data = await websocket.receive_json()
                
                if data.get("type") == "subscribe":
                    # Acknowledge subscription with filters
                    await websocket.send_json({
                        "type": "subscribed",
                        "filters": data.get("filters", {})
                    })
                
                elif data.get("type") == "ping":
                    # Respond to keepalive ping
                    await websocket.send_json({"type": "pong"})
                    
            except Exception as e:
                logger.debug(f"WebSocket receive error: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info("Network WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Network WebSocket error: {e}")
    finally:
        # Clean up client registration on disconnect
        middleware = get_network_logger_middleware()
        if middleware:
            middleware.unregister_websocket_client(websocket)
            logger.info(f"Network WebSocket client removed. Total clients: {len(middleware.websocket_clients)}")


async def broadcast_to_clients(message: dict):
    """Broadcast network log message to all connected WebSocket clients."""
    middleware = get_network_logger_middleware()
    if not middleware:
        return
    
    # Send message to all clients, track disconnected ones
    disconnected = set()
    for client in middleware.websocket_clients:
        try:
            await client.send_json(message)
        except Exception:
            disconnected.add(client)
    
    # Remove disconnected clients
    for client in disconnected:
        middleware.unregister_websocket_client(client)

