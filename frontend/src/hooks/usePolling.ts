"use client";
import { useEffect, useState, useCallback } from "react";

export function usePolling<T>(
  fetcher: () => Promise<T | null>,
  intervalMs: number = 5000
): { data: T | null; loading: boolean; error: boolean } {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const poll = useCallback(async () => {
    try {
      const result = await fetcher();
      setData(result);
      setError(false);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [fetcher]);

  useEffect(() => {
    poll();
    const id = setInterval(poll, intervalMs);
    return () => clearInterval(id);
  }, [poll, intervalMs]);

  return { data, loading, error };
}
