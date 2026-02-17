"use client";

import { useCallback, useState } from "react";
import { api, BacktestResult } from "@/lib/api";
import { usePolling } from "@/hooks/usePolling";

const metricLabels: Record<string, string> = {
  total_return: "Total Return",
  sharpe_ratio: "Sharpe Ratio",
  max_drawdown: "Max Drawdown",
  total_trades: "Trades",
  hit_rate: "Hit Rate",
};

function fmt(key: string, value: number): string {
  if (key === "total_return" || key === "max_drawdown" || key === "hit_rate")
    return `${(value * 100).toFixed(2)}%`;
  if (key === "total_trades") return String(value);
  return value.toFixed(3);
}

function rankColor(idx: number): string {
  if (idx === 0) return "text-[var(--color-accent-cyan)]";
  if (idx === 1) return "text-[var(--color-text-primary)]";
  return "text-[var(--color-text-secondary)]";
}

const STRATEGIES = [
  { value: "buy_and_hold", label: "Buy & Hold" },
  { value: "ma_crossover", label: "MA Crossover (20/50)" },
  { value: "mean_reversion", label: "Mean Reversion (z-score)" },
];

const LOOKBACK_OPTIONS = [
  { value: 90, label: "90 days" },
  { value: 180, label: "180 days" },
  { value: 365, label: "1 year" },
  { value: 730, label: "2 years" },
];

const SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"];

