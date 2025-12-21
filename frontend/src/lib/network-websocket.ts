"use client";

// Type declaration for process.env in client components
declare const process: { env: { NEXT_PUBLIC_API_URL?: string } };

// Get WebSocket URL from API URL
function getWebSocketUrl(): string {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
  // Convert http/https to ws/wss
  const wsUrl = apiUrl
    .replace(/^http:/, 'ws:')
    .replace(/^https:/, 'wss:');
  return wsUrl;
}

export interface NetworkLogEntry {
  id: string;
  timestamp: string;
  ip: string;
  method: string;
  path: string;
  query: string;
  headers: Record<string, string>;
  body: string;
  body_size: number;
  body_truncated: boolean;
  user_agent: string;
  referer: string;
  status: number;
  response_headers: Record<string, string>;
  response_body: string;
  response_body_size: number;
  response_body_truncated: boolean;
  response_time_ms: number;
  tunnel_detection?: {
    detected: boolean;
    tunnel_type: string;
    confidence: string;
    risk_score: number;
    indicators: string[];
    detection_id: string;
  };
}

export interface TunnelAlert {
  detected: boolean;
  tunnel_type: string;
  confidence: string;
  risk_score: number;
  indicators: string[];
  detection_id: string;
}

export interface NetworkWebSocketMessage {
  type: "log" | "tunnel_alert" | "stats_update" | "block_added" | "connected" | "pong";
  data: any;
}

export interface NetworkWebSocketCallbacks {
  onLog?: (log: NetworkLogEntry) => void;
  onTunnelAlert?: (alert: TunnelAlert) => void;
  onStatsUpdate?: (stats: any) => void;
  onBlockAdded?: (block: any) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: string) => void;
}

export function connectNetworkWebSocket(
  callbacks: NetworkWebSocketCallbacks
): WebSocket | null {
  const wsUrl = getWebSocketUrl();
  const url = `${wsUrl}/network/ws`;
  
  try {
    const ws = new WebSocket(url);

    ws.onopen = () => {
      console.log("[Network WebSocket] Connected");
      callbacks.onConnect?.();
    };

    ws.onmessage = (event) => {
      try {
        const message: NetworkWebSocketMessage = JSON.parse(event.data);
        console.log(`[Network WebSocket] Received message type: ${message.type}`, message);
        
        switch (message.type) {
          case "log":
            callbacks.onLog?.(message.data);
            break;
          case "tunnel_alert":
            callbacks.onTunnelAlert?.(message.data);
            break;
          case "stats_update":
            callbacks.onStatsUpdate?.(message.data);
            break;
          case "block_added":
            callbacks.onBlockAdded?.(message.data);
            break;
          case "connected":
            console.log("[Network WebSocket] Connection confirmed");
            break;
          case "pong":
            // Heartbeat response
            break;
          default:
            console.warn("[Network WebSocket] Unknown message type:", message.type, message);
        }
      } catch (err) {
        console.error("[Network WebSocket] Error parsing message:", err, event.data);
      }
    };

    ws.onerror = (error) => {
      console.error("[Network WebSocket] Error:", error);
      callbacks.onError?.("WebSocket connection error");
    };

    ws.onclose = () => {
      console.log("[Network WebSocket] Disconnected");
      callbacks.onDisconnect?.();
    };

    // Send ping every 30 seconds to keep connection alive
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "ping" }));
      } else {
        clearInterval(pingInterval);
      }
    }, 30000);

    // Store interval on WebSocket for cleanup
    (ws as any).pingInterval = pingInterval;

    return ws;
  } catch (err) {
    console.error("[Network WebSocket] Failed to create connection:", err);
    callbacks.onError?.("Failed to create WebSocket connection");
    return null;
  }
}

export function disconnectNetworkWebSocket(ws: WebSocket | null): void {
  if (ws) {
    // Clear ping interval
    if ((ws as any).pingInterval) {
      clearInterval((ws as any).pingInterval);
    }
    ws.close();
  }
}




