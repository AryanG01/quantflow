"use client";

import { useCallback } from "react";
import { api } from "@/lib/api";
import { usePolling } from "@/hooks/usePolling";
import { NavBar } from "@/components/NavBar";

export function SharedHeader() {
  const { data: health } = usePolling(useCallback(() => api.health(), []), 10000);
  const isConnected = health?.status === "ok";

  return (
    <header className="flex items-center justify-between mb-6 animate-fade-in">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-bold tracking-tight">
          <span className="text-[var(--color-accent-cyan)]">QUANT</span>
          <span className="text-[var(--color-text-muted)]">::</span>
          FLOW
        </h1>
        <div className="h-4 w-px bg-[var(--color-border)]" />
        <NavBar />
      </div>
      <div className="flex items-center gap-3 text-xs">
        <span className="text-[var(--color-text-muted)]">v{health?.version ?? "—"}</span>
        <div className="flex items-center gap-1.5">
          <span
            className={`w-2 h-2 rounded-full ${isConnected ? "bg-emerald-400 pulse-dot" : "bg-red-400"}`}
          />
          <span className={isConnected ? "text-emerald-400" : "text-red-400"}>
            {isConnected ? "LIVE" : "OFFLINE"}
          </span>
        </div>
      </div>
    </header>
  );
}
