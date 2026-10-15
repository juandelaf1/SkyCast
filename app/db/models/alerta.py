from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Alerta(Base):
    __tablename__ = "alertas"

    id = Column(Integer, primary_key=True, index=True)
    medicion_id = Column(Integer, ForeignKey("mediciones.id", ondelete="CASCADE"), nullable=False, index=True)
    umbral_id = Column(Integer, ForeignKey("umbrales_alerta.id", ondelete="SET NULL"))
    tipo = Column(String(50), index=True)
    nivel = Column(String(50), index=True)
    mensaje = Column(Text)
    valor_detectado = Column(Numeric(10, 4))
    umbral = Column(Numeric(10, 4))
    created_at = Column(TIMESTAMP, server_default=func.now())

    medicion = relationship("Medicion", back_populates="alertas")
    umbral = relationship("UmbralAlerta")
