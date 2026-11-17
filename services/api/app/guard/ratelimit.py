from dataclasses import dataclass, field


@dataclass
class _State:
    tokens: float
    updated: float


@dataclass
class TokenBucket:
    """In-memory token bucket per key. Replaced by a Postgres-backed store for multi-instance."""

    capacity: float
    refill_per_sec: float
    _buckets: dict[str, _State] = field(default_factory=dict)

    def allow(self, key: str, now: float) -> bool:
        state = self._buckets.get(key)
        if state is None:
            state = _State(tokens=self.capacity, updated=now)
            self._buckets[key] = state
        elapsed = max(0.0, now - state.updated)
        state.tokens = min(self.capacity, state.tokens + elapsed * self.refill_per_sec)
        state.updated = now
        if state.tokens >= 1.0:
            state.tokens -= 1.0
            return True
        return False
