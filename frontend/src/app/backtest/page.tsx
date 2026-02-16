"use client";

import { useCallback } from "react";
import { api, BacktestResult } from "@/lib/api";
import { usePolling } from "@/hooks/usePolling";

const metricLabels: Record<string, string> = {
  total_return: "Total Return",
  sharpe_ratio: "Sharpe Ratio",
  max_drawdown: "Max Drawdown",
  total_trades: "Trades",
  hit_rate: "Hit Rate",
};

function fmt(key: string, value: number): string {
  if (key === "total_return" || key === "max_drawdown" || key === "hit_rate")
    return `${(value * 100).toFixed(2)}%`;
  if (key === "total_trades") return String(value);
  return value.toFixed(3);
}

function rankColor(idx: number): string {
  if (idx === 0) return "text-[var(--color-accent-cyan)]";
  if (idx === 1) return "text-[var(--color-text-primary)]";
  return "text-[var(--color-text-secondary)]";
}

export default function BacktestPage() {
  const { data: results } = usePolling(
    useCallback(() => api.backtestResults(), []),
    30000,
  );

  const sorted = [...(results || [])].sort(
    (a, b) => b.sharpe_ratio - a.sharpe_ratio,
  );

  const best = sorted[0] as BacktestResult | undefined;

  return (
    <>
      {/* Hero stat */}
      {best && (
        <div className="card-glow bg-[var(--color-bg-card)] rounded-sm px-6 py-5 mb-4 animate-fade-in">
          <span className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)]">
            Best Strategy (by Sharpe)
          </span>
          <div className="flex items-baseline gap-4 mt-1">
            <span className="text-2xl font-bold text-[var(--color-accent-cyan)]">
              {best.strategy}
            </span>
            <span className="text-lg tabular-nums font-semibold">
              Sharpe {best.sharpe_ratio.toFixed(3)}
            </span>
            <span
              className={`text-sm tabular-nums ${best.total_return >= 0 ? "text-[var(--color-accent-green)]" : "text-[var(--color-accent-red)]"}`}
            >
              {best.total_return >= 0 ? "+" : ""}
              {(best.total_return * 100).toFixed(2)}% return
            </span>
          </div>
        </div>
      )}

      {/* Comparison Table */}
      <div className="card-glow bg-[var(--color-bg-card)] rounded-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-[var(--color-border)]">
          <h2 className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)]">
            Strategy Comparison
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                <th className="text-left px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">
                  #
                </th>
                <th className="text-left px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">
                  Strategy
                </th>
                {Object.keys(metricLabels).map((k) => (
                  <th
                    key={k}
                    className="text-right px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal"
                  >
                    {metricLabels[k]}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((r, i) => (
                <tr
                  key={r.strategy}
                  className="border-b border-[var(--color-border)] hover:bg-[var(--color-bg-card-hover)] transition-colors"
                >
                  <td className={`px-4 py-2.5 font-bold ${rankColor(i)}`}>
                    {i + 1}
                  </td>
                  <td className="px-4 py-2.5 font-semibold">{r.strategy}</td>
                  {Object.keys(metricLabels).map((k) => {
                    const val = r[k as keyof BacktestResult] as number;
                    let color = "";
                    if (k === "total_return")
                      color =
                        val >= 0
                          ? "text-[var(--color-accent-green)]"
                          : "text-[var(--color-accent-red)]";
                    if (k === "max_drawdown")
                      color =
                        val > 0.15
                          ? "text-[var(--color-accent-red)]"
                          : "text-[var(--color-text-secondary)]";
                    return (
                      <td
                        key={k}
                        className={`px-4 py-2.5 text-right tabular-nums ${color}`}
                      >
                        {fmt(k, val)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {sorted.length === 0 && (
          <div className="text-center py-8 text-[var(--color-text-muted)] text-sm">
            No backtest results available
          </div>
        )}
      </div>

      {/* Methodology note */}
      <div className="card-glow bg-[var(--color-bg-card)] rounded-sm p-4 mt-4">
        <h3 className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] mb-2">
          Methodology
        </h3>
        <div className="text-[10px] text-[var(--color-text-muted)] space-y-1 font-mono">
          <p>Walk-forward validation · Purged k-fold (gap=3, embargo=2)</p>
          <p>
            Cost model: spread + linear impact + exchange fees (maker/taker)
          </p>
          <p>Triple-barrier labels: TP=3%, SL=1.5%, max_hold=12 bars</p>
        </div>
      </div>
    </>
  );
}
