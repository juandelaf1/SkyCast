"""Auditoría mínima de integración (no secretos/PII). Persistencia opcional JSONL via SKYCAST_AUDIT_FILE."""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from fastapi import Request

logger = logging.getLogger("skycast.audit")


def audit_integration(request: Request, contract_version: str, outcome: str = "ok", extra: dict | None = None):
    payload = {
        "event": "integration_call",
        "ts": datetime.now(timezone.utc).isoformat(),
        "caller": getattr(request.state, "caller", "anonymous"),
        "correlation_id": getattr(request.state, "correlation_id", None) or request.headers.get("X-Correlation-Id") or request.headers.get("X-Request-Id") or "",
        "contract_version": contract_version,
        "method": request.method,
        "path": request.url.path,
        "outcome": outcome,
    }
    if extra:
        payload.update(extra)
    logger.info("audit %s", payload)
    path = os.getenv("SKYCAST_AUDIT_FILE", "").strip()
    if path:
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:
            logger.exception("audit file write failed")
