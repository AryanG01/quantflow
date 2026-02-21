const API_BASE = "/api";

export const FALLBACK_SYMBOLS = [
  "BTC/USDT",
  "ETH/USDT",
  "SOL/USDT",
  "AVAX/USDT",
  "DOGE/USDT",
];

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

export interface Universe {
  symbols: string[];
  timeframe: string;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  version: string;
  uptime_seconds: number;
  db_connected: boolean;
  candle_count: number;
}

export interface BacktestRunRequest {
  symbol: string;
  strategy: string;
  lookback_days?: number;
  initial_capital?: number;
}

export interface OrderRequest {
  symbol: string;
  side: "buy" | "sell";
  quantity: number;
  order_type?: "market" | "limit";
  price?: number;
}

export interface PortfolioAnalytics {
  daily_return: number | null;
  weekly_return: number | null;
  rolling_sharpe_30d: number | null;
  max_drawdown: number | null;
  max_drawdown_duration_bars: number;
  equity_series: EquityCurvePoint[];
}

export interface ModelStatus {
  status: string;
  message: string;
  model_id: string | null;
  val_accuracy: number | null;
  last_trained: string | null;
}

export interface ExchangeTestResult {
  status: string;
  message: string;
}

async function fetchJson<T>(path: string): Promise<T | null> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 10000);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      cache: "no-store",
      signal: controller.signal,
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

async function postJson<T>(path: string, body: unknown): Promise<T | null> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 5000);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
      signal: controller.signal,
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

async function patchJson<T>(path: string, body: unknown): Promise<T | null> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 5000);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
      signal: controller.signal,
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
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
  universe: () => fetchJson<Universe>("/config/universe"),
  prices: () => fetchJson<Record<string, number>>("/prices"),
  updateConfig: (body: Partial<SystemConfig>) =>
    patchJson<SystemConfig>("/config", body),
  runBacktest: (body: BacktestRunRequest) =>
    postJson<BacktestResult>("/backtest/run", body),
  placeOrder: (body: OrderRequest) =>
    postJson<Trade>("/orders", body),
  portfolioAnalytics: () =>
    fetchJson<PortfolioAnalytics>("/portfolio/analytics"),
  modelStatus: () => fetchJson<ModelStatus>("/model/status"),
  modelRetrain: () => postJson<ModelStatus>("/model/retrain", {}),
  testExchangeKeys: (apiKey: string, apiSecret: string) =>
    postJson<ExchangeTestResult>("/config/exchange/test", {
      api_key: apiKey,
      api_secret: apiSecret,
    }),
};
