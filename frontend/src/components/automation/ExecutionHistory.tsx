"use client";

import { useState, useEffect } from "react";
import { GlassCard, Badge } from "@/components/ui";
import { api } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";

interface ExecutionHistoryProps {
  scheduledSearchId: string;
}

interface HistoryItem {
  job_id: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  findings_count: number;
  error: string | null;
}

export default function ExecutionHistory({ scheduledSearchId }: ExecutionHistoryProps) {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getScheduledSearchHistory(scheduledSearchId, 50);
        setHistory(data);
      } catch (err: any) {
        setError(err.message || "Failed to load execution history");
      } finally {
        setLoading(false);
      }
    };

    loadHistory();
  }, [scheduledSearchId]);

  if (loading) {
    return (
      <GlassCard className="p-4">
        <p className="text-gray-300">Loading execution history...</p>
      </GlassCard>
    );
  }

  if (error) {
    return (
      <GlassCard className="p-4 bg-red-500/20 border-red-500/50">
        <p className="text-red-200">{error}</p>
      </GlassCard>
    );
  }

  if (history.length === 0) {
    return (
      <GlassCard className="p-4">
        <p className="text-gray-300">No execution history yet</p>
      </GlassCard>
    );
  }

  return (
    <div className="space-y-2">
      <h4 className="text-lg font-semibold text-white mb-3">Execution History</h4>
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {history.map((item) => (
          <GlassCard key={item.job_id} className="p-3">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Badge
                    variant={
                      item.status === "completed"
                        ? "success"
                        : item.status === "failed"
                        ? "critical"
                        : "info"
                    }
                  >
                    {item.status}
                  </Badge>
                  <span className="text-sm text-gray-400 font-mono">
                    {item.job_id.slice(0, 8)}...
                  </span>
                </div>
                <div className="text-sm text-gray-300">
                  <div>
                    Started: {formatRelativeTime(new Date(item.created_at))}
                  </div>
                  {item.completed_at && (
                    <div>
                      Completed: {formatRelativeTime(new Date(item.completed_at))}
                    </div>
                  )}
                  <div>Findings: {item.findings_count}</div>
                  {item.error && (
                    <div className="text-red-400 mt-1">Error: {item.error}</div>
                  )}
                </div>
              </div>
            </div>
          </GlassCard>
        ))}
      </div>
    </div>
  );
}

