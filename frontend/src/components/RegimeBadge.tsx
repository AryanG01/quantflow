"use client";

const regimeConfig: Record<string, { color: string; bg: string; border: string; icon: string }> = {
  trending: {
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
    icon: "↗",
  },
  mean_reverting: {
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/30",
    icon: "↔",
  },
  choppy: {
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    icon: "⚡",
  },
};

export function RegimeBadge({ regime, confidence }: { regime: string; confidence?: number }) {
  const config = regimeConfig[regime] || regimeConfig.choppy;

  return (
    <div className={`inline-flex items-center gap-2 ${config.bg} border ${config.border} rounded-sm px-3 py-1.5`}>
      <span className="text-base">{config.icon}</span>
      <div>
        <span className={`text-xs font-bold uppercase tracking-wider ${config.color}`}>
          {regime.replace("_", " ")}
        </span>
        {confidence !== undefined && (
          <span className="text-[10px] text-[var(--color-text-muted)] ml-2">
            {(confidence * 100).toFixed(0)}%
          </span>
        )}
      </div>
    </div>
  );
}
