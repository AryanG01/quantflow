"""Token bucket rate limiter for exchange API calls."""

from __future__ import annotations

import asyncio
import time


class TokenBucketRateLimiter:
    """Token bucket rate limiter with configurable requests per minute."""

    def __init__(self, requests_per_minute: int) -> None:
        self._rate = requests_per_minute / 60.0  # tokens per second
        self._max_tokens = float(requests_per_minute)
        self._tokens = self._max_tokens
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._max_tokens, self._tokens + elapsed * self._rate)
        self._last_refill = now

    async def acquire(self) -> None:
        """Wait until a token is available, then consume it."""
        async with self._lock:
            self._refill()
            if self._tokens < 1.0:
                wait_time = (1.0 - self._tokens) / self._rate
                await asyncio.sleep(wait_time)
                self._refill()
            self._tokens -= 1.0
