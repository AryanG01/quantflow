"use client";

import type { LucideIcon } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: string;
  subvalue?: string;
  color?: "green" | "red" | "amber" | "blue" | "cyan" | "default";
  pulse?: boolean;
  icon?: LucideIcon;
}

const colorMap = {
  green: "text-[var(--color-accent-green)] glow-green",
  red: "text-[var(--color-accent-red)] glow-red",
  amber: "text-[var(--color-accent-amber)] glow-amber",
  blue: "text-[var(--color-accent-blue)]",
  cyan: "text-[var(--color-accent-cyan)]",
  default: "text-[var(--color-text-primary)]",
};

export function MetricCard({ label, value, subvalue, color = "default", pulse, icon: Icon }: MetricCardProps) {
  return (
    <div className="card-glow bg-[var(--color-bg-card)] rounded-lg px-4 py-4 transition-all duration-200 hover:bg-[var(--color-bg-card-hover)]">
      <div className="flex items-center gap-2 mb-2">
        {pulse && (
          <span className="pulse-dot inline-block w-1.5 h-1.5 rounded-full bg-[var(--color-accent-green)]" />
        )}
        {Icon && <Icon size={12} className="text-[var(--color-text-muted)]" />}
        <span className="text-xs text-[var(--color-text-muted)]">
          {label}
        </span>
      </div>
      <div className={`text-xl font-semibold tabular-nums font-mono ${colorMap[color]}`}>
        {value}
      </div>
      {subvalue && (
        <div className="text-[11px] text-[var(--color-text-muted)] mt-1">{subvalue}</div>
      )}
    </div>
  );
}
