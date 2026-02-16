"use client";

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
} from "recharts";
import type { EquityCurvePoint } from "@/lib/api";

interface EquityChartProps {
  data: EquityCurvePoint[];
}

function formatTick(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K`;
  return value.toFixed(0);
}

function formatDate(ts: string): string {
  const d = new Date(ts);
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ value: number; payload: EquityCurvePoint }> }) {
  if (!active || !payload?.length) return null;
  const point = payload[0];
  return (
    <div className="bg-[var(--color-bg-card)] border border-[var(--color-border-accent)] rounded-sm px-3 py-2 text-xs">
      <p className="text-[var(--color-text-muted)] mb-1">
        {new Date(point.payload.timestamp).toLocaleString()}
      </p>
      <p className="text-[var(--color-accent-cyan)] font-bold tabular-nums">
        ${point.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </p>
    </div>
  );
}

export function EquityChart({ data }: EquityChartProps) {
  if (!data.length) {
    return (
      <div className="card-glow bg-[var(--color-bg-card)] rounded-sm p-4">
        <h3 className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] mb-3">
          Equity Curve
        </h3>
        <div className="h-48 flex items-center justify-center text-[var(--color-text-muted)] text-xs">
          Awaiting equity data...
        </div>
      </div>
    );
  }

  const startEquity = data[0].equity;
  const currentEquity = data[data.length - 1].equity;
  const isPositive = currentEquity >= startEquity;

  const strokeColor = isPositive ? "var(--color-accent-green)" : "var(--color-accent-red)";
  const fillId = isPositive ? "equityFillGreen" : "equityFillRed";
  const fillStart = isPositive ? "rgba(16, 185, 129, 0.25)" : "rgba(239, 68, 68, 0.25)";

  return (
    <div className="card-glow bg-[var(--color-bg-card)] rounded-sm p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)]">
          Equity Curve
        </h3>
        <span
          className={`text-xs font-bold tabular-nums ${isPositive ? "text-[var(--color-accent-green)]" : "text-[var(--color-accent-red)]"}`}
        >
          {isPositive ? "+" : ""}
          {(((currentEquity - startEquity) / startEquity) * 100).toFixed(2)}%
        </span>
      </div>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id={fillId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={fillStart} />
                <stop offset="100%" stopColor="transparent" />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatDate}
              tick={{ fontSize: 9, fill: "#64748b" }}
              axisLine={{ stroke: "#1e293b" }}
              tickLine={false}
              minTickGap={40}
            />
            <YAxis
              tickFormatter={formatTick}
              tick={{ fontSize: 9, fill: "#64748b" }}
              axisLine={false}
              tickLine={false}
              width={48}
              domain={["auto", "auto"]}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine
              y={startEquity}
              stroke="#334155"
              strokeDasharray="3 3"
            />
            <Area
              type="monotone"
              dataKey="equity"
              stroke={strokeColor}
              strokeWidth={1.5}
              fill={`url(#${fillId})`}
              animationDuration={800}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
