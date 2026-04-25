import { DependencyList, useCallback, useEffect, useRef, useState } from 'react';

interface UseApiDataResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * Generic data-fetching hook used by every analytics page.
 *
 * Replaces the boilerplate of {data, loading, error} useStates + useCallback
 * fetcher + useEffect mount + cancellation guard. The fetcher is captured
 * via a ref so `refetch` always sees the latest closure (e.g. with
 * up-to-date filter selections), while the auto-fetch effect re-runs only
 * when `deps` change.
 *
 * Cancellation guard prevents setState calls on stale unmounted instances
 * (or after deps change before the in-flight request resolves).
 */
export function useApiData<T>(
  fetcher: () => Promise<T>,
  deps: DependencyList = [],
  errorMessage = 'Failed to load data',
): UseApiDataResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const refetch = useCallback(async () => {
    setLoading(true);
    try {
      const result = await fetcherRef.current();
      setData(result);
      setError(null);
    } catch {
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [errorMessage]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetcherRef.current()
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setError(null);
        }
      })
      .catch(() => {
        if (!cancelled) setError(errorMessage);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [errorMessage, ...deps]);

  return { data, loading, error, refetch };
}
