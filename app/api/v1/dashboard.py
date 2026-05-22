import os
import secrets
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx
from pathlib import Path

from app.config.settings import settings

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

SESSION_COOKIE = "skycast_session"
sessions: dict[str, dict] = {}


def get_session_token(request: Request) -> str | None:
    return request.cookies.get(SESSION_COOKIE)


def get_session(request: Request) -> dict | None:
    token = get_session_token(request)
    if token:
        return sessions.get(token)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    s = get_session(request)
    if not s:
        return RedirectResponse(url="/login", status_code=302)

    api_token = s["api_token"]
    headers = {"Authorization": f"Bearer {api_token}"}

    clima = await _api_get("/api/v1/clima?lat=40.4168&lon=-3.7038", headers)
    stats = await _api_get("/api/v1/health/stats", headers)
    health = await _api_get("/api/v1/health", headers)
    geo_mad = await _api_get("/api/v1/geo/Madrid", headers)
    geo_tok = await _api_get("/api/v1/geo/Tokyo", headers)
    alertas = await _api_get("/api/v1/alertas/oficiales", headers)
    registros = await _api_get("/api/v1/registros?page=1&limit=50", headers)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "clima": clima,
            "stats": stats,
            "health": health,
            "geo_mad": geo_mad,
            "geo_tok": geo_tok,
            "alertas": alertas,
            "registros": registros,
            "user_email": s["email"],
        },
    )


@router.get("/comparar", response_class=HTMLResponse)
async def comparar_get(request: Request):
    s = get_session(request)
    if not s:
        return RedirectResponse(url="/login", status_code=302)
    headers = {"Authorization": f"Bearer {s['api_token']}"}
    stats = await _api_get("/api/v1/health/stats", headers)
    health = await _api_get("/api/v1/health", headers)
    return templates.TemplateResponse("comparar.html", {"request": request, "stats": stats, "health": health, "result": None, "error": None, "user_email": s["email"]})


@router.post("/comparar", response_class=HTMLResponse)
async def comparar_post(request: Request, temp: float = Form(...), humedad: float = Form(...),
                       viento: float = Form(...), lluvia: float = Form(...), municipio: str = Form("Madrid")):
    s = get_session(request)
    if not s:
        return RedirectResponse(url="/login", status_code=302)
    headers = {"Authorization": f"Bearer {s['api_token']}"}
    result = await _api_post("/api/v1/comparar", json={"temperatura_manual": temp, "humedad_manual": humedad, "viento_manual": viento, "lluvia_manual": lluvia, "municipio": municipio}, headers=headers)
    stats = await _api_get("/api/v1/health/stats", headers)
    health = await _api_get("/api/v1/health", headers)
    return templates.TemplateResponse("comparar.html", {"request": request, "stats": stats, "health": health, "result": result, "error": None, "user_email": s["email"]})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    s = get_session(request)
    if s:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    r = httpx.post(f"{settings.API_BASE}/api/v1/auth/login", data={"username": email, "password": password}, timeout=10)
    if r.status_code != 200:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Credenciales inválidas"})
    data = r.json()
    session_token = secrets.token_hex(24)
    sessions[session_token] = {"api_token": data["access_token"], "email": email, "user_id": data["user_id"]}
    resp = RedirectResponse(url="/dashboard", status_code=302)
    resp.set_cookie(key=SESSION_COOKIE, value=session_token, httponly=True, secure=False, samesite="lax", max_age=86400)
    return resp


@router.get("/registro", response_class=HTMLResponse)
async def registro_page(request: Request):
    return templates.TemplateResponse("registro.html", {"request": request, "error": None, "success": None})


@router.post("/registro", response_class=HTMLResponse)
async def registro_post(request: Request, email: str = Form(...), password: str = Form(...)):
    r = httpx.post(f"{settings.API_BASE}/api/v1/auth/register", json={"email": email, "password": password}, timeout=10)
    if r.status_code == 200:
        return templates.TemplateResponse("registro.html", {"request": request, "error": None, "success": "Cuenta creada. Ya puedes iniciar sesión."})
    error = r.json().get("detail", "Error al registrar") if r.status_code < 500 else "Error del servidor"
    return templates.TemplateResponse("registro.html", {"request": request, "error": error, "success": None})


@router.get("/logout")
async def logout(request: Request):
    token = get_session_token(request)
    if token and token in sessions:
        del sessions[token]
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie(SESSION_COOKIE)
    return resp


async def _api_get(path: str, headers: dict) -> dict:
    try:
        r = httpx.get(f"{settings.API_BASE}{path}", headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}


async def _api_post(path: str, json: dict, headers: dict) -> dict:
    try:
        r = httpx.post(f"{settings.API_BASE}{path}", json=json, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}