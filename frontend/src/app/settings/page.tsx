"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ModelStatus, SystemConfig } from "@/lib/api";
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
    return <span className="text-[var(--color-accent-cyan)] font-mono tabular-nums">{value}</span>;
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

  // Exchange keys (session-scoped, not persisted)
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [testingKeys, setTestingKeys] = useState(false);
  const [keyStatus, setKeyStatus] = useState<string | null>(null);

  // Model retrain
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [retraining, setRetraining] = useState(false);

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

  // Load model status on mount
  useEffect(() => {
    api.modelStatus().then((s) => {
      if (s) setModelStatus(s);
    });
  }, []);

  const handleTestKeys = async () => {
    if (!apiKey || !apiSecret) {
      showToast("Enter both API key and secret", "error");
      return;
    }
    setTestingKeys(true);
    setKeyStatus(null);
    const result = await api.testExchangeKeys(apiKey, apiSecret);
    setTestingKeys(false);
    if (result?.status === "ok") {
      setKeyStatus("valid");
      showToast(result.message, "success");
    } else {
      setKeyStatus("invalid");
      showToast(result?.message || "Connection test failed", "error");
    }
  };

  const handleRetrain = async () => {
    setRetraining(true);
    const result = await api.modelRetrain();
    setRetraining(false);
    if (result) {
      setModelStatus(result);
      if (result.status === "ok") {
        showToast(result.message, "success");
      } else {
        showToast(result.message, "error");
      }
    } else {
      showToast("Retrain request failed", "error");
    }
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
          className={`fixed top-4 right-4 z-50 px-4 py-2.5 rounded-lg text-xs font-medium animate-fade-in shadow-lg ${
            toast.type === "success"
              ? "bg-[var(--color-accent-green)]/20 text-[var(--color-accent-green)] border border-[var(--color-accent-green)]/30"
              : "bg-[var(--color-accent-red)]/20 text-[var(--color-accent-red)] border border-[var(--color-accent-red)]/30"
          }`}
        >
          {toast.message}
        </div>
      )}

      {/* Header */}
      <div className="card-glow bg-[var(--color-bg-card)] rounded-lg px-6 py-4 mb-4 animate-fade-in flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold">System Configuration</h2>
          <p className="text-xs text-[var(--color-text-muted)] mt-1">
            Edit universe, risk, and execution settings. Advanced sections are read-only.
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleReset} className="btn btn-secondary">
            Reset
          </button>
          <button onClick={handleSave} disabled={saving} className="btn btn-primary">
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>

      {config ? (
        <div className="space-y-4 stagger">
          {/* Universe Section */}
          <div className="card-glow bg-[var(--color-bg-card)] rounded-lg p-5">
            <div className="mb-4">
              <h3 className="text-sm font-semibold">Universe</h3>
              <p className="text-xs text-[var(--color-text-muted)]">Trading pairs and data configuration</p>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-[var(--color-text-muted)] block mb-2">Symbols</label>
                <div className="flex gap-2 flex-wrap">
                  {AVAILABLE_SYMBOLS.map((sym) => (
                    <button
                      key={sym}
                      onClick={() => toggleSymbol(sym)}
                      className={`px-3 py-1.5 text-xs rounded-full transition-colors ${
                        symbols.includes(sym)
                          ? "bg-[var(--color-accent-cyan)]/15 text-[var(--color-accent-cyan)] border border-[var(--color-accent-cyan)]/30"
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
                  <label className="text-xs text-[var(--color-text-muted)] block mb-1.5">Timeframe</label>
                  <select
                    value={timeframe}
                    onChange={(e) => setTimeframe(e.target.value)}
                    className="input"
                  >
                    {TIMEFRAMES.map((tf) => (
                      <option key={tf} value={tf}>{tf}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-[var(--color-text-muted)] block mb-1.5">Lookback Days</label>
                  <input
                    type="number"
                    value={lookbackDays}
                    onChange={(e) => setLookbackDays(Number(e.target.value))}
                    min={30}
                    max={3650}
                    className="input tabular-nums font-mono"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Risk Section */}
          <div className="card-glow bg-[var(--color-bg-card)] rounded-lg p-5">
            <div className="mb-4">
              <h3 className="text-sm font-semibold">Risk Management</h3>
              <p className="text-xs text-[var(--color-text-muted)]">Position limits, drawdown guards, kill switch</p>
            </div>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1.5">
                  <label className="text-xs text-[var(--color-text-muted)]">Vol Target</label>
                  <span className="text-xs tabular-nums font-mono text-[var(--color-accent-cyan)]">{(volTarget * 100).toFixed(0)}%</span>
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
                  <label className="text-xs text-[var(--color-text-muted)]">Max Drawdown (Kill Switch)</label>
                  <span className="text-xs tabular-nums font-mono text-[var(--color-accent-red)]">{(maxDrawdown * 100).toFixed(0)}%</span>
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
                  <label className="text-xs text-[var(--color-text-muted)]">Max Position Size</label>
                  <span className="text-xs tabular-nums font-mono text-[var(--color-text-primary)]">{(maxPositionPct * 100).toFixed(0)}%</span>
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
                <label className="text-xs text-[var(--color-text-muted)] block mb-1.5">Min Trade USD</label>
                <input
                  type="number"
                  value={minTradeUsd}
                  onChange={(e) => setMinTradeUsd(Number(e.target.value))}
                  min={1}
                  max={10000}
                  className="input tabular-nums font-mono"
                />
              </div>
            </div>
          </div>

          {/* Execution Section */}
          <div className="card-glow bg-[var(--color-bg-card)] rounded-lg p-5">
            <div className="mb-4">
              <h3 className="text-sm font-semibold">Execution</h3>
              <p className="text-xs text-[var(--color-text-muted)]">Order types, slippage model, retry policy</p>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-[var(--color-text-muted)] block mb-2">Mode</label>
                <div className="flex gap-2">
                  {["paper", "live"].map((mode) => (
                    <button
                      key={mode}
                      onClick={() => setExecMode(mode)}
                      className={`px-4 py-1.5 text-xs rounded-md transition-colors ${
                        execMode === mode
                          ? mode === "live"
                            ? "bg-[var(--color-accent-red)]/15 text-[var(--color-accent-red)] border border-[var(--color-accent-red)]/30"
                            : "bg-[var(--color-accent-green)]/15 text-[var(--color-accent-green)] border border-[var(--color-accent-green)]/30"
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
                  <label className="text-xs text-[var(--color-text-muted)] block mb-1.5">Timeout (sec)</label>
                  <input
                    type="number"
                    value={orderTimeout}
                    onChange={(e) => setOrderTimeout(Number(e.target.value))}
                    min={10}
                    max={600}
                    className="input tabular-nums font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs text-[var(--color-text-muted)] block mb-1.5">Max Retries</label>
                  <input
                    type="number"
                    value={maxRetries}
                    onChange={(e) => setMaxRetries(Number(e.target.value))}
                    min={0}
                    max={10}
                    className="input tabular-nums font-mono"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Exchange API Keys */}
          <div className="card-glow bg-[var(--color-bg-card)] rounded-lg p-5">
            <div className="mb-4">
              <h3 className="text-sm font-semibold">Exchange Connection</h3>
              <p className="text-xs text-[var(--color-text-muted)]">
                API keys are used for connection testing only (not stored on disk)
              </p>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-[var(--color-text-muted)] block mb-1.5">API Key</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => { setApiKey(e.target.value); setKeyStatus(null); }}
                  placeholder="Enter Binance API key"
                  className="input font-mono text-xs"
                  autoComplete="off"
                />
              </div>
              <div>
                <label className="text-xs text-[var(--color-text-muted)] block mb-1.5">API Secret</label>
                <input
                  type="password"
                  value={apiSecret}
                  onChange={(e) => { setApiSecret(e.target.value); setKeyStatus(null); }}
                  placeholder="Enter Binance API secret"
                  className="input font-mono text-xs"
                  autoComplete="off"
                />
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleTestKeys}
                  disabled={testingKeys || !apiKey || !apiSecret}
                  className="btn btn-secondary"
                >
                  {testingKeys ? "Testing..." : "Test Connection"}
                </button>
                {keyStatus === "valid" && (
                  <span className="text-xs text-[var(--color-accent-green)]">Connected</span>
                )}
                {keyStatus === "invalid" && (
                  <span className="text-xs text-[var(--color-accent-red)]">Invalid</span>
                )}
              </div>
              <p className="text-[10px] text-[var(--color-text-muted)]">
                For live trading, set BINANCE_API_KEY and BINANCE_API_SECRET as environment variables on the worker process.
              </p>
            </div>
          </div>

          {/* Model Management */}
          <div className="card-glow bg-[var(--color-bg-card)] rounded-lg p-5">
            <div className="mb-4">
              <h3 className="text-sm font-semibold">Model Management</h3>
              <p className="text-xs text-[var(--color-text-muted)]">
                LightGBM quantile model — retrain on latest candle data
              </p>
            </div>
            <div className="space-y-3">
              {modelStatus && (
                <div className="text-xs space-y-1">
                  <div className="flex gap-2">
                    <span className="text-[var(--color-text-muted)]">Status:</span>
                    <span className={
                      modelStatus.status === "ok"
                        ? "text-[var(--color-accent-green)]"
                        : modelStatus.status === "no_model"
                        ? "text-[var(--color-text-muted)]"
                        : "text-[var(--color-accent-red)]"
                    }>
                      {modelStatus.status === "ok" ? "Trained" : modelStatus.status === "no_model" ? "No model" : modelStatus.status}
                    </span>
                  </div>
                  {modelStatus.last_trained && (
                    <div className="flex gap-2">
                      <span className="text-[var(--color-text-muted)]">Last trained:</span>
                      <span className="font-mono tabular-nums">{new Date(modelStatus.last_trained).toLocaleString()}</span>
                    </div>
                  )}
                  {modelStatus.train_accuracy != null && (
                    <div className="flex gap-2">
                      <span className="text-[var(--color-text-muted)]">Validation accuracy:</span>
                      <span className="font-mono tabular-nums text-[var(--color-accent-cyan)]">
                        {(modelStatus.train_accuracy * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}
                </div>
              )}
              <button
                onClick={handleRetrain}
                disabled={retraining}
                className="btn btn-primary"
              >
                {retraining ? "Retraining..." : "Retrain Model"}
              </button>
            </div>
          </div>

          {/* Divider */}
          <div className="border-t border-[var(--color-border)] my-2" />

          {/* Read-only sections */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {Object.keys(sectionMeta).map((key) => {
              const meta = sectionMeta[key];
              const data = config[key as keyof SystemConfig];
              return (
                <div key={key} className="card-glow bg-[var(--color-bg-card)] rounded-lg p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-semibold">{meta.label}</h3>
                      <p className="text-xs text-[var(--color-text-muted)]">{meta.description}</p>
                    </div>
                    <span className="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] border border-[var(--color-border)] rounded-full px-2 py-0.5">
                      Read-only
                    </span>
                  </div>
                  <div className="text-xs space-y-1">
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
        <div className="space-y-3">
          <div className="skeleton h-48 rounded-lg" />
          <div className="skeleton h-48 rounded-lg" />
          <div className="skeleton h-32 rounded-lg" />
        </div>
      )}
    </>
  );
}
