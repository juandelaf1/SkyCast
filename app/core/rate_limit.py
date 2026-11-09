"""Rate limit mínimo en memoria (por caller o IP). No distribuido."""
from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import HTTPException, Request

# (window_start_count not used) simple fixed window
_buckets: Dict[str, Deque[float]] = defaultdict(deque)


def _parse_limit(spec: str) -> Tuple[int, int]:
    # "60/minute"
    try:
        n, per = spec.split("/", 1)
        n = int(n)
        seconds = 60 if "min" in per else 1 if "sec" in per else 3600 if "hour" in per else 60
        return n, seconds
    except Exception:
        return 60, 60


def rate_limit(spec_env: str, default: str = "60/minute"):
    spec = os.getenv(spec_env, default)
    limit_n, window = _parse_limit(spec)

    async def _dep(request: Request):
        caller = getattr(request.state, "caller", None) or request.client.host if request.client else "unknown"
        key = f"{spec_env}:{caller}"
        now = time.time()
        q = _buckets[key]
        while q and q[0] <= now - window:
            q.popleft()
        if len(q) >= limit_n:
            raise HTTPException(status_code=429, detail="rate_limit_exceeded")
        q.append(now)
    return _dep
