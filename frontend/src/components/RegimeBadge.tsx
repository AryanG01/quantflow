"use client";

import { TrendingUp, ArrowLeftRight, Zap } from "lucide-react";
import type { LucideIcon } from "lucide-react";

const regimeConfig: Record<string, { color: string; bg: string; border: string; icon: LucideIcon }> = {
  trending: {
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
    icon: TrendingUp,
  },
  mean_reverting: {
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/30",
    icon: ArrowLeftRight,
  },
  choppy: {
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    icon: Zap,
  },
};

export function RegimeBadge({ regime, confidence }: { regime: string; confidence?: number }) {
  const config = regimeConfig[regime] || regimeConfig.choppy;
  const Icon = config.icon;

  return (
    <div className={`inline-flex items-center gap-2 ${config.bg} border ${config.border} rounded-full px-3 py-1.5`}>
      <Icon size={14} className={config.color} />
      <div>
        <span className={`text-xs font-semibold uppercase tracking-wider ${config.color}`}>
          {regime.replace("_", " ")}
        </span>
        {confidence !== undefined && (
          <span className="text-[11px] text-[var(--color-text-muted)] ml-2 tabular-nums font-mono">
            {(confidence * 100).toFixed(0)}%
          </span>
        )}
      </div>
    </div>
  );
}