export default function BacktestPage() {
  const { data: demoResults } = usePolling(
    useCallback(() => api.backtestResults(), []),
    30000,
  );

  // Run form state
  const [symbol, setSymbol] = useState("BTC/USDT");
  const [strategy, setStrategy] = useState("buy_and_hold");
  const [lookbackDays, setLookbackDays] = useState(365);
  const [initialCapital, setInitialCapital] = useState(100000);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [liveResults, setLiveResults] = useState<BacktestResult[]>([]);

  const handleRun = async () => {
    setRunning(true);
    setError(null);
    const result = await api.runBacktest({
      symbol,
      strategy,
      lookback_days: lookbackDays,
      initial_capital: initialCapital,
    });
    setRunning(false);
    if (result) {
      setLiveResults((prev) => [result, ...prev]);
    } else {
      setError("Backtest failed — check that candle data is loaded for this symbol.");
    }
  };

  // Combine live results with demo results for display
  const allResults = [...liveResults, ...(demoResults || [])];
  const sorted = [...allResults].sort((a, b) => b.sharpe_ratio - a.sharpe_ratio);
  const best = sorted[0] as BacktestResult | undefined;

  return (
    <>
      {/* Run Backtest Form */}
      <div className="card-glow bg-[var(--color-bg-card)] rounded-sm p-4 mb-4 animate-fade-in">
        <h2 className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] mb-3">
          Run Backtest
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 items-end">
          <div>
            <label className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] block mb-1.5">Symbol</label>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="w-full bg-[var(--color-bg-main)] border border-[var(--color-border)] rounded-sm px-3 py-1.5 text-xs text-[var(--color-text-primary)] focus:border-[var(--color-accent-cyan)] outline-none"
            >
              {SYMBOLS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] block mb-1.5">Strategy</label>
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
              className="w-full bg-[var(--color-bg-main)] border border-[var(--color-border)] rounded-sm px-3 py-1.5 text-xs text-[var(--color-text-primary)] focus:border-[var(--color-accent-cyan)] outline-none"
            >
              {STRATEGIES.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] block mb-1.5">Lookback</label>
            <select
              value={lookbackDays}
              onChange={(e) => setLookbackDays(Number(e.target.value))}
              className="w-full bg-[var(--color-bg-main)] border border-[var(--color-border)] rounded-sm px-3 py-1.5 text-xs text-[var(--color-text-primary)] focus:border-[var(--color-accent-cyan)] outline-none"
            >
              {LOOKBACK_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] block mb-1.5">Capital</label>
            <input
              type="number"
              value={initialCapital}
              onChange={(e) => setInitialCapital(Number(e.target.value))}
              min={1000}
              max={10000000}
              className="w-full bg-[var(--color-bg-main)] border border-[var(--color-border)] rounded-sm px-3 py-1.5 text-xs text-[var(--color-text-primary)] tabular-nums focus:border-[var(--color-accent-cyan)] outline-none"
            />
          </div>
          <div>
            <button
              onClick={handleRun}
              disabled={running}
              className="w-full px-4 py-1.5 text-[11px] rounded-sm bg-[var(--color-accent-cyan)]/20 text-[var(--color-accent-cyan)] border border-[var(--color-accent-cyan)]/30 hover:bg-[var(--color-accent-cyan)]/30 transition-colors disabled:opacity-50"
            >
              {running ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="inline-block w-3 h-3 border border-[var(--color-accent-cyan)] border-t-transparent rounded-full animate-spin" />
                  Running...
                </span>
              ) : (
                "Run Backtest"
              )}
            </button>
          </div>
        </div>
        {error && (
          <p className="text-[11px] text-[var(--color-accent-red)] mt-2">{error}</p>
        )}
      </div>

      {/* Hero stat */}
      {best && (
        <div className="card-glow bg-[var(--color-bg-card)] rounded-sm px-6 py-5 mb-4 animate-fade-in">
          <span className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)]">
            Best Strategy (by Sharpe)
          </span>
          <div className="flex items-baseline gap-4 mt-1">
            <span className="text-2xl font-bold text-[var(--color-accent-cyan)]">
              {best.strategy}
            </span>
            <span className="text-lg tabular-nums font-semibold">
              Sharpe {best.sharpe_ratio.toFixed(3)}
            </span>
            <span
              className={`text-sm tabular-nums ${best.total_return >= 0 ? "text-[var(--color-accent-green)]" : "text-[var(--color-accent-red)]"}`}
            >
              {best.total_return >= 0 ? "+" : ""}
              {(best.total_return * 100).toFixed(2)}% return
            </span>
          </div>
        </div>
      )}

      {/* Comparison Table */}
      <div className="card-glow bg-[var(--color-bg-card)] rounded-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-[var(--color-border)] flex items-center justify-between">
          <h2 className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)]">
            Strategy Comparison
          </h2>
          {liveResults.length > 0 && (
            <span className="text-[10px] text-[var(--color-accent-cyan)]">
              {liveResults.length} live run{liveResults.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                <th className="text-left px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">
                  #
                </th>
                <th className="text-left px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal">
                  Strategy
                </th>
                {Object.keys(metricLabels).map((k) => (
                  <th
                    key={k}
                    className="text-right px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] font-normal"
                  >
                    {metricLabels[k]}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((r, i) => (
                <tr
                  key={`${r.strategy}-${i}`}
                  className="border-b border-[var(--color-border)] hover:bg-[var(--color-bg-card-hover)] transition-colors"
                >
                  <td className={`px-4 py-2.5 font-bold ${rankColor(i)}`}>
                    {i + 1}
                  </td>
                  <td className="px-4 py-2.5 font-semibold">{r.strategy}</td>
                  {Object.keys(metricLabels).map((k) => {
                    const val = r[k as keyof BacktestResult] as number;
                    let color = "";
                    if (k === "total_return")
                      color =
                        val >= 0
                          ? "text-[var(--color-accent-green)]"
                          : "text-[var(--color-accent-red)]";
                    if (k === "max_drawdown")
                      color =
                        val > 0.15
                          ? "text-[var(--color-accent-red)]"
                          : "text-[var(--color-text-secondary)]";
                    return (
                      <td
                        key={k}
                        className={`px-4 py-2.5 text-right tabular-nums ${color}`}
                      >
                        {fmt(k, val)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {sorted.length === 0 && (
          <div className="text-center py-8 text-[var(--color-text-muted)] text-sm">
            No backtest results available — run one above
          </div>
        )}
      </div>

      {/* Methodology note */}
      <div className="card-glow bg-[var(--color-bg-card)] rounded-sm p-4 mt-4">
        <h3 className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] mb-2">
          Methodology
        </h3>
        <div className="text-[10px] text-[var(--color-text-muted)] space-y-1 font-mono">
          <p>Walk-forward validation &middot; Purged k-fold (gap=3, embargo=2)</p>
          <p>
            Cost model: spread + linear impact + exchange fees (maker/taker)
          </p>
          <p>Triple-barrier labels: TP=3%, SL=1.5%, max_hold=12 bars</p>
        </div>
      </div>
    </>
  );
}
