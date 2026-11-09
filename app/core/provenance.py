"""Convención de procedencia (P1)."""
from __future__ import annotations

from enum import Enum


class Procedencia(str, Enum):
    OBSERVADO = "observado"
    ESTIMADO = "estimado"
    SIMULADO = "simulado"
    MIXTO = "mixto"
