import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.jwt_auth import get_current_user
from app.db import get_db
from app.db.models import Medicion, Estacion
from app.core.utils import haversine

logger = logging.getLogger(__name__)
router = APIRouter()

class ValidarReclamoRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitud del evento")
    lon: float = Field(..., ge=-180, le=180, description="Longitud del evento")
    fecha_hora: str = Field(..., description="Fecha y hora del evento en formato ISO (YYYY-MM-DDTHH:MM:SS)")
    tipo_riesgo: str = Field(..., description="Tipo de riesgo climático (helada, granizo, viento_extremo, lluvia_intensa, etc.)")
    poliza_id: Optional[str] = Field(None, description="ID de póliza para trazabilidad")

class EvidenciaEstacion(BaseModel):
    estacion_id: str
    nombre: str
    distancia_km: float
    valor_registrado: float
    umbral_riesgo: float
    cumple_condicion: bool

class ValidarReclamoResponse(BaseModel):
    valido: bool
    confianza: int  # 0-100
    evidencia: List[EvidenciaEstacion]
    nota: str
    poliza_id: Optional[str] = None
    fecha_procesamiento: datetime

# Umbrales de riesgo por tipo (en unidades estándar)
UMBRALES_RIESGO = {
    "helada": {"variable": "temperatura", "comparador": "<=", "valor": 0.0, "unidad": "°C"},
    "granizo": {"variable": "lluvia", "comparador": ">", "valor": 5.0, "unidad": "mm"},  # Simplificado: granizo como lluvia intensa
    "viento_extremo": {"variable": "viento", "comparador": ">", "valor": 50.0, "unidad": "km/h"},
    "lluvia_intensa": {"variable": "lluvia", "comparador": ">", "valor": 20.0, "unidad": "mm/h"},
    "calor_extremo": {"variable": "temperatura", "comparador": ">=", "valor": 35.0, "unidad": "°C"},
}

