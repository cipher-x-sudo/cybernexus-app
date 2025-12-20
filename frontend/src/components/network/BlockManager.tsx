"use client";

import React, { useState, useEffect } from "react";
import { GlassCard, GlassButton } from "@/components/ui";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";

interface BlockManagerProps {
  className?: string;
}

export function BlockManager({ className }: BlockManagerProps) {
  const [blocks, setBlocks] = useState<any>({ ips: [], endpoints: [], patterns: [] });
  const [loading, setLoading] = useState(true);
  const [showAddBlock, setShowAddBlock] = useState(false);
  const [blockType, setBlockType] = useState<"ip" | "endpoint" | "pattern">("ip");
  const [blockValue, setBlockValue] = useState("");
  const [blockReason, setBlockReason] = useState("");

  useEffect(() => {
    fetchBlocks();
  }, []);

  const fetchBlocks = async () => {
    try {
      const data = await api.getAllBlocks();
      setBlocks(data);
    } catch (error) {
      console.error("Error fetching blocks:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleBlock = async () => {
    try {
      if (blockType === "ip") {
        await api.blockIP(blockValue, blockReason);
      } else if (blockType === "endpoint") {
        await api.blockEndpoint(blockValue, "ALL", blockReason);
      } else {
        await api.blockPattern("user_agent", blockValue, blockReason);
      }
      setBlockValue("");
      setBlockReason("");
      setShowAddBlock(false);
      fetchBlocks();
    } catch (error) {
      console.error("Error blocking:", error);
    }
  };

  const handleUnblock = async (type: string, value: string) => {
    try {
      if (type === "ip") {
        await api.unblockIP(value);
      } else if (type === "endpoint") {
        await api.unblockEndpoint(value);
      }
      fetchBlocks();
    } catch (error) {
      console.error("Error unblocking:", error);
    }
  };

  if (loading) {
    return (
      <GlassCard className={cn("", className)} hover={false}>
        <div className="text-white/40 font-mono text-sm">Loading blocks...</div>
      </GlassCard>
    );
  }

  return (
    <GlassCard className={cn("", className)} hover={false}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-mono text-lg font-semibold text-white">Block Management</h2>
        <GlassButton size="sm" onClick={() => setShowAddBlock(!showAddBlock)}>
          {showAddBlock ? "Cancel" : "Add Block"}
        </GlassButton>
      </div>

      {showAddBlock && (
        <div className="mb-4 p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
          <div className="space-y-3">
            <div>
              <label className="block text-xs text-white/50 mb-1">Block Type</label>
              <select
                value={blockType}
                onChange={(e) => setBlockType(e.target.value as any)}
                className="w-full h-9 px-3 bg-white/[0.05] border border-white/[0.1] rounded-lg text-sm text-white/80 font-mono"
              >
                <option value="ip">IP Address</option>
                <option value="endpoint">Endpoint Pattern</option>
                <option value="pattern">Pattern</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1">Value</label>
              <input
                type="text"
                value={blockValue}
                onChange={(e) => setBlockValue(e.target.value)}
                placeholder={blockType === "ip" ? "192.168.1.1" : "/api/v1/admin/*"}
                className="w-full h-9 px-3 bg-white/[0.05] border border-white/[0.1] rounded-lg text-sm text-white/80 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1">Reason</label>
              <input
                type="text"
                value={blockReason}
                onChange={(e) => setBlockReason(e.target.value)}
                placeholder="Reason for blocking"
                className="w-full h-9 px-3 bg-white/[0.05] border border-white/[0.1] rounded-lg text-sm text-white/80 font-mono"
              />
            </div>
            <GlassButton size="sm" onClick={handleBlock}>
              Block
            </GlassButton>
          </div>
        </div>
      )}

      <div className="space-y-4">
        <div>
          <div className="text-xs text-white/50 mb-2">Blocked IPs ({blocks.ips?.length || 0})</div>
          <div className="space-y-1">
            {blocks.ips?.slice(0, 5).map((block: any) => (
              <div
                key={block.ip}
                className="flex items-center justify-between p-2 rounded bg-white/[0.02] border border-white/[0.05]"
              >
                <div>
                  <div className="text-sm font-mono text-white/80">{block.ip}</div>
                  {block.reason && (
                    <div className="text-xs text-white/50">{block.reason}</div>
                  )}
                </div>
                <GlassButton
                  variant="danger"
                  size="sm"
                  onClick={() => handleUnblock("ip", block.ip)}
                >
                  Unblock
                </GlassButton>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div className="text-xs text-white/50 mb-2">
            Blocked Endpoints ({blocks.endpoints?.length || 0})
          </div>
          <div className="space-y-1">
            {blocks.endpoints?.slice(0, 5).map((block: any) => (
              <div
                key={block.pattern}
                className="flex items-center justify-between p-2 rounded bg-white/[0.02] border border-white/[0.05]"
              >
                <div>
                  <div className="text-sm font-mono text-white/80">
                    {block.method} {block.pattern}
                  </div>
                  {block.reason && (
                    <div className="text-xs text-white/50">{block.reason}</div>
                  )}
                </div>
                <GlassButton
                  variant="danger"
                  size="sm"
                  onClick={() => handleUnblock("endpoint", block.pattern)}
                >
                  Unblock
                </GlassButton>
              </div>
            ))}
          </div>
        </div>
      </div>
    </GlassCard>
  );
}


