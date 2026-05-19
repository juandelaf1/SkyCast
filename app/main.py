from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import router as api_v1
from app.db import init_db


limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(application: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="SkyCast",
    description="Enterprise Climate Intelligence Platform — Monitorización climática en tiempo real con datos oficiales de AEMET",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["root"])
async def root():
    return {
        "nombre": "SkyCast",
        "descripcion": "Enterprise Climate Intelligence Platform",
        "version": "1.0.0",
        "documentacion": "/docs",
        "endpoints": {
            "api": "/api/v1",
            "health": "/api/v1/health",
        },
    }


app.include_router(api_v1, prefix="/api/v1")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "codigo": "INTERNAL_ERROR",
            "mensaje": "Error interno del servidor",
            "detalle": str(exc),
        },
    )