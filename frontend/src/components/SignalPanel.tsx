"use client";

import type { Signal } from "@/lib/api";

const directionStyle = {
  long: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/30", label: "LONG" },
  short: { bg: "bg-red-500/10", text: "text-red-400", border: "border-red-500/30", label: "SHORT" },
  flat: { bg: "bg-slate-500/10", text: "text-slate-400", border: "border-slate-500/30", label: "FLAT" },
};

const regimeColors: Record<string, string> = {
  trending: "text-[var(--color-regime-trending)]",
  mean_reverting: "text-[var(--color-regime-mean-reverting)]",
  choppy: "text-[var(--color-regime-choppy)]",
};

export function SignalPanel({ signals }: { signals: Signal[] }) {
  if (!signals.length) {
    return (
      <div className="card-glow bg-[var(--color-bg-card)] rounded-lg p-4">
        <h3 className="text-sm font-semibold text-[var(--color-text-secondary)] mb-3">Signals</h3>
        <p className="text-[var(--color-text-muted)] text-sm">Waiting for signal generation...</p>
      </div>
    );
  }

  return (
    <div className="card-glow bg-[var(--color-bg-card)] rounded-lg p-4">
      <h3 className="text-sm font-semibold text-[var(--color-text-secondary)] mb-3">
        Active Signals
      </h3>
      <div className="space-y-2">
        {signals.map((sig) => {
          const style = directionStyle[sig.direction] || directionStyle.flat;
          return (
            <div
              key={`${sig.symbol}-${sig.timestamp}`}
              className={`${style.bg} border ${style.border} rounded-lg px-4 py-2.5 flex items-center justify-between`}
            >
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold text-[var(--color-text-primary)]">
                  {sig.symbol}
                </span>
                <span className={`text-[11px] font-bold uppercase tracking-wider ${style.text}`}>
                  {style.label}
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs">
                <span className="text-[var(--color-text-secondary)]">
                  str <span className="font-semibold text-[var(--color-text-primary)] tabular-nums font-mono">{(sig.strength * 100).toFixed(0)}%</span>
                </span>
                <span className="text-[var(--color-text-secondary)]">
                  conf <span className="font-semibold text-[var(--color-text-primary)] tabular-nums font-mono">{(sig.confidence * 100).toFixed(0)}%</span>
                </span>
                <span className={`${regimeColors[sig.regime] || "text-slate-400"} text-[11px] uppercase`}>
                  {sig.regime.replace("_", " ")}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
