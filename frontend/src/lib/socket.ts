"use client";

import { io, Socket } from "socket.io-client";
import { create } from "zustand";

// Types
export interface ThreatUpdate {
  id: string;
  type: "new" | "update" | "resolved";
  threat: {
    name: string;
    severity: "critical" | "high" | "medium" | "low";
    source: string;
  };
  timestamp: Date;
}

export interface NotificationEvent {
  id: string;
  type: "critical" | "high" | "medium" | "low" | "info" | "success";
  title: string;
  message: string;
  timestamp: Date;
  actionUrl?: string;
}

export interface CollectorStatusUpdate {
  collectorId: string;
  status: "running" | "paused" | "error" | "idle";
  itemsCollected?: number;
  lastUpdate: Date;
}

// Socket Store
interface SocketState {
  socket: Socket | null;
  isConnected: boolean;
  threats: ThreatUpdate[];
  notifications: NotificationEvent[];
  collectorStatuses: Map<string, CollectorStatusUpdate>;
  connect: () => void;
  disconnect: () => void;
  subscribe: (event: string, callback: (data: any) => void) => () => void;
}

export const useSocket = create<SocketState>((set, get) => ({
  socket: null,
  isConnected: false,
  threats: [],
  notifications: [],
  collectorStatuses: new Map(),

  connect: () => {
    const { socket } = get();
    if (socket?.connected) return;

    const newSocket = io(process.env.NEXT_PUBLIC_WS_URL || "http://localhost:8000", {
      transports: ["websocket", "polling"],
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      autoConnect: true,
    });

    newSocket.on("connect", () => {
      console.log("WebSocket connected");
      set({ isConnected: true });
    });

    newSocket.on("disconnect", () => {
      console.log("WebSocket disconnected");
      set({ isConnected: false });
    });

    newSocket.on("connect_error", (error) => {
      console.error("WebSocket connection error:", error);
      set({ isConnected: false });
    });

    // Listen for threat updates
    newSocket.on("threat:update", (data: ThreatUpdate) => {
      set((state) => ({
        threats: [data, ...state.threats].slice(0, 100),
      }));
    });

    // Listen for notifications
    newSocket.on("notification", (data: NotificationEvent) => {
      set((state) => ({
        notifications: [data, ...state.notifications].slice(0, 50),
      }));
    });

    // Listen for collector status updates
    newSocket.on("collector:status", (data: CollectorStatusUpdate) => {
      set((state) => {
        const newStatuses = new Map(state.collectorStatuses);
        newStatuses.set(data.collectorId, data);
        return { collectorStatuses: newStatuses };
      });
    });

    set({ socket: newSocket });
  },

  disconnect: () => {
    const { socket } = get();
    if (socket) {
      socket.disconnect();
      set({ socket: null, isConnected: false });
    }
  },

  subscribe: (event: string, callback: (data: any) => void) => {
    const { socket } = get();
    if (socket) {
      socket.on(event, callback);
      return () => socket.off(event, callback);
    }
    return () => {};
  },
}));

// Hook for using socket with auto-connect
export function useSocketConnection() {
  const { connect, disconnect, isConnected } = useSocket();

  // Auto-connect on mount
  if (typeof window !== "undefined" && !isConnected) {
    connect();
  }

  return { isConnected, connect, disconnect };
}

// Hook for threat updates
export function useThreatUpdates() {
  const threats = useSocket((state) => state.threats);
  const subscribe = useSocket((state) => state.subscribe);

  return {
    threats,
    onNewThreat: (callback: (threat: ThreatUpdate) => void) =>
      subscribe("threat:update", callback),
  };
}

// Hook for notifications
export function useSocketNotifications() {
  const notifications = useSocket((state) => state.notifications);
  const subscribe = useSocket((state) => state.subscribe);

  return {
    notifications,
    onNotification: (callback: (notification: NotificationEvent) => void) =>
      subscribe("notification", callback),
  };
}

// Hook for collector statuses
export function useCollectorStatuses() {
  const collectorStatuses = useSocket((state) => state.collectorStatuses);
  const subscribe = useSocket((state) => state.subscribe);

  return {
    statuses: collectorStatuses,
    onStatusUpdate: (callback: (status: CollectorStatusUpdate) => void) =>
      subscribe("collector:status", callback),
  };
}


