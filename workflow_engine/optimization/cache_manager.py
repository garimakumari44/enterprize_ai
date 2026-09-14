from dataclasses import dataclass
from typing import Any, Optional, Dict, Tuple
import time
import hashlib
import json
import threading


# -----------------------------
# Cache Entry
# -----------------------------

@dataclass
class CacheEntry:
    value: Any
    timestamp: float
    ttl: Optional[int]  # seconds; None = infinite


# -----------------------------
# Cache Manager
# -----------------------------

class CacheManager:
    """
    High-performance in-memory cache for workflow execution.

    Features:
    - TTL-based expiration
    - Thread-safe access
    - Workflow-aware cache keys
    - Hash-based normalization for complex inputs
    """

    def __init__(self, default_ttl: int = 300, max_size: int = 10000):
        self.store: Dict[str, CacheEntry] = {}
        self.lock = threading.RLock()
        self.default_ttl = default_ttl
        self.max_size = max_size

    # -------------------------
    # Key generation
    # -------------------------

    def generate_key(self, prefix: str, payload: Any) -> str:
        """
        Creates deterministic cache key for any input.
        Useful for LLM prompts, tool calls, and node outputs.
        """
        try:
            serialized = json.dumps(payload, sort_keys=True, default=str)
        except Exception:
            serialized = str(payload)

        hash_digest = hashlib.sha256(serialized.encode()).hexdigest()
        return f"{prefix}:{hash_digest}"

    # -------------------------
    # Get / Set
    # -------------------------

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        with self.lock:
            if len(self.store) >= self.max_size:
                self._evict_oldest()

            self.store[key] = CacheEntry(
                value=value,
                timestamp=time.time(),
                ttl=ttl if ttl is not None else self.default_ttl,
            )

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            entry = self.store.get(key)

            if not entry:
                return None

            if self._is_expired(entry):
                del self.store[key]
                return None

            return entry.value

    # -------------------------
    # Workflow-aware helpers
    # -------------------------

    def cache_node_result(
        self,
        workflow_id: str,
        node_id: str,
        input_data: Any,
        output: Any,
        ttl: Optional[int] = None,
    ) -> str:
        key = self.generate_key(
            f"wf:{workflow_id}:node:{node_id}", input_data
        )
        self.set(key, output, ttl)
        return key

    def get_node_result(
        self,
        workflow_id: str,
        node_id: str,
        input_data: Any,
    ) -> Optional[Any]:
        key = self.generate_key(
            f"wf:{workflow_id}:node:{node_id}", input_data
        )
        return self.get(key)

    # -------------------------
    # Cache invalidation
    # -------------------------

    def invalidate_prefix(self, prefix: str) -> None:
        with self.lock:
            keys_to_delete = [k for k in self.store if k.startswith(prefix)]
            for k in keys_to_delete:
                del self.store[k]

    def clear(self) -> None:
        with self.lock:
            self.store.clear()

    # -------------------------
    # Internal utilities
    # -------------------------

    def _is_expired(self, entry: CacheEntry) -> bool:
        if entry.ttl is None:
            return False
        return (time.time() - entry.timestamp) > entry.ttl

    def _evict_oldest(self) -> None:
        """
        Simple LRU-like eviction (timestamp-based).
        """
        oldest_key = None
        oldest_time = float("inf")

        for k, v in self.store.items():
            if v.timestamp < oldest_time:
                oldest_time = v.timestamp
                oldest_key = k

        if oldest_key:
            del self.store[oldest_key]

    # -------------------------
    # Stats (useful for observability)
    # -------------------------

    def stats(self) -> Dict[str, Any]:
        with self.lock:
            total = len(self.store)
            expired = sum(1 for v in self.store.values() if self._is_expired(v))

            return {
                "total_entries": total,
                "expired_entries": expired,
                "active_entries": total - expired,
                "max_size": self.max_size,
            }