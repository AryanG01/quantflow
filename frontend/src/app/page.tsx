"use client";

import { useCallback } from "react";
import { api } from "@/lib/api";
import { usePolling } from "@/hooks/usePolling";
import { MetricCard } from "@/components/MetricCard";
import { SignalPanel } from "@/components/SignalPanel";
import { PositionsTable } from "@/components/PositionsTable";
import { RiskPanel } from "@/components/RiskPanel";
import { RegimeBadge } from "@/components/RegimeBadge";

function formatCurrency(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(2)}`;
}

function formatPct(n: number): string {
  const sign = n >= 0 ? "+" : "";
  return `${sign}${(n * 100).toFixed(2)}%`;
}

export default function Dashboard() {
  const { data: health } = usePolling(useCallback(() => api.health(), []), 10000);
  const { data: portfolio } = usePolling(useCallback(() => api.portfolio(), []), 5000);
  const { data: signals } = usePolling(useCallback(() => api.signals(), []), 5000);
  const { data: positions } = usePolling(useCallback(() => api.positions(), []), 5000);
  const { data: risk } = usePolling(useCallback(() => api.risk(), []), 5000);
  const { data: regime } = usePolling(useCallback(() => api.regime(), []), 5000);

  const isConnected = health?.status === "ok";

  return (
    <div className="min-h-screen p-4 md:p-6 max-w-[1600px] mx-auto">
      {/* ── Header ─────────────────────────────────── */}
      <header className="flex items-center justify-between mb-6 animate-fade-in">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold tracking-tight">
            <span className="text-[var(--color-accent-cyan)]">AI</span>
            <span className="text-[var(--color-text-muted)]">::</span>
            TRADING
          </h1>
          <div className="h-4 w-px bg-[var(--color-border)]" />
          {regime && <RegimeBadge regime={regime.current} confidence={regime.confidence} />}
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

      {/* ── Portfolio Metrics Row ──────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 mb-4 stagger">
        <MetricCard
          label="Equity"
          value={portfolio ? formatCurrency(portfolio.equity) : "—"}
          pulse
          color="cyan"
        />
        <MetricCard
          label="Cash"
          value={portfolio ? formatCurrency(portfolio.cash) : "—"}
        />
        <MetricCard
          label="Positions"
          value={portfolio ? formatCurrency(portfolio.positions_value) : "—"}
          color="blue"
        />
        <MetricCard
          label="Unrealized PnL"
          value={portfolio ? formatCurrency(portfolio.unrealized_pnl) : "—"}
          color={portfolio && portfolio.unrealized_pnl >= 0 ? "green" : "red"}
        />
        <MetricCard
          label="Realized PnL"
          value={portfolio ? formatCurrency(portfolio.realized_pnl) : "—"}
          color={portfolio && portfolio.realized_pnl >= 0 ? "green" : "red"}
        />
        <MetricCard
          label="Drawdown"
          value={portfolio ? formatPct(-portfolio.drawdown_pct) : "—"}
          color={portfolio && portfolio.drawdown_pct > 0.10 ? "red" : portfolio && portfolio.drawdown_pct > 0.05 ? "amber" : "green"}
        />
      </div>

      {/* ── Main Grid ─────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 stagger">
        {/* Left column: Signals + Positions */}
        <div className="lg:col-span-2 space-y-4">
          <SignalPanel signals={signals || []} />
          <PositionsTable positions={positions || []} />

          {/* System Info */}
          <div className="card-glow bg-[var(--color-bg-card)] rounded-sm p-4">
            <h3 className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] mb-3">
              System
            </h3>
            <div className="grid grid-cols-3 gap-4 text-xs">
              <div>
                <span className="text-[var(--color-text-muted)]">Mode</span>
                <p className="font-semibold text-amber-400">PAPER</p>
              </div>
              <div>
                <span className="text-[var(--color-text-muted)]">Timeframe</span>
                <p className="font-semibold">4H</p>
              </div>
              <div>
                <span className="text-[var(--color-text-muted)]">Uptime</span>
                <p className="font-semibold tabular-nums">
                  {health ? `${Math.floor(health.uptime_seconds / 3600)}h ${Math.floor((health.uptime_seconds % 3600) / 60)}m` : "—"}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Right column: Risk */}
        <div className="space-y-4">
          <RiskPanel risk={risk} />

          {/* Regime Detail */}
          <div className="card-glow bg-[var(--color-bg-card)] rounded-sm p-4">
            <h3 className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] mb-3">
              Regime Detection
            </h3>
            {regime ? (
              <div className="space-y-3">
                <RegimeBadge regime={regime.current} confidence={regime.confidence} />
                <div className="text-[10px] text-[var(--color-text-muted)] space-y-1">
                  <p>States: Trending · Mean-Reverting · Choppy</p>
                  <p>Model: 3-state Gaussian HMM</p>
                  <p>Features: log_returns, realized_vol</p>
                </div>
              </div>
            ) : (
              <p className="text-[var(--color-text-muted)] text-sm">Awaiting regime detection...</p>
            )}
          </div>

          {/* Architecture */}
          <div className="card-glow bg-[var(--color-bg-card)] rounded-sm p-4">
            <h3 className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] mb-3">
              Architecture
            </h3>
            <div className="text-[10px] text-[var(--color-text-muted)] space-y-1 font-mono">
              <p className="text-[var(--color-accent-cyan)]">▸ Regime-Gated MoE</p>
              <p>├─ Technical Features (RSI, ATR, BB, VWAP)</p>
              <p>├─ LightGBM Quantile Regression</p>
              <p>├─ Sentiment (CryptoPanic + Reddit)</p>
              <p>├─ HMM Regime Detection (3-state)</p>
              <p>├─ Vol-Target Position Sizing</p>
              <p>└─ Kill Switch @ -15% DD</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Footer ─────────────────────────────────── */}
      <footer className="mt-8 pt-4 border-t border-[var(--color-border)] text-center">
        <p className="text-[10px] text-[var(--color-text-muted)] tracking-wider">
          AI TRADING SYSTEM · CRYPTO SPOT · MULTI-EXCHANGE · 4H SWING
        </p>
      </footer>
    </div>
  );
}
