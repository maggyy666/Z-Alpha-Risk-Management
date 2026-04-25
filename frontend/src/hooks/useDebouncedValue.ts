import { useEffect, useState } from 'react';

/**
 * Returns `value` echoed after a quiescent period of `delay` ms.
 * Useful for guarding network-bound effects against keystroke storms
 * (e.g. number/text inputs that drive a fetcher via a useEffect dep).
 */
export function useDebouncedValue<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState<T>(value);

  useEffect(() => {
    const handle = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(handle);
  }, [value, delay]);

  return debounced;
}
