"use client";
import { useEffect, useState, useCallback, useRef } from "react";

// Module-level cache: survives page navigations within the same browser session.
// Keys should be stable strings matching the endpoint (e.g. "/health").
const _cache = new Map<string, { data: unknown; ts: number }>();

export function usePolling<T>(
  fetcher: () => Promise<T | null>,
  intervalMs: number = 5000,
  cacheKey?: string
): { data: T | null; loading: boolean; error: boolean } {
  const cached = cacheKey ? (_cache.get(cacheKey)?.data as T | undefined) ?? null : null;
  const [data, setData] = useState<T | null>(cached);
  // Don't show loading spinner if we already have cached data from a previous mount.
  const [loading, setLoading] = useState(cached === null);
  const [error, setError] = useState(false);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const poll = useCallback(async () => {
    try {
      const result = await fetcherRef.current();
      if (result !== null) {
        setData(result);
        setError(false);
        if (cacheKey) _cache.set(cacheKey, { data: result, ts: Date.now() });
      } else {
        setError(true);
      }
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [cacheKey]);

  useEffect(() => {
    poll();
    const id = setInterval(poll, intervalMs);
    return () => clearInterval(id);
  }, [poll, intervalMs]);

  return { data, loading, error };
}
