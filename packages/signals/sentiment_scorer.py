"""Sentiment scoring with anti-manipulation filters.

Ingests from CryptoPanic and Reddit, applies deduplication,
source credibility caps, and staleness decay to neutral.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from packages.common.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SentimentEvent:
    """A single sentiment data point."""

    time: datetime
    symbol: str
    source: str
    title: str
    raw_score: float  # -1 to 1
    confidence: float  # 0 to 1


@dataclass
class SentimentConfig:
    """Configuration for sentiment scoring."""

    decay_halflife_hours: float = 12.0
    max_events_per_source: int = 10
    staleness_hours: float = 24.0
    dedup_window_hours: float = 6.0


class SentimentScorer:
    """Aggregate sentiment events into a single score with anti-manipulation filters."""

    def __init__(self, config: SentimentConfig | None = None) -> None:
        self._config = config or SentimentConfig()
        self._events: list[SentimentEvent] = []
        self._seen_hashes: set[str] = set()

    def add_event(self, event: SentimentEvent) -> bool:
        """Add a sentiment event with deduplication.

        Returns:
            True if event was added (not a duplicate)
        """
        event_hash = self._hash_event(event)
        if event_hash in self._seen_hashes:
            return False

        self._seen_hashes.add(event_hash)
        self._events.append(event)
        return True

    def compute_score(self, symbol: str, as_of: datetime | None = None) -> float:
        """Compute aggregate sentiment score for a symbol.

        Applies:
        1. Staleness filter (drop events older than staleness_hours)
        2. Source caps (max N events per source)
        3. Time decay (exponential decay toward neutral)

        Args:
            symbol: Trading symbol
            as_of: Reference time (default: now)

        Returns:
            Aggregate sentiment score in [-1, 1], 0 = neutral
        """
        if as_of is None:
            as_of = datetime.now(timezone.utc)

        cutoff = as_of - timedelta(hours=self._config.staleness_hours)

        # Filter relevant events
        relevant = [
            e for e in self._events
            if e.symbol == symbol and e.time >= cutoff
        ]

        if not relevant:
            return 0.0  # neutral when no data

        # Source caps: keep only most recent N per source
        source_events: dict[str, list[SentimentEvent]] = {}
        for e in sorted(relevant, key=lambda x: x.time, reverse=True):
            source_events.setdefault(e.source, [])
            if len(source_events[e.source]) < self._config.max_events_per_source:
                source_events[e.source].append(e)

        capped_events = [e for events in source_events.values() for e in events]

        # Weighted average with time decay
        total_weight = 0.0
        weighted_sum = 0.0
        halflife_seconds = self._config.decay_halflife_hours * 3600

        for e in capped_events:
            age_seconds = (as_of - e.time).total_seconds()
            decay = 0.5 ** (age_seconds / halflife_seconds)
            weight = e.confidence * decay

            weighted_sum += e.raw_score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        score = weighted_sum / total_weight
        return max(-1.0, min(1.0, score))

    def _hash_event(self, event: SentimentEvent) -> str:
        """Create dedup hash from source + title + approximate time."""
        bucket = event.time.replace(
            minute=0, second=0, microsecond=0
        )
        key = f"{event.source}:{event.title}:{bucket.isoformat()}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def clear_old_events(self, before: datetime) -> int:
        """Remove events older than given time."""
        original = len(self._events)
        self._events = [e for e in self._events if e.time >= before]
        removed = original - len(self._events)
        if removed > 0:
            logger.debug("cleared_old_events", count=removed)
        return removed
