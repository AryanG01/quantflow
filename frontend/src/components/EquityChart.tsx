"use client";

import { useState } from "react";
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
    <div className="bg-[var(--color-bg-card)] border border-[var(--color-border-accent)] rounded-md px-3 py-2 text-xs shadow-lg">
      <p className="text-[var(--color-text-muted)] mb-1">
        {new Date(point.payload.timestamp).toLocaleString()}
      </p>
      <p className="text-[var(--color-accent-cyan)] font-bold tabular-nums font-mono">
        ${point.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </p>
    </div>
  );
}

const TIME_RANGES = [
  { label: "1W", days: 7 },
  { label: "1M", days: 30 },
  { label: "3M", days: 90 },
  { label: "All", days: 0 },
];

export function EquityChart({ data }: EquityChartProps) {
  const [rangeDays, setRangeDays] = useState(0);

  if (!data.length) {
    return (
      <div className="card-glow bg-[var(--color-bg-card)] rounded-lg p-4">
        <h3 className="text-sm font-semibold text-[var(--color-text-secondary)] mb-3">
          Equity Curve
        </h3>
        <div className="h-64 flex items-center justify-center text-[var(--color-text-muted)] text-sm">
          Awaiting equity data...
        </div>
      </div>
    );
  }

  const filteredData = rangeDays > 0
    ? data.filter((p) => new Date(p.timestamp) >= new Date(Date.now() - rangeDays * 86400000))
    : data;

  const displayData = filteredData.length > 0 ? filteredData : data;
  const startEquity = displayData[0].equity;
  const currentEquity = displayData[displayData.length - 1].equity;
  const isPositive = currentEquity >= startEquity;

  const strokeColor = isPositive ? "var(--color-accent-green)" : "var(--color-accent-red)";
  const fillId = isPositive ? "equityFillGreen" : "equityFillRed";
  const fillStart = isPositive ? "rgba(16, 185, 129, 0.25)" : "rgba(239, 68, 68, 0.25)";

  return (
    <div className="card-glow bg-[var(--color-bg-card)] rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-[var(--color-text-secondary)]">
          Equity Curve
        </h3>
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            {TIME_RANGES.map((r) => (
              <button
                key={r.label}
                onClick={() => setRangeDays(r.days)}
                className={`px-2 py-0.5 text-[11px] rounded-md transition-colors ${
                  rangeDays === r.days
                    ? "bg-[var(--color-accent-cyan)]/15 text-[var(--color-accent-cyan)]"
                    : "text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>
          <span
            className={`text-xs font-semibold tabular-nums font-mono ${isPositive ? "text-[var(--color-accent-green)]" : "text-[var(--color-accent-red)]"}`}
          >
            {isPositive ? "+" : ""}
            {(((currentEquity - startEquity) / startEquity) * 100).toFixed(2)}%
          </span>
        </div>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={displayData} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id={fillId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={fillStart} />
                <stop offset="100%" stopColor="transparent" />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatDate}
              tick={{ fontSize: 10, fill: "#64748b", fontFamily: "Inter" }}
              axisLine={{ stroke: "#1e293b" }}
              tickLine={false}
              minTickGap={40}
            />
            <YAxis
              tickFormatter={formatTick}
              tick={{ fontSize: 10, fill: "#64748b", fontFamily: "Inter" }}
              axisLine={false}
              tickLine={false}
              width={52}
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
