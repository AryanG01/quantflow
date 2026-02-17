"use client";

import { useCallback, useEffect, useState } from "react";
import { api, Trade } from "@/lib/api";
import { usePolling } from "@/hooks/usePolling";

function formatCurrency(n: number): string {
  if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(2)}`;
}

function formatTime(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const regimeColors: Record<string, string> = {
  trending: "text-[var(--color-regime-trending)]",
  mean_reverting: "text-[var(--color-regime-mean-reverting)]",
  choppy: "text-[var(--color-regime-choppy)]",
};

const SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"];

export default function TradesPage() {
  const { data: trades } = usePolling(useCallback(() => api.trades(), []), 10000);
  const [filter, setFilter] = useState<string>("all");

  // Order entry state
  const [orderSymbol, setOrderSymbol] = useState("BTC/USDT");
  const [orderSide, setOrderSide] = useState<"buy" | "sell">("buy");
  const [orderQty, setOrderQty] = useState("");
  const [orderType, setOrderType] = useState<"market" | "limit">("market");
  const [limitPrice, setLimitPrice] = useState("");
  const [placing, setPlacing] = useState(false);
  const [orderError, setOrderError] = useState<string | null>(null);
  const [orderSuccess, setOrderSuccess] = useState<string | null>(null);
  const [localTrades, setLocalTrades] = useState<Trade[]>([]);
  const [prices, setPrices] = useState<Record<string, number>>({});

  // Poll prices for live display
  useEffect(() => {
    const fetchPrices = async () => {
      const p = await api.prices();
      if (p) setPrices(p);
    };
    fetchPrices();
    const id = setInterval(fetchPrices, 5000);
    return () => clearInterval(id);
  }, []);

  const handlePlaceOrder = async () => {
    const qty = parseFloat(orderQty);
    if (!qty || qty <= 0) {
      setOrderError("Enter a valid quantity");
      return;
    }
    if (orderType === "limit" && (!limitPrice || parseFloat(limitPrice) <= 0)) {
      setOrderError("Enter a valid limit price");
      return;
    }

    setPlacing(true);
    setOrderError(null);
    setOrderSuccess(null);

    const result = await api.placeOrder({
      symbol: orderSymbol,
      side: orderSide,
      quantity: qty,
      order_type: orderType,
      price: orderType === "limit" ? parseFloat(limitPrice) : undefined,
    });

    setPlacing(false);
    if (result) {
      setLocalTrades((prev) => [result, ...prev]);
      setOrderSuccess(`${orderSide.toUpperCase()} ${qty} ${orderSymbol} filled @ ${formatCurrency(result.price)}`);
      setOrderQty("");
      setLimitPrice("");
      setTimeout(() => setOrderSuccess(null), 4000);
    } else {
      setOrderError("Order failed — no price data available for this symbol.");
    }
  };

  const allTrades = [...localTrades, ...(trades || [])];

  const filtered = allTrades.filter((t: Trade) => {
    if (filter === "all") return true;
    if (filter === "winners") return t.pnl > 0;
    if (filter === "losers") return t.pnl < 0;
    return t.symbol === filter;
  });

  const totalPnl = filtered.reduce((sum: number, t: Trade) => sum + t.pnl, 0);
  const winCount = filtered.filter((t: Trade) => t.pnl > 0).length;
  const hitRate = filtered.length > 0 ? (winCount / filtered.length) * 100 : 0;

  return (
    <>
      {/* Order Entry Panel */}
      <div className="card-glow bg-[var(--color-bg-card)] rounded-sm p-4 mb-4 animate-fade-in">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)]">
            Place Order
          </h2>
          <span className="text-[10px] px-2 py-0.5 rounded-sm bg-[var(--color-accent-green)]/15 text-[var(--color-accent-green)] border border-[var(--color-accent-green)]/20">
            Paper Mode
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-6 gap-3 items-end">
          {/* Symbol */}
          <div>
            <label className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] block mb-1.5">Symbol</label>
            <select
              value={orderSymbol}
              onChange={(e) => setOrderSymbol(e.target.value)}
              className="w-full bg-[var(--color-bg-main)] border border-[var(--color-border)] rounded-sm px-3 py-1.5 text-xs text-[var(--color-text-primary)] focus:border-[var(--color-accent-cyan)] outline-none"
            >
              {SYMBOLS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            {prices[orderSymbol] && (
              <span className="text-[10px] text-[var(--color-text-muted)] mt-0.5 block tabular-nums">
                {formatCurrency(prices[orderSymbol])}
              </span>
            )}
          </div>

          {/* Side */}
          <div>
            <label className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] block mb-1.5">Side</label>
            <div className="flex gap-1">
              <button
                onClick={() => setOrderSide("buy")}
                className={`flex-1 px-3 py-1.5 text-[11px] rounded-sm transition-colors ${
                  orderSide === "buy"
                    ? "bg-[var(--color-accent-green)]/20 text-[var(--color-accent-green)] border border-[var(--color-accent-green)]/30"
                    : "border border-[var(--color-border)] text-[var(--color-text-muted)]"
                }`}
              >
                BUY
              </button>
              <button
                onClick={() => setOrderSide("sell")}
                className={`flex-1 px-3 py-1.5 text-[11px] rounded-sm transition-colors ${
                  orderSide === "sell"
                    ? "bg-[var(--color-accent-red)]/20 text-[var(--color-accent-red)] border border-[var(--color-accent-red)]/30"
                    : "border border-[var(--color-border)] text-[var(--color-text-muted)]"
                }`}
              >
                SELL
              </button>
            </div>
          </div>

          {/* Quantity */}
          <div>
            <label className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] block mb-1.5">Quantity</label>
            <input
              type="number"
              value={orderQty}
              onChange={(e) => setOrderQty(e.target.value)}
              placeholder="0.01"
              step="any"
              min="0"
              className="w-full bg-[var(--color-bg-main)] border border-[var(--color-border)] rounded-sm px-3 py-1.5 text-xs text-[var(--color-text-primary)] tabular-nums focus:border-[var(--color-accent-cyan)] outline-none"
            />
          </div>

          {/* Order Type */}
          <div>
            <label className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] block mb-1.5">Type</label>
            <select
              value={orderType}
              onChange={(e) => setOrderType(e.target.value as "market" | "limit")}
              className="w-full bg-[var(--color-bg-main)] border border-[var(--color-border)] rounded-sm px-3 py-1.5 text-xs text-[var(--color-text-primary)] focus:border-[var(--color-accent-cyan)] outline-none"
            >
              <option value="market">Market</option>
              <option value="limit">Limit</option>
            </select>
          </div>

          {/* Limit Price (conditional) */}
          <div>
            <label className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] block mb-1.5">
              {orderType === "limit" ? "Limit Price" : "Est. Price"}
            </label>
            {orderType === "limit" ? (
              <input
                type="number"
                value={limitPrice}
                onChange={(e) => setLimitPrice(e.target.value)}
                placeholder="0.00"
                step="any"
                min="0"
                className="w-full bg-[var(--color-bg-main)] border border-[var(--color-border)] rounded-sm px-3 py-1.5 text-xs text-[var(--color-text-primary)] tabular-nums focus:border-[var(--color-accent-cyan)] outline-none"
              />
            ) : (
              <div className="w-full border border-[var(--color-border)] rounded-sm px-3 py-1.5 text-xs text-[var(--color-text-muted)] tabular-nums bg-[var(--color-bg-main)]/50">
                {prices[orderSymbol] ? formatCurrency(prices[orderSymbol]) : "—"}
              </div>
            )}
          </div>

          {/* Submit */}
          <div>
            <button
              onClick={handlePlaceOrder}
              disabled={placing}
              className={`w-full px-4 py-1.5 text-[11px] rounded-sm transition-colors disabled:opacity-50 ${
                orderSide === "buy"
                  ? "bg-[var(--color-accent-green)]/20 text-[var(--color-accent-green)] border border-[var(--color-accent-green)]/30 hover:bg-[var(--color-accent-green)]/30"
                  : "bg-[var(--color-accent-red)]/20 text-[var(--color-accent-red)] border border-[var(--color-accent-red)]/30 hover:bg-[var(--color-accent-red)]/30"
              }`}
            >
              {placing ? "Placing..." : "Place Order"}
            </button>
          </div>
        </div>

        {/* Feedback */}
        {orderError && (
          <p className="text-[11px] text-[var(--color-accent-red)] mt-2">{orderError}</p>
        )}
        {orderSuccess && (
          <p className="text-[11px] text-[var(--color-accent-green)] mt-2 animate-fade-in">{orderSuccess}</p>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4 stagger">
        <div className="card-glow bg-[var(--color-bg-card)] rounded-sm px-4 py-3">
          <span className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)]">Total Trades</span>
          <div className="text-xl font-bold tabular-nums">{filtered.length}</div>
        </div>
        <div className="card-glow bg-[var(--color-bg-card)] rounded-sm px-4 py-3">
          <span className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)]">Net PnL</span>
          <div className={`text-xl font-bold tabular-nums ${totalPnl >= 0 ? "text-[var(--color-accent-green)]" : "text-[var(--color-accent-red)]"}`}>
            {totalPnl >= 0 ? "+" : ""}{formatCurrency(totalPnl)}
          </div>
        </div>
        <div className="card-glow bg-[var(--color-bg-card)] rounded-sm px-4 py-3">
          <span className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)]">Win Rate</span>
          <div className="text-xl font-bold tabular-nums">{hitRate.toFixed(1)}%</div>
        </div>
        <div className="card-glow bg-[var(--color-bg-card)] rounded-sm px-4 py-3">
          <span className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)]">Avg Fees</span>
          <div className="text-xl font-bold tabular-nums text-[var(--color-text-secondary)]">
            ${filtered.length > 0 ? (filtered.reduce((s: number, t: Trade) => s + t.fees, 0) / filtered.length).toFixed(2) : "0.00"}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {["all", "winners", "losers", "BTC/USDT", "ETH/USDT", "SOL/USDT"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1 text-xs rounded-sm transition-colors ${
              filter === f
                ? "bg-[var(--color-bg-card)] text-[var(--color-accent-cyan)] card-glow"
                : "text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
            }`}
          >
            {f === "all" ? "All" : f === "winners" ? "Winners" : f === "losers" ? "Losers" : f}
          </button>
        ))}
      </div>

      {/* Trade Table */}
      <div className="card-glow bg-[var(--color-bg-card)] rounded-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                <th className="text-left px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">Time</th>
                <th className="text-left px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">ID</th>
                <th className="text-left px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">Symbol</th>
                <th className="text-left px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">Side</th>
                <th className="text-right px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">Qty</th>
                <th className="text-right px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">Price</th>
                <th className="text-right px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">PnL</th>
                <th className="text-right px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">Fees</th>
                <th className="text-center px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">Regime</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((trade: Trade) => (
                <tr key={trade.id} className="border-b border-[var(--color-border)] hover:bg-[var(--color-bg-card-hover)] transition-colors">
                  <td className="px-4 py-2.5 text-[var(--color-text-secondary)] tabular-nums">{formatTime(trade.timestamp)}</td>
                  <td className="px-4 py-2.5 text-[var(--color-text-muted)]">{trade.id}</td>
                  <td className="px-4 py-2.5 font-semibold">{trade.symbol}</td>
                  <td className="px-4 py-2.5">
                    <span className={trade.side === "buy" ? "text-[var(--color-accent-green)]" : "text-[var(--color-accent-red)]"}>
                      {trade.side.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{trade.quantity}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{formatCurrency(trade.price)}</td>
                  <td className={`px-4 py-2.5 text-right tabular-nums font-semibold ${trade.pnl >= 0 ? "text-[var(--color-accent-green)]" : "text-[var(--color-accent-red)]"}`}>
                    {trade.pnl >= 0 ? "+" : ""}{formatCurrency(trade.pnl)}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-[var(--color-text-muted)]">${trade.fees.toFixed(2)}</td>
                  <td className={`px-4 py-2.5 text-center ${regimeColors[trade.regime] || ""}`}>
                    {trade.regime.replace("_", "-")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && (
          <div className="text-center py-8 text-[var(--color-text-muted)] text-sm">No trades found</div>
        )}
      </div>
    </>
  );
}
