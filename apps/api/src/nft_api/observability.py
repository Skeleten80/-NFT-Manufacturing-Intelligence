"""Process-local measurement and safe error-reporting boundary.

An exporter can consume snapshots later; do not use tenant IDs as metric labels.
"""

from collections import Counter
from dataclasses import dataclass, field
from threading import Lock
from typing import Protocol


class ErrorReporter(Protocol):
    def report(self, request_id: str, error_type: str) -> None: ...


class NullErrorReporter:
    def report(self, request_id: str, error_type: str) -> None:
        """No external reporting configured in Phase 0."""


@dataclass
class RequestMetrics:
    counts: Counter[int] = field(default_factory=Counter)
    duration_ms: float = 0.0
    _lock: Lock = field(default_factory=Lock)

    def observe(self, status: int, duration_ms: float) -> None:
        with self._lock:
            self.counts[status] += 1
            self.duration_ms += duration_ms

    def snapshot(self) -> dict[str, int | float]:
        with self._lock:
            return {
                "requests": sum(self.counts.values()),
                "server_errors": sum(n for status, n in self.counts.items() if status >= 500),
                "duration_ms": self.duration_ms,
            }
