"""UTC time helpers and bar alignment utilities."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

TIMEFRAME_SECONDS: dict[str, int] = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
}


def utc_now() -> datetime:
    """Current UTC time."""
    return datetime.now(UTC)


def to_utc(dt: datetime) -> datetime:
    """Ensure a datetime is UTC-aware."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def align_to_bar(dt: datetime, timeframe: str) -> datetime:
    """Align a datetime to the start of the current bar.

    For 4h bars, aligns to 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC.
    """
    seconds = TIMEFRAME_SECONDS.get(timeframe)
    if seconds is None:
        raise ValueError(f"Unknown timeframe: {timeframe}")

    dt = to_utc(dt)
    epoch = datetime(2000, 1, 1, tzinfo=UTC)
    elapsed = (dt - epoch).total_seconds()
    aligned_elapsed = (elapsed // seconds) * seconds
    return epoch + timedelta(seconds=aligned_elapsed)


def bars_between(start: datetime, end: datetime, timeframe: str) -> int:
    """Count bars between two datetimes."""
    seconds = TIMEFRAME_SECONDS.get(timeframe)
    if seconds is None:
        raise ValueError(f"Unknown timeframe: {timeframe}")
    return int((to_utc(end) - to_utc(start)).total_seconds() / seconds)


def timeframe_to_ms(timeframe: str) -> int:
    """Convert timeframe string to milliseconds."""
    seconds = TIMEFRAME_SECONDS.get(timeframe)
    if seconds is None:
        raise ValueError(f"Unknown timeframe: {timeframe}")
    return seconds * 1000
