"""Auth m2m mínima (D5). No loguear secretos.
Formato: SKYCAST_M2M_KEYS='callerA:secretA:scope1|scope2'
Si SKYCAST_M2M_REQUIRED=true y hay keys configuradas, exige credencial válida con scope.
"""
from __future__ import annotations

import os
from typing import Optional, Set

from fastapi import Header, HTTPException, Request


def _load_keys() -> list[tuple[str, Set[str]]]:
    raw = os.getenv("SKYCAST_M2M_KEYS", "")
    keys = []
    for part in raw.split(";"):
        part = part.strip()
        if not part or part.count(":") < 2:
            continue
        _caller, secret, scopes_s = part.split(":", 2)
        keys.append((secret.strip(), {s.strip() for s in scopes_s.split("|") if s.strip()}))
    single = os.getenv("SKYCAST_M2M_API_KEY", "").strip()
    if single:
        scopes = {s.strip() for s in os.getenv("SKYCAST_M2M_SCOPES", "weather:route").split(",") if s.strip()}
        keys.append((single, scopes))
    return keys


def _load_callers() -> list[tuple[str, str, Set[str]]]:
    raw = os.getenv("SKYCAST_M2M_KEYS", "")
    keys = []
    for part in raw.split(";"):
        part = part.strip()
        if not part or part.count(":") < 2:
            continue
        caller, secret, scopes_s = part.split(":", 2)
        keys.append((caller.strip(), secret.strip(), {s.strip() for s in scopes_s.split("|") if s.strip()}))
    single = os.getenv("SKYCAST_M2M_API_KEY", "").strip()
    if single:
        caller = os.getenv("SKYCAST_M2M_CALLER", "m2m").strip()
        scopes = {s.strip() for s in os.getenv("SKYCAST_M2M_SCOPES", "weather:route,weather:validate").split(",") if s.strip()}
        keys.append((caller, single, scopes))
    return keys


def require_m2m_if_configured(required_scope: str):
    async def _dep(
        request: Request,
        x_api_key: str = Header("", alias="X-API-Key"),
        authorization: str = Header("", alias="Authorization"),
    ):
        keys = _load_callers()
        required = os.getenv("SKYCAST_M2M_REQUIRED", "false").lower() in ("1", "true", "yes")
        request.state.correlation_id = request.headers.get("X-Correlation-Id") or request.headers.get("X-Request-Id") or ""
        if not keys or not required:
            request.state.caller = getattr(request.state, "caller", "anonymous")
            return None
        candidate = (x_api_key or "").strip()
        if not candidate and authorization.startswith("Bearer "):
            candidate = authorization.replace("Bearer ", "", 1).strip()
        if not candidate:
            raise HTTPException(status_code=401, detail="m2m_credentials_required")
        for caller, secret, scopes in keys:
            if candidate == secret:
                if required_scope not in scopes:
                    raise HTTPException(status_code=403, detail="insufficient_scope")
                request.state.caller = caller
                return {"scope": required_scope, "caller": caller}
        raise HTTPException(status_code=401, detail="invalid_m2m_credentials")
    return _dep
