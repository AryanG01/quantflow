"use client";

import { useCallback } from "react";
import { api } from "@/lib/api";
import { usePolling } from "@/hooks/usePolling";
import { MetricCard } from "@/components/MetricCard";
import { SignalPanel } from "@/components/SignalPanel";
import { PositionsTable } from "@/components/PositionsTable";
import { RiskPanel } from "@/components/RiskPanel";
import { RegimeBadge } from "@/components/RegimeBadge";
import { EquityChart } from "@/components/EquityChart";
import { DollarSign, Wallet, PieChart, TrendingUp, TrendingDown, ShieldAlert } from "lucide-react";

function formatCurrency(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(2)}`;
}

function formatPct(n: number): string {
  const sign = n >= 0 ? "+" : "";
  return `${sign}${(n * 100).toFixed(2)}%`;
}

function MetricSkeleton() {
  return <div className="skeleton h-[88px] rounded-lg" />;
}

export default function Dashboard() {
  const { data: health } = usePolling(useCallback(() => api.health(), []), 10000);
  const { data: portfolio } = usePolling(useCallback(() => api.portfolio(), []), 5000);
  const { data: signals } = usePolling(useCallback(() => api.signals(), []), 5000);
  const { data: positions } = usePolling(useCallback(() => api.positions(), []), 5000);
  const { data: risk } = usePolling(useCallback(() => api.risk(), []), 5000);
  const { data: regime } = usePolling(useCallback(() => api.regime(), []), 5000);
  const { data: equityHistory } = usePolling(useCallback(() => api.equityHistory(), []), 15000);

  const loading = !portfolio;

  return (
    <>
      {/* Portfolio Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-4 stagger">
        {loading ? (
          <>
            <MetricSkeleton />
            <MetricSkeleton />
            <MetricSkeleton />
            <MetricSkeleton />
            <MetricSkeleton />
            <MetricSkeleton />
          </>
        ) : (
          <>
            <MetricCard
              label="Equity"
              value={formatCurrency(portfolio.equity)}
              pulse
              color="cyan"
              icon={DollarSign}
            />
            <MetricCard
              label="Cash"
              value={formatCurrency(portfolio.cash)}
              icon={Wallet}
            />
            <MetricCard
              label="Positions"
              value={formatCurrency(portfolio.positions_value)}
              color="blue"
              icon={PieChart}
            />
            <MetricCard
              label="Unrealized PnL"
              value={formatCurrency(portfolio.unrealized_pnl)}
              color={portfolio.unrealized_pnl >= 0 ? "green" : "red"}
              icon={TrendingUp}
            />
            <MetricCard
              label="Realized PnL"
              value={formatCurrency(portfolio.realized_pnl)}
              color={portfolio.realized_pnl >= 0 ? "green" : "red"}
              icon={TrendingDown}
            />
            <MetricCard
              label="Drawdown"
              value={formatPct(-portfolio.drawdown_pct)}
              color={portfolio.drawdown_pct > 0.10 ? "red" : portfolio.drawdown_pct > 0.05 ? "amber" : "green"}
              icon={ShieldAlert}
            />
          </>
        )}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 stagger">
        {/* Left column: Signals + Equity + Positions */}
        <div className="lg:col-span-2 space-y-4">
          <SignalPanel signals={signals || []} />
          <EquityChart data={equityHistory || []} />
          <PositionsTable positions={positions || []} />

          {/* System Info */}
          <div className="card-glow bg-[var(--color-bg-card)] rounded-lg p-4">
            <h3 className="text-sm font-semibold text-[var(--color-text-secondary)] mb-3">
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
                <p className="font-semibold tabular-nums font-mono">
                  {health ? `${Math.floor(health.uptime_seconds / 3600)}h ${Math.floor((health.uptime_seconds % 3600) / 60)}m` : "—"}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Right column: Risk + Regime */}
        <div className="space-y-4">
          <RiskPanel risk={risk} />

          {/* Regime Detail */}
          <div className="card-glow bg-[var(--color-bg-card)] rounded-lg p-4">
            <h3 className="text-sm font-semibold text-[var(--color-text-secondary)] mb-3">
              Regime Detection
            </h3>
            {regime ? (
              <div className="space-y-3">
                <RegimeBadge regime={regime.current} confidence={regime.confidence} />
                <div className="text-xs text-[var(--color-text-muted)] space-y-1">
                  <p>States: Trending / Mean-Reverting / Choppy</p>
                  <p>Model: 3-state Gaussian HMM</p>
                  <p>Features: log_returns, realized_vol</p>
                </div>
              </div>
            ) : (
              <p className="text-[var(--color-text-muted)] text-sm">Awaiting regime detection...</p>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-8 pt-4 border-t border-[var(--color-border)] text-center">
        <p className="text-xs text-[var(--color-text-muted)] tracking-wider">
          QUANTFLOW · CRYPTO SPOT · MULTI-EXCHANGE · 4H SWING
        </p>
      </footer>
    </>
  );
}
