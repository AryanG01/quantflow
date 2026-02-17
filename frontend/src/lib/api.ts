const API_BASE = "/api";

export interface Signal {
  symbol: string;
  direction: "long" | "short" | "flat";
  strength: number;
  confidence: number;
  regime: string;
  components: Record<string, number>;
  timestamp: string;
}

export interface Position {
  symbol: string;
  side: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
}

export interface Portfolio {
  equity: number;
  cash: number;
  positions_value: number;
  unrealized_pnl: number;
  realized_pnl: number;
  drawdown_pct: number;
  timestamp: string;
}

export interface RiskMetrics {
  current_drawdown_pct: number;
  max_drawdown_pct: number;
  portfolio_vol: number;
  sharpe_ratio: number | null;
  concentration_pct: number;
  kill_switch_active: boolean;
}

export interface Regime {
  current: string;
  confidence: number;
  history: Array<{ timestamp: string; regime: string }>;
}

export interface EquityCurvePoint {
  timestamp: string;
  equity: number;
}

export interface BacktestResult {
  strategy: string;
  total_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  total_trades: number;
  hit_rate: number;
}

export interface Trade {
  id: string;
  timestamp: string;
  symbol: string;
  side: string;
  quantity: number;
  price: number;
  fees: number;
  pnl: number;
  signal_strength: number;
  regime: string;
}

export interface SystemConfig {
  universe: Record<string, unknown>;
  risk: Record<string, unknown>;
  execution: Record<string, unknown>;
  features: Record<string, unknown>;
  model: Record<string, unknown>;
  regime: Record<string, unknown>;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  version: string;
  uptime_seconds: number;
  db_connected: boolean;
  candle_count: number;
}

async function fetchJson<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export const api = {
  health: () => fetchJson<HealthStatus>("/health"),
  signals: () => fetchJson<Signal[]>("/signals"),
  portfolio: () => fetchJson<Portfolio>("/portfolio"),
  positions: () => fetchJson<Position[]>("/positions"),
  risk: () => fetchJson<RiskMetrics>("/risk"),
  regime: () => fetchJson<Regime>("/regime"),
  equityHistory: () => fetchJson<EquityCurvePoint[]>("/equity-history"),
  backtestResults: () => fetchJson<BacktestResult[]>("/backtest-results"),
  trades: () => fetchJson<Trade[]>("/trades"),
  config: () => fetchJson<SystemConfig>("/config"),
};
