"""Thread-safe in-memory TTL cache used by DataService and analytics layers.

The cache is intentionally simple: a dict + timestamps, with fnmatch
wildcards for bulk invalidation. It is suitable for a single-pod deployment;
once the backend runs as multiple replicas in K8s this should be replaced
by Redis (the API is compatible -- get/set/clear(pattern)).
"""

from __future__ import annotations

import fnmatch
import threading
import time
from typing import Any, Optional


DEFAULT_TTL_SECONDS = 300  # 5 minutes


class TTLCache:
    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self._data: dict[str, Any] = {}
        self._timestamps: dict[str, float] = {}
        self._lock = threading.Lock()
        self._ttl = ttl_seconds

    @staticmethod
    def build_key(method: str, username: str, **kwargs) -> str:
        """Build a deterministic cache key from (method, username, **kwargs)."""
        parts = [method, username]
        for k, v in sorted(kwargs.items()):
            parts.append(f"{k}:{v}")
        return "|".join(parts)

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._data:
                return None
            ts = self._timestamps.get(key, 0)
            if time.time() - ts >= self._ttl:
                # Expired -- drop
                self._data.pop(key, None)
                self._timestamps.pop(key, None)
                return None
            return self._data[key]

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value
            self._timestamps[key] = time.time()

    def clear(self, pattern: Optional[str] = None) -> int:
        """Clear entries matching fnmatch pattern, or everything if pattern is None.
        Returns number of removed entries."""
        with self._lock:
            if pattern is None:
                removed = len(self._data)
                self._data.clear()
                self._timestamps.clear()
                return removed

            keys = [k for k in self._data if fnmatch.fnmatch(k, pattern)]
            for k in keys:
                self._data.pop(k, None)
                self._timestamps.pop(k, None)
            return len(keys)

    def size(self) -> int:
        with self._lock:
            return len(self._data)
