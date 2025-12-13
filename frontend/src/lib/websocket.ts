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

export interface WebSocketMessage {
  type: "finding" | "progress" | "complete" | "error";
  data: any;
  timestamp: string;
}

export interface WebSocketCallbacks {
  onFinding?: (finding: any) => void;
  onProgress?: (progress: number, message: string) => void;
  onComplete?: (data: { total_findings: number; urls_crawled: number; total_time_seconds: number }) => void;
  onError?: (error: string) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export function connectDarkwebJobWebSocket(
  jobId: string,
  callbacks: WebSocketCallbacks
): WebSocket | null {
  const wsUrl = getWebSocketUrl();
  const url = `${wsUrl}/capabilities/ws/darkweb/${jobId}`;
  
  try {
    const ws = new WebSocket(url);

    ws.onopen = () => {
      console.log(`[WebSocket] Connected to darkweb job ${jobId}`);
      callbacks.onConnect?.();
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        
        switch (message.type) {
          case "finding":
            callbacks.onFinding?.(message.data);
            break;
          case "progress":
            const progressData = message.data;
            callbacks.onProgress?.(
              progressData.progress || 0,
              progressData.message || ""
            );
            break;
          case "complete":
            callbacks.onComplete?.(message.data);
            ws.close();
            break;
          case "error":
            callbacks.onError?.(message.data.error || "Unknown error");
            ws.close();
            break;
          default:
            console.warn("[WebSocket] Unknown message type:", message.type);
        }
      } catch (err) {
        console.error("[WebSocket] Error parsing message:", err);
      }
    };

    ws.onerror = (error) => {
      console.error(`[WebSocket] Error for job ${jobId}:`, error);
      callbacks.onError?.("WebSocket connection error");
    };

    ws.onclose = () => {
      console.log(`[WebSocket] Disconnected from darkweb job ${jobId}`);
      callbacks.onDisconnect?.();
    };

    return ws;
  } catch (err) {
    console.error(`[WebSocket] Failed to create connection for job ${jobId}:`, err);
    callbacks.onError?.("Failed to create WebSocket connection");
    return null;
  }
}
