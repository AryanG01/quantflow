"use client";

import { useCallback, useState } from "react";
import { api, Trade } from "@/lib/api";
import { usePolling } from "@/hooks/usePolling";

function formatCurrency(n: number): string {
  if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(2)}`;
}

function formatTime(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const regimeColors: Record<string, string> = {
  trending: "text-[var(--color-regime-trending)]",
  mean_reverting: "text-[var(--color-regime-mean-reverting)]",
  choppy: "text-[var(--color-regime-choppy)]",
};

export default function TradesPage() {
  const { data: trades } = usePolling(useCallback(() => api.trades(), []), 10000);
  const [filter, setFilter] = useState<string>("all");

  const filtered = (trades || []).filter((t: Trade) => {
    if (filter === "all") return true;
    if (filter === "winners") return t.pnl > 0;
    if (filter === "losers") return t.pnl < 0;
    return t.symbol === filter;
  });

  const totalPnl = filtered.reduce((sum: number, t: Trade) => sum + t.pnl, 0);
  const winCount = filtered.filter((t: Trade) => t.pnl > 0).length;
  const hitRate = filtered.length > 0 ? (winCount / filtered.length) * 100 : 0;

  return (
    <>
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4 stagger">
        <div className="card-glow bg-[var(--color-bg-card)] rounded-sm px-4 py-3">
          <span className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)]">Total Trades</span>
          <div className="text-xl font-bold tabular-nums">{filtered.length}</div>
        </div>
        <div className="card-glow bg-[var(--color-bg-card)] rounded-sm px-4 py-3">
          <span className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)]">Net PnL</span>
          <div className={`text-xl font-bold tabular-nums ${totalPnl >= 0 ? "text-[var(--color-accent-green)]" : "text-[var(--color-accent-red)]"}`}>
            {totalPnl >= 0 ? "+" : ""}{formatCurrency(totalPnl)}
          </div>
        </div>
        <div className="card-glow bg-[var(--color-bg-card)] rounded-sm px-4 py-3">
          <span className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)]">Win Rate</span>
          <div className="text-xl font-bold tabular-nums">{hitRate.toFixed(1)}%</div>
        </div>
        <div className="card-glow bg-[var(--color-bg-card)] rounded-sm px-4 py-3">
          <span className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)]">Avg Fees</span>
          <div className="text-xl font-bold tabular-nums text-[var(--color-text-secondary)]">
            ${filtered.length > 0 ? (filtered.reduce((s: number, t: Trade) => s + t.fees, 0) / filtered.length).toFixed(2) : "0.00"}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {["all", "winners", "losers", "BTC/USDT", "ETH/USDT", "SOL/USDT"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1 text-xs rounded-sm transition-colors ${
              filter === f
                ? "bg-[var(--color-bg-card)] text-[var(--color-accent-cyan)] card-glow"
                : "text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
            }`}
          >
            {f === "all" ? "All" : f === "winners" ? "Winners" : f === "losers" ? "Losers" : f}
          </button>
        ))}
      </div>

      {/* Trade Table */}
      <div className="card-glow bg-[var(--color-bg-card)] rounded-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                <th className="text-left px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">Time</th>
                <th className="text-left px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">ID</th>
                <th className="text-left px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">Symbol</th>
                <th className="text-left px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">Side</th>
                <th className="text-right px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">Qty</th>
                <th className="text-right px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">Price</th>
                <th className="text-right px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">PnL</th>
                <th className="text-right px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">Fees</th>
                <th className="text-center px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">Regime</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((trade: Trade) => (
                <tr key={trade.id} className="border-b border-[var(--color-border)] hover:bg-[var(--color-bg-card-hover)] transition-colors">
                  <td className="px-4 py-2.5 text-[var(--color-text-secondary)] tabular-nums">{formatTime(trade.timestamp)}</td>
                  <td className="px-4 py-2.5 text-[var(--color-text-muted)]">{trade.id}</td>
                  <td className="px-4 py-2.5 font-semibold">{trade.symbol}</td>
                  <td className="px-4 py-2.5">
                    <span className={trade.side === "buy" ? "text-[var(--color-accent-green)]" : "text-[var(--color-accent-red)]"}>
                      {trade.side.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{trade.quantity}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{formatCurrency(trade.price)}</td>
                  <td className={`px-4 py-2.5 text-right tabular-nums font-semibold ${trade.pnl >= 0 ? "text-[var(--color-accent-green)]" : "text-[var(--color-accent-red)]"}`}>
                    {trade.pnl >= 0 ? "+" : ""}{formatCurrency(trade.pnl)}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-[var(--color-text-muted)]">${trade.fees.toFixed(2)}</td>
                  <td className={`px-4 py-2.5 text-center ${regimeColors[trade.regime] || ""}`}>
                    {trade.regime.replace("_", "-")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && (
          <div className="text-center py-8 text-[var(--color-text-muted)] text-sm">No trades found</div>
        )}
      </div>
    </>
  );
}
