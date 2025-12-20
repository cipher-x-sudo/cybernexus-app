"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { api } from "./api";

export interface Notification {
  id: string;
  user_id: string | null;
  channel: string;
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";
  title: string;
  message: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  read: boolean;
  read_at: string | null;
  metadata: Record<string, any>;
  timestamp: string;
  created_at: string;
}

interface UseNotificationsOptions {
  pollInterval?: number; // Polling interval in milliseconds (default: 5000)
  limit?: number; // Number of notifications to fetch (default: 50)
  autoPoll?: boolean; // Whether to automatically poll (default: true)
  unreadOnly?: boolean; // Only fetch unread notifications (default: false)
}

interface UseNotificationsReturn {
  notifications: Notification[];
  unreadCount: number;
  loading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
  markAsRead: (id: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
}

/**
 * Hook for fetching and managing notifications via HTTP polling
 */
export function useNotifications(
  options: UseNotificationsOptions = {}
): UseNotificationsReturn {
  const {
    pollInterval = 15000, // Default to 15 seconds
    limit = 50,
    autoPoll = true,
    unreadOnly = false,
  } = options;

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const backoffDelayRef = useRef<number>(pollInterval);
  const isMountedRef = useRef(true);
  const lastFetchRef = useRef<number>(0);

  const fetchNotifications = useCallback(async () => {
    if (!isMountedRef.current) return;

    try {
      const response = await api.getNotifications({
        limit,
        unread_only: unreadOnly,
      });

      if (isMountedRef.current) {
        // Map API response to Notification type with proper type assertions
        const mappedNotifications: Notification[] = response.notifications.map((n) => ({
          id: n.id,
          user_id: n.user_id,
          channel: n.channel,
          priority: n.priority as "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO",
          title: n.title,
          message: n.message,
          severity: n.severity as "critical" | "high" | "medium" | "low" | "info",
          read: n.read,
          read_at: n.read_at,
          metadata: n.metadata,
          timestamp: n.timestamp,
          created_at: n.created_at,
        }));
        
        setNotifications(mappedNotifications);
        setUnreadCount(response.unread_count);
        setError(null);
        // Reset backoff on success
        backoffDelayRef.current = pollInterval;
        lastFetchRef.current = Date.now();
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err instanceof Error ? err : new Error("Failed to fetch notifications"));
        // Exponential backoff on error (max 60 seconds)
        backoffDelayRef.current = Math.min(backoffDelayRef.current * 2, 60000);
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [limit, unreadOnly]);

  const fetchUnreadCount = useCallback(async () => {
    try {
      const response = await api.getUnreadCount();
      if (isMountedRef.current) {
        setUnreadCount(response.unread_count);
      }
    } catch (err) {
      // Silently fail unread count fetch
      console.error("Failed to fetch unread count:", err);
    }
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    await fetchNotifications();
    await fetchUnreadCount();
  }, [fetchNotifications, fetchUnreadCount]);

  const markAsRead = useCallback(async (id: string) => {
    try {
      await api.markNotificationRead(id);
      // Update local state
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true, read_at: new Date().toISOString() } : n))
      );
      // Refresh unread count
      await fetchUnreadCount();
    } catch (err) {
      console.error("Failed to mark notification as read:", err);
      throw err;
    }
  }, [fetchUnreadCount]);

  const markAllAsRead = useCallback(async () => {
    try {
      await api.markAllNotificationsRead();
      // Update local state
      setNotifications((prev) =>
        prev.map((n) => ({ ...n, read: true, read_at: new Date().toISOString() }))
      );
      setUnreadCount(0);
    } catch (err) {
      console.error("Failed to mark all notifications as read:", err);
      throw err;
    }
  }, []);

  // Set up polling
  useEffect(() => {
    isMountedRef.current = true;

    // Initial fetch
    refresh();

    if (autoPoll) {
      const poll = () => {
        if (isMountedRef.current) {
          // Only poll if enough time has passed (avoid rapid polling)
          const timeSinceLastFetch = Date.now() - lastFetchRef.current;
          if (timeSinceLastFetch >= backoffDelayRef.current) {
            fetchNotifications();
            fetchUnreadCount();
          }
        }
      };

      pollIntervalRef.current = setInterval(poll, backoffDelayRef.current);

      // Pause polling when tab is inactive (optional optimization)
      const handleVisibilityChange = () => {
        if (document.hidden) {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
        } else {
          // Resume polling when tab becomes active
          if (!pollIntervalRef.current && autoPoll) {
            refresh();
            pollIntervalRef.current = setInterval(poll, backoffDelayRef.current);
          }
        }
      };

      document.addEventListener("visibilitychange", handleVisibilityChange);

      return () => {
        isMountedRef.current = false;
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
        }
        document.removeEventListener("visibilitychange", handleVisibilityChange);
      };
    }

    return () => {
      isMountedRef.current = false;
    };
  }, [autoPoll, refresh, fetchNotifications, fetchUnreadCount]);

  return {
    notifications,
    unreadCount,
    loading,
    error,
    refresh,
    markAsRead,
    markAllAsRead,
  };
}

