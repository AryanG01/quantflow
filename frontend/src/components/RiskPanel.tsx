"use client";

import type { RiskMetrics } from "@/lib/api";

export function RiskPanel({ risk }: { risk: RiskMetrics | null }) {
  if (!risk) {
    return (
      <div className="card-glow bg-[var(--color-bg-card)] rounded-sm p-4">
        <h3 className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] mb-3">Risk</h3>
        <p className="text-[var(--color-text-muted)] text-sm">No risk data</p>
      </div>
    );
  }

  const ddColor = risk.current_drawdown_pct > 0.10 ? "text-red-400" : risk.current_drawdown_pct > 0.05 ? "text-amber-400" : "text-emerald-400";

  return (
    <div className="card-glow bg-[var(--color-bg-card)] rounded-sm p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)]">Risk Monitor</h3>
        {risk.kill_switch_active && (
          <span className="text-[10px] font-bold uppercase bg-red-500/20 text-red-400 border border-red-500/40 px-2 py-0.5 rounded-sm animate-pulse">
            KILL SWITCH
          </span>
        )}
      </div>

      <div className="space-y-3">
        {/* Drawdown bar */}
        <div>
          <div className="flex justify-between text-[10px] mb-1">
            <span className="text-[var(--color-text-muted)]">Drawdown</span>
            <span className={`font-bold tabular-nums ${ddColor}`}>
              {(risk.current_drawdown_pct * 100).toFixed(1)}%
            </span>
          </div>
          <div className="h-1.5 bg-[var(--color-bg-primary)] rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                risk.current_drawdown_pct > 0.10 ? "bg-red-500" : risk.current_drawdown_pct > 0.05 ? "bg-amber-500" : "bg-emerald-500"
              }`}
              style={{ width: `${Math.min(risk.current_drawdown_pct / 0.15 * 100, 100)}%` }}
            />
          </div>
          <div className="flex justify-between text-[9px] text-[var(--color-text-muted)] mt-0.5">
            <span>0%</span>
            <span className="text-red-400/60">15% kill</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-[var(--color-text-muted)]">Max DD</span>
            <p className="font-semibold tabular-nums">{(risk.max_drawdown_pct * 100).toFixed(1)}%</p>
          </div>
          <div>
            <span className="text-[var(--color-text-muted)]">Vol</span>
            <p className="font-semibold tabular-nums">{(risk.portfolio_vol * 100).toFixed(1)}%</p>
          </div>
          <div>
            <span className="text-[var(--color-text-muted)]">Sharpe</span>
            <p className="font-semibold tabular-nums">{risk.sharpe_ratio?.toFixed(2) ?? "—"}</p>
          </div>
          <div>
            <span className="text-[var(--color-text-muted)]">Concentration</span>
            <p className="font-semibold tabular-nums">{(risk.concentration_pct * 100).toFixed(0)}%</p>
          </div>
        </div>
      </div>
    </div>
  );
}
