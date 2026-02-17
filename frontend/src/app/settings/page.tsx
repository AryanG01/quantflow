"use client";

import { useCallback, useEffect, useState } from "react";
import { api, SystemConfig } from "@/lib/api";
import { usePolling } from "@/hooks/usePolling";

type Toast = { message: string; type: "success" | "error" } | null;

const sectionMeta: Record<string, { label: string; description: string }> = {
  features: {
    label: "Features",
    description: "Technical indicators and normalization",
  },
  model: {
    label: "Model",
    description: "LightGBM parameters and walk-forward config",
  },
  regime: {
    label: "Regime Detection",
    description: "HMM states and transition thresholds",
  },
};

function renderValue(value: unknown, depth: number = 0): React.ReactNode {
  if (value === null || value === undefined) {
    return <span className="text-[var(--color-text-muted)]">null</span>;
  }
  if (typeof value === "boolean") {
    return (
      <span className={value ? "text-[var(--color-accent-green)]" : "text-[var(--color-accent-red)]"}>
        {String(value)}
      </span>
    );
  }
  if (typeof value === "number") {
    return <span className="text-[var(--color-accent-cyan)]">{value}</span>;
  }
  if (typeof value === "string") {
    return <span className="text-[var(--color-text-primary)]">&quot;{value}&quot;</span>;
  }
  if (Array.isArray(value)) {
    return (
      <span className="text-[var(--color-text-secondary)]">
        [{value.map((v, i) => (
          <span key={i}>
            {i > 0 && ", "}
            {renderValue(v, depth + 1)}
          </span>
        ))}]
      </span>
    );
  }
  if (typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>);
    if (depth > 1) {
      return <span className="text-[var(--color-text-muted)]">{`{${entries.length} keys}`}</span>;
    }
    return (
      <div className="ml-4 border-l border-[var(--color-border)] pl-3 space-y-1">
        {entries.map(([k, v]) => (
          <div key={k} className="flex items-start gap-2">
            <span className="text-[var(--color-text-muted)] shrink-0">{k}:</span>
            <span>{renderValue(v, depth + 1)}</span>
          </div>
        ))}
      </div>
    );
  }
  return <span>{String(value)}</span>;
}

const AVAILABLE_SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "DOGE/USDT"];
const TIMEFRAMES = ["1h", "4h", "1d"];

