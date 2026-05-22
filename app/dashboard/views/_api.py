import httpx
import streamlit as st

API_BASE = "http://localhost:8000"


def _headers():
    token = st.session_state.get("token", "")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def api_get(path: str, timeout: float = 10.0):
    try:
        resp = httpx.get(f"{API_BASE}{path}", headers=_headers(), timeout=timeout)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        return None
    return None


def api_post(path: str, json_data: dict, timeout: float = 10.0):
    try:
        resp = httpx.post(f"{API_BASE}{path}", json=json_data, headers=_headers(), timeout=timeout)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        return None
    return None


def is_authenticated():
    return bool(st.session_state.get("token", ""))
