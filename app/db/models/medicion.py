from app.db.base import Base
from sqlalchemy import Column, Integer, Numeric, ForeignKey, TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Medicion(Base):
    __tablename__ = "mediciones"

    id = Column(Integer, primary_key=True, index=True)
    estacion_id = Column(Integer, ForeignKey("estaciones.id", ondelete="CASCADE"), nullable=False, index=True)
    fecha = Column(TIMESTAMP, nullable=False, index=True)
    temperatura = Column(Numeric(6, 2))
    humedad = Column(Numeric(5, 2))
    viento = Column(Numeric(6, 2))
    lluvia = Column(Numeric(6, 2))
    presion = Column(Numeric(7, 2))
    fuente_id = Column(Integer, ForeignKey("fuentes_dato.id", ondelete="SET NULL"), index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (UniqueConstraint("estacion_id", "fecha", name="uq_medicion_estacion_fecha"),)

    estacion = relationship("Estacion", back_populates="mediciones")
    fuente = relationship("FuenteDato", back_populates="mediciones")
    alertas = relationship("Alerta", back_populates="medicion", cascade="all, delete-orphan")