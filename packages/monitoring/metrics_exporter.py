"""Prometheus metrics exporter for trading system observability."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Gauges (current state)
equity_gauge = Gauge("trading_equity_usd", "Current portfolio equity in USD")
drawdown_gauge = Gauge("trading_drawdown_pct", "Current drawdown percentage")
positions_gauge = Gauge("trading_open_positions", "Number of open positions")
signal_strength_gauge = Gauge(
    "trading_signal_strength", "Latest signal strength", ["symbol"]
)
regime_gauge = Gauge("trading_regime", "Current market regime (0=trending, 1=mr, 2=choppy)")
data_freshness_gauge = Gauge(
    "trading_data_freshness_seconds", "Seconds since last data update", ["source"]
)

# Counters (cumulative)
orders_counter = Counter("trading_orders_total", "Total orders submitted", ["side", "status"])
rejections_counter = Counter(
    "trading_rejections_total", "Total risk rejections", ["reason"]
)
errors_counter = Counter("trading_errors_total", "Total errors", ["component"])

# Histograms (distributions)
fill_latency_histogram = Histogram(
    "trading_fill_latency_seconds",
    "Order fill latency",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)


def start_metrics_server(port: int = 9090) -> None:
    """Start the Prometheus metrics HTTP server."""
    start_http_server(port)


def update_portfolio_metrics(equity: float, drawdown_pct: float, n_positions: int) -> None:
    """Update portfolio-related gauges."""
    equity_gauge.set(equity)
    drawdown_gauge.set(drawdown_pct)
    positions_gauge.set(n_positions)


def record_order(side: str, status: str) -> None:
    orders_counter.labels(side=side, status=status).inc()


def record_rejection(reason: str) -> None:
    rejections_counter.labels(reason=reason).inc()


def record_error(component: str) -> None:
    errors_counter.labels(component=component).inc()


def record_fill_latency(seconds: float) -> None:
    fill_latency_histogram.observe(seconds)
