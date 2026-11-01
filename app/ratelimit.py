"""Small in-memory sliding-window rate limiter shared by the web and live servers."""

import time
from collections import deque
from typing import Deque, Dict


class RateLimiter:
    """Per client and bucket. Memory is bounded: stale clients are purged once the table is large.

    On Vercel each instance has its own memory, so this is only a best-effort first line of defence;
    add a Vercel Firewall rate-limit rule for real protection (see README).
    """

    def __init__(self, max_clients: int = 5000):
        self.hits: Dict[str, Deque[float]] = {}
        self.max_clients = max_clients

    def allow(self, client: str, bucket: str, limit: int, window: float = 60.0) -> bool:
        now = time.monotonic()
        if len(self.hits) > self.max_clients:
            self.hits = {k: q for k, q in self.hits.items() if q and now - q[-1] < window}
        q = self.hits.setdefault(f"{bucket}:{client}", deque())
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        return True
