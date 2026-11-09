"""Rate limit (D5). In-memory por defecto; opcional Redis si REDIS_URL configurado y `redis` instalado."""
from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import HTTPException, Request

_buckets: Dict[str, Deque[float]] = defaultdict(deque)
_redis = None
_redis_checked = False


def _get_redis():
    global _redis, _redis_checked
    if _redis_checked:
        return _redis
    _redis_checked = True
    url = os.getenv("REDIS_URL", "").strip()
    if not url:
        return None
    try:
        import redis  # type: ignore

        _redis = redis.Redis.from_url(url, decode_responses=True)
        _redis.ping()
    except Exception:
        _redis = None
    return _redis


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
        caller = getattr(request.state, "caller", None) or (request.client.host if request.client else "unknown")
        key = f"rl:{spec_env}:{caller}"
        r = _get_redis()
        if r is not None:
            try:
                n = r.incr(key)
                if n == 1:
                    r.expire(key, window)
                if int(n) > limit_n:
                    raise HTTPException(status_code=429, detail="rate_limit_exceeded")
                return
            except HTTPException:
                raise
            except Exception:
                pass
        now = time.time()
        q = _buckets[key]
        while q and q[0] <= now - window:
            q.popleft()
        if len(q) >= limit_n:
            raise HTTPException(status_code=429, detail="rate_limit_exceeded")
        q.append(now)
    return _dep