@router.post("")
async def validar_reclamo(
    reclamo: ValidarReclamoRequest,
    db: Session = Depends(get_db),
    usuario: dict = Depends(get_current_user)
):
    """
    Valida si un reclamo por daño climático está respaldado por datos meteorológicos confiables
    en la ubicación y hora especificadas.
    """
    try:
        # Parsear fecha_hora
        try:
            fecha_evento = datetime.fromisoformat(reclamo.fecha_hora.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de fecha_hora inválido. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )
        
        # Definir ventana de tiempo: 1 hora antes y después del evento
        ventana_inicio = fecha_evento - timedelta(hours=1)
        ventana_fin = fecha_evento + timedelta(hours=1)
        
        # Obtener umbrales para el tipo de riesgo
        if reclamo.tipo_riesgo not in UMBRALES_RIESGO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de riesgo '{reclamo.tipo_riesgo}' no soportado. Tipos válidos: {list(UMBRALES_RIESGO.keys())}"
            )
        
        umbral_info = UMBRALES_RIESGO[reclamo.tipo_riesgo]
        variable = umbral_info["variable"]
        comparador = umbral_info["comparador"]
        umbral_valor = umbral_info["valor"]
        
        # Mapear variable de riesgo a columna en tabla medicion
        variable_map = {
            "temperatura": "temperatura",
            "humedad": "humedad", 
            "viento": "viento",
            "lluvia": "lluvia",
            "presion": "presion"
        }
        
        if variable not in variable_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Variable '{variable}' no soportada para validación"
            )
        
        columna_variable = variable_map[variable]
        
        # Consultar mediciones en la ventana de tiempo alrededor de las coordenadas
        # Primero obtener estaciones cercanas (por ejemplo, dentro de 20km)
        estaciones_cercanas = db.query(Estacion).all()
        
        evidencias = []
        contador_cumple = 0
        total_evaluadas = 0
        
        for estacion in estaciones_cercanas:
            # Calcular distancia
            dist = haversine(reclamo.lat, reclamo.lon, estacion.lat, estacion.lon)
            
            # Considerar estaciones dentro de 15km (configurable)
            if dist > 15.0:
                continue
                
            # Obtener mediciones de esta estación en la ventana de tiempo
            mediciones = db.query(Medicion).filter(
                Medicion.estacion_id == estacion.id,
                Medicion.fecha >= ventana_inicio,
                Medicion.fecha <= ventana_fin
            ).all()
            
            if not mediciones:
                continue
                
            total_evaluadas += 1
            
            # Obtener el valor más representativo (promedio, máximo o mínimo según el tipo de riesgo)
            valores = [getattr(m, columna_variable) for m in mediciones if getattr(m, columna_variable) is not None]
            if not valores:
                continue
                
            # Según el tipo de riesgo, usar el valor más relevante
            if comparador in [">=", ">"]:  # Para riesgos de exceso (viento, lluvia, calor)
                valor_representativo = max(valores)
            else:  # Para riesgos de déficit (helada)
                valor_representativo = min(valores)
            
            # Verificar si cumple la condición de riesgo
            if comparador == ">=":
                cumple = valor_representativo >= umbral_valor
            elif comparador == "<=":
                cumple = valor_representativo <= umbral_valor
            elif comparador == ">":
                cumple = valor_representativo > umbral_valor
            elif comparador == "<":
                cumple = valor_representativo < umbral_valor
            else:
                cumple = False
            
            if cumple:
                contador_cumple += 1
            
            evidencias.append(EvidenciaEstacion(
                estacion_id=estacion.id,
                nombre=estacion.nombre,
                distancia_km=round(dist, 2),
                valor_registrado=round(valor_representativo, 2),
                umbral_riesgo=round(umbral_valor, 2),
                cumple_condicion=cumple
            ))
        
        # Ordenar evidencias por distancia (más cercanas primero)
        evidencias.sort(key=lambda x: x.distancia_km)
        
        # Calcular confianza basada en:
        # 1. Proporción de estaciones que confirman el evento
        # 2. Número total de estaciones evaluadas (más estaciones = más confianza)
        # 3. Consistencia espacial (estaciones cercanas mostrando el mismo fenómeno)
        if total_evaluadas == 0:
            confianza = 0
            valido = False
            nota = "No se encontraron estaciones meteorológicas con datos en el rango de tiempo especificado"
        else:
            proporcion_cumple = contador_cumple / total_evaluadas
            # Factor de cantidad de estaciones (más estaciones = más confianza hasta cierto punto)
            factor_cantidad = min(total_evaluadas / 5.0, 1.0)  # Máximo a 5 estaciones
            # Factor de consistencia (evitar falsos positivos por una sola estación extraña)
            factor_consistencia = proporcion_cumple  # Ya está entre 0 y 1
            
            confianza = int((proporcion_cumple * 0.6 + factor_cantidad * 0.2 + factor_consistencia * 0.2) * 100)
            confianza = max(0, min(100, confianza))  # Asegurar rango 0-100
            
            # Lógica de validación: considerar válido si al menos el 40% de las estaciones cercanas confirman
            # Y hay al menos 2 estaciones que confirman (evitar falsos positivos con una sola estación)
            valido = (proporcion_cumple >= 0.4) and (contador_cumple >= 2)
            
            if valido:
                nota = f"{contador_cumple} de {total_evaluadas} estaciones cercanas confirmaron condiciones de {reclamo.tipo_riesgo} durante la ventana de tiempo especificada"
            else:
                if total_evaluadas == 0:
                    nota = "No se encontraron datos meteorológicos suficientes para validar el reclamo"
                elif contador_cumple == 0:
                    nota = f"Ninguna de las {total_evaluadas} estaciones cercanas confirmó condiciones de {reclamo.tipo_riesgo}"
                else:
                    nota = f"Solo {contador_cumple} de {total_evaluadas} estaciones cercanas confirmaron condiciones de {reclamo.tipo_riesgo} (se requiere al menos 40%)"
        
        # Limitar evidencias a las 5 más cercanas para la respuesta
        evidencias_limitadas = evidencias[:5]
        
        return ValidarReclamoResponse(
            valido=valido,
            confianza=confianza,
            evidencia=evidencias_limitadas,
            nota=nota,
            poliza_id=reclamo.poliza_id,
            fecha_procesamiento=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en validar_reclamo: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor durante la validación del reclamo"
        )