export default function SettingsPage() {
  const { data: config } = usePolling(useCallback(() => api.config(), []), 30000);

  // Editable state
  const [symbols, setSymbols] = useState<string[]>([]);
  const [timeframe, setTimeframe] = useState("4h");
  const [lookbackDays, setLookbackDays] = useState(730);
  const [volTarget, setVolTarget] = useState(0.15);
  const [maxDrawdown, setMaxDrawdown] = useState(0.15);
  const [maxPositionPct, setMaxPositionPct] = useState(0.25);
  const [minTradeUsd, setMinTradeUsd] = useState(10.0);
  const [execMode, setExecMode] = useState("paper");
  const [orderTimeout, setOrderTimeout] = useState(120);
  const [maxRetries, setMaxRetries] = useState(3);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<Toast>(null);

  // Sync from server config
  useEffect(() => {
    if (!config) return;
    const u = config.universe as Record<string, unknown>;
    const r = config.risk as Record<string, unknown>;
    const e = config.execution as Record<string, unknown>;
    setSymbols((u.symbols as string[]) || []);
    setTimeframe((u.timeframe as string) || "4h");
    setLookbackDays((u.lookback_days as number) || 730);
    setVolTarget((r.vol_target as number) || 0.15);
    setMaxDrawdown((r.max_drawdown_pct as number) || 0.15);
    setMaxPositionPct((r.max_position_pct as number) || 0.25);
    setMinTradeUsd((r.min_trade_usd as number) || 10.0);
    setExecMode((e.mode as string) || "paper");
    setOrderTimeout((e.order_timeout_seconds as number) || 120);
    setMaxRetries((e.max_retries as number) || 3);
  }, [config]);

  const showToast = (message: string, type: "success" | "error") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleSave = async () => {
    setSaving(true);
    const result = await api.updateConfig({
      universe: { symbols, timeframe, lookback_days: lookbackDays },
      risk: {
        vol_target: volTarget,
        max_drawdown_pct: maxDrawdown,
        max_position_pct: maxPositionPct,
        min_trade_usd: minTradeUsd,
      },
      execution: {
        mode: execMode,
        order_timeout_seconds: orderTimeout,
        max_retries: maxRetries,
      },
    });
    setSaving(false);
    if (result) {
      showToast("Configuration saved successfully", "success");
    } else {
      showToast("Failed to save configuration", "error");
    }
  };

  const handleReset = () => {
    if (!config) return;
    const u = config.universe as Record<string, unknown>;
    const r = config.risk as Record<string, unknown>;
    const e = config.execution as Record<string, unknown>;
    setSymbols((u.symbols as string[]) || []);
    setTimeframe((u.timeframe as string) || "4h");
    setLookbackDays((u.lookback_days as number) || 730);
    setVolTarget((r.vol_target as number) || 0.15);
    setMaxDrawdown((r.max_drawdown_pct as number) || 0.15);
    setMaxPositionPct((r.max_position_pct as number) || 0.25);
    setMinTradeUsd((r.min_trade_usd as number) || 10.0);
    setExecMode((e.mode as string) || "paper");
    setOrderTimeout((e.order_timeout_seconds as number) || 120);
    setMaxRetries((e.max_retries as number) || 3);
    showToast("Reset to last saved values", "success");
  };

  const toggleSymbol = (sym: string) => {
    setSymbols((prev) =>
      prev.includes(sym) ? prev.filter((s) => s !== sym) : [...prev, sym]
    );
  };

  return (
    <>
      {/* Toast */}
      {toast && (
        <div
          className={`fixed top-4 right-4 z-50 px-4 py-2 rounded-sm text-xs font-medium animate-fade-in ${
            toast.type === "success"
              ? "bg-[var(--color-accent-green)]/20 text-[var(--color-accent-green)] border border-[var(--color-accent-green)]/30"
              : "bg-[var(--color-accent-red)]/20 text-[var(--color-accent-red)] border border-[var(--color-accent-red)]/30"
          }`}
        >
          {toast.message}
        </div>
      )}

      {/* Header */}
      <div className="card-glow bg-[var(--color-bg-card)] rounded-sm px-6 py-4 mb-4 animate-fade-in flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold">System Configuration</h2>
          <p className="text-[10px] text-[var(--color-text-muted)] mt-1">
            Edit universe, risk, and execution settings. Advanced sections are read-only.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleReset}
            className="px-3 py-1.5 text-[10px] rounded-sm border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
          >
            Reset
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-1.5 text-[10px] rounded-sm bg-[var(--color-accent-cyan)]/20 text-[var(--color-accent-cyan)] border border-[var(--color-accent-cyan)]/30 hover:bg-[var(--color-accent-cyan)]/30 transition-colors disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>

      {config ? (
        <div className="space-y-4 stagger">
          {/* Universe Section */}
          <div className="card-glow bg-[var(--color-bg-card)] rounded-sm p-4">
            <div className="mb-4">
              <h3 className="text-xs font-semibold">Universe</h3>
              <p className="text-[10px] text-[var(--color-text-muted)]">Trading pairs and data configuration</p>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] block mb-2">Symbols</label>
                <div className="flex gap-2 flex-wrap">
                  {AVAILABLE_SYMBOLS.map((sym) => (
                    <button
                      key={sym}
                      onClick={() => toggleSymbol(sym)}
                      className={`px-3 py-1 text-[11px] rounded-sm transition-colors ${
                        symbols.includes(sym)
                          ? "bg-[var(--color-accent-cyan)]/20 text-[var(--color-accent-cyan)] border border-[var(--color-accent-cyan)]/30"
                          : "border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
                      }`}
                    >
                      {sym}
                    </button>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] block mb-1.5">Timeframe</label>
                  <select
                    value={timeframe}
                    onChange={(e) => setTimeframe(e.target.value)}
                    className="w-full bg-[var(--color-bg-main)] border border-[var(--color-border)] rounded-sm px-3 py-1.5 text-xs text-[var(--color-text-primary)] focus:border-[var(--color-accent-cyan)] outline-none"
                  >
                    {TIMEFRAMES.map((tf) => (
                      <option key={tf} value={tf}>{tf}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] block mb-1.5">Lookback Days</label>
                  <input
                    type="number"
                    value={lookbackDays}
                    onChange={(e) => setLookbackDays(Number(e.target.value))}
                    min={30}
                    max={3650}
                    className="w-full bg-[var(--color-bg-main)] border border-[var(--color-border)] rounded-sm px-3 py-1.5 text-xs text-[var(--color-text-primary)] tabular-nums focus:border-[var(--color-accent-cyan)] outline-none"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Risk Section */}
          <div className="card-glow bg-[var(--color-bg-card)] rounded-sm p-4">
            <div className="mb-4">
              <h3 className="text-xs font-semibold">Risk Management</h3>
              <p className="text-[10px] text-[var(--color-text-muted)]">Position limits, drawdown guards, kill switch</p>
            </div>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1.5">
                  <label className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)]">Vol Target</label>
                  <span className="text-[11px] tabular-nums text-[var(--color-accent-cyan)]">{(volTarget * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min={0.05} max={0.30} step={0.01}
                  value={volTarget}
                  onChange={(e) => setVolTarget(Number(e.target.value))}
                  className="w-full accent-[var(--color-accent-cyan)] h-1"
                />
              </div>
              <div>
                <div className="flex justify-between mb-1.5">
                  <label className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)]">Max Drawdown (Kill Switch)</label>
                  <span className="text-[11px] tabular-nums text-[var(--color-accent-red)]">{(maxDrawdown * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min={0.05} max={0.25} step={0.01}
                  value={maxDrawdown}
                  onChange={(e) => setMaxDrawdown(Number(e.target.value))}
                  className="w-full accent-[var(--color-accent-red)] h-1"
                />
              </div>
              <div>
                <div className="flex justify-between mb-1.5">
                  <label className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)]">Max Position Size</label>
                  <span className="text-[11px] tabular-nums text-[var(--color-text-primary)]">{(maxPositionPct * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min={0.10} max={0.50} step={0.01}
                  value={maxPositionPct}
                  onChange={(e) => setMaxPositionPct(Number(e.target.value))}
                  className="w-full accent-[var(--color-accent-cyan)] h-1"
                />
              </div>
              <div>
                <label className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] block mb-1.5">Min Trade USD</label>
                <input
                  type="number"
                  value={minTradeUsd}
                  onChange={(e) => setMinTradeUsd(Number(e.target.value))}
                  min={1}
                  max={10000}
                  className="w-full bg-[var(--color-bg-main)] border border-[var(--color-border)] rounded-sm px-3 py-1.5 text-xs text-[var(--color-text-primary)] tabular-nums focus:border-[var(--color-accent-cyan)] outline-none"
                />
              </div>
            </div>
          </div>

          {/* Execution Section */}
          <div className="card-glow bg-[var(--color-bg-card)] rounded-sm p-4">
            <div className="mb-4">
              <h3 className="text-xs font-semibold">Execution</h3>
              <p className="text-[10px] text-[var(--color-text-muted)]">Order types, slippage model, retry policy</p>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] block mb-2">Mode</label>
                <div className="flex gap-2">
                  {["paper", "live"].map((mode) => (
                    <button
                      key={mode}
                      onClick={() => setExecMode(mode)}
                      className={`px-4 py-1.5 text-[11px] rounded-sm transition-colors ${
                        execMode === mode
                          ? mode === "live"
                            ? "bg-[var(--color-accent-red)]/20 text-[var(--color-accent-red)] border border-[var(--color-accent-red)]/30"
                            : "bg-[var(--color-accent-green)]/20 text-[var(--color-accent-green)] border border-[var(--color-accent-green)]/30"
                          : "border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
                      }`}
                    >
                      {mode.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] block mb-1.5">Timeout (sec)</label>
                  <input
                    type="number"
                    value={orderTimeout}
                    onChange={(e) => setOrderTimeout(Number(e.target.value))}
                    min={10}
                    max={600}
                    className="w-full bg-[var(--color-bg-main)] border border-[var(--color-border)] rounded-sm px-3 py-1.5 text-xs text-[var(--color-text-primary)] tabular-nums focus:border-[var(--color-accent-cyan)] outline-none"
                  />
                </div>
                <div>
                  <label className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] block mb-1.5">Max Retries</label>
                  <input
                    type="number"
                    value={maxRetries}
                    onChange={(e) => setMaxRetries(Number(e.target.value))}
                    min={0}
                    max={10}
                    className="w-full bg-[var(--color-bg-main)] border border-[var(--color-border)] rounded-sm px-3 py-1.5 text-xs text-[var(--color-text-primary)] tabular-nums focus:border-[var(--color-accent-cyan)] outline-none"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Read-only sections */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {Object.keys(sectionMeta).map((key) => {
              const meta = sectionMeta[key];
              const data = config[key as keyof SystemConfig];
              return (
                <div key={key} className="card-glow bg-[var(--color-bg-card)] rounded-sm p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <div>
                      <h3 className="text-xs font-semibold">{meta.label}</h3>
                      <p className="text-[10px] text-[var(--color-text-muted)]">{meta.description}</p>
                    </div>
                    <span className="text-[9px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] border border-[var(--color-border)] rounded-sm px-1.5 py-0.5">
                      Read-only
                    </span>
                  </div>
                  <div className="text-[11px] font-mono space-y-1">
                    {data && typeof data === "object" ? (
                      Object.entries(data as Record<string, unknown>).map(([k, v]) => (
                        <div key={k} className="flex items-start gap-2">
                          <span className="text-[var(--color-text-muted)] shrink-0">{k}:</span>
                          <span>{renderValue(v)}</span>
                        </div>
                      ))
                    ) : (
                      <span className="text-[var(--color-text-muted)]">No data</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="card-glow bg-[var(--color-bg-card)] rounded-sm p-8 text-center text-[var(--color-text-muted)] text-sm">
          Loading configuration...
        </div>
      )}
    </>
  );
}
