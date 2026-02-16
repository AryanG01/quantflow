"use client";

import type { Position } from "@/lib/api";

function formatCurrency(n: number): string {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2 });
}

function formatPct(n: number): string {
  const sign = n >= 0 ? "+" : "";
  return `${sign}${(n * 100).toFixed(2)}%`;
}

export function PositionsTable({ positions }: { positions: Position[] }) {
  return (
    <div className="card-glow bg-[var(--color-bg-card)] rounded-sm p-4">
      <h3 className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] mb-3">
        Open Positions
      </h3>
      {!positions.length ? (
        <p className="text-[var(--color-text-muted)] text-sm">No open positions</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                <th className="text-left py-2 text-[var(--color-text-muted)] font-medium">Symbol</th>
                <th className="text-left py-2 text-[var(--color-text-muted)] font-medium">Side</th>
                <th className="text-right py-2 text-[var(--color-text-muted)] font-medium">Qty</th>
                <th className="text-right py-2 text-[var(--color-text-muted)] font-medium">Entry</th>
                <th className="text-right py-2 text-[var(--color-text-muted)] font-medium">Current</th>
                <th className="text-right py-2 text-[var(--color-text-muted)] font-medium">PnL</th>
                <th className="text-right py-2 text-[var(--color-text-muted)] font-medium">PnL %</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((pos) => (
                <tr key={pos.symbol} className="border-b border-[var(--color-border)]/50 hover:bg-[var(--color-bg-card-hover)]">
                  <td className="py-2 font-semibold">{pos.symbol}</td>
                  <td className={`py-2 uppercase text-[10px] font-bold ${pos.side === "long" ? "text-emerald-400" : "text-red-400"}`}>
                    {pos.side}
                  </td>
                  <td className="py-2 text-right tabular-nums">{pos.quantity.toFixed(6)}</td>
                  <td className="py-2 text-right tabular-nums">{formatCurrency(pos.entry_price)}</td>
                  <td className="py-2 text-right tabular-nums">{formatCurrency(pos.current_price)}</td>
                  <td className={`py-2 text-right tabular-nums font-semibold ${pos.unrealized_pnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {formatCurrency(pos.unrealized_pnl)}
                  </td>
                  <td className={`py-2 text-right tabular-nums ${pos.unrealized_pnl_pct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {formatPct(pos.unrealized_pnl_pct)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
