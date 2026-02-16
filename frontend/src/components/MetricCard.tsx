"use client";

interface MetricCardProps {
  label: string;
  value: string;
  subvalue?: string;
  color?: "green" | "red" | "amber" | "blue" | "cyan" | "default";
  pulse?: boolean;
}

const colorMap = {
  green: "text-[var(--color-accent-green)] glow-green",
  red: "text-[var(--color-accent-red)] glow-red",
  amber: "text-[var(--color-accent-amber)] glow-amber",
  blue: "text-[var(--color-accent-blue)]",
  cyan: "text-[var(--color-accent-cyan)]",
  default: "text-[var(--color-text-primary)]",
};

export function MetricCard({ label, value, subvalue, color = "default", pulse }: MetricCardProps) {
  return (
    <div className="card-glow bg-[var(--color-bg-card)] rounded-sm px-4 py-3 transition-all duration-200 hover:bg-[var(--color-bg-card-hover)]">
      <div className="flex items-center gap-2 mb-1">
        {pulse && (
          <span className="pulse-dot inline-block w-1.5 h-1.5 rounded-full bg-[var(--color-accent-green)]" />
        )}
        <span className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)]">
          {label}
        </span>
      </div>
      <div className={`text-xl font-bold tabular-nums ${colorMap[color]}`}>
        {value}
      </div>
      {subvalue && (
        <div className="text-[11px] text-[var(--color-text-muted)] mt-0.5">{subvalue}</div>
      )}
    </div>
  );
}
