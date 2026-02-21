"use client";

import type { RiskMetrics } from "@/lib/api";

export function RiskPanel({
  risk,
  killSwitchThreshold = 0.15,
}: {
  risk: RiskMetrics | null;
  killSwitchThreshold?: number;
}) {
  if (!risk) {
    return (
      <div className="card-glow bg-[var(--color-bg-card)] rounded-lg p-4">
        <h3 className="text-sm font-semibold text-[var(--color-text-secondary)] mb-3">Risk</h3>
        <p className="text-[var(--color-text-muted)] text-sm">No risk data</p>
      </div>
    );
  }

  const ddColor = risk.current_drawdown_pct > 0.10 ? "text-red-400" : risk.current_drawdown_pct > 0.05 ? "text-amber-400" : "text-emerald-400";

  return (
    <div className="card-glow bg-[var(--color-bg-card)] rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-[var(--color-text-secondary)]">Risk Monitor</h3>
        {risk.kill_switch_active && (
          <span className="text-[11px] font-bold uppercase bg-red-500/20 text-red-400 border border-red-500/40 px-2.5 py-0.5 rounded-full animate-pulse">
            KILL SWITCH
          </span>
        )}
      </div>

      <div className="space-y-3">
        {/* Drawdown bar */}
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-[var(--color-text-muted)]">Drawdown</span>
            <span className={`font-semibold tabular-nums font-mono ${ddColor}`}>
              {(risk.current_drawdown_pct * 100).toFixed(1)}%
            </span>
          </div>
          <div className="h-1.5 bg-[var(--color-bg-primary)] rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                risk.current_drawdown_pct > 0.10 ? "bg-red-500" : risk.current_drawdown_pct > 0.05 ? "bg-amber-500" : "bg-emerald-500"
              }`}
              style={{ width: `${Math.min(risk.current_drawdown_pct / killSwitchThreshold * 100, 100)}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-[var(--color-text-muted)] mt-0.5">
            <span>0%</span>
            <span className="text-red-400/60">{(killSwitchThreshold * 100).toFixed(0)}% kill</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 text-xs">
          <div>
            <span className="text-[var(--color-text-muted)]">Max DD</span>
            <p className="font-semibold tabular-nums font-mono">{(risk.max_drawdown_pct * 100).toFixed(1)}%</p>
          </div>
          <div>
            <span className="text-[var(--color-text-muted)]">Vol</span>
            <p className="font-semibold tabular-nums font-mono">{(risk.portfolio_vol * 100).toFixed(1)}%</p>
          </div>
          <div>
            <span className="text-[var(--color-text-muted)]">Sharpe</span>
            <p className="font-semibold tabular-nums font-mono">{risk.sharpe_ratio?.toFixed(2) ?? "—"}</p>
          </div>
          <div>
            <span className="text-[var(--color-text-muted)]">Concentration</span>
            <p className="font-semibold tabular-nums font-mono">{(risk.concentration_pct * 100).toFixed(0)}%</p>
          </div>
        </div>
      </div>
    </div>
  );
}
