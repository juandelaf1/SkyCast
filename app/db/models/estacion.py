from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Estacion(Base):
    __tablename__ = "estaciones"

    id = Column(Integer, primary_key=True, index=True)
    indicativo = Column(String(50), unique=True, nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    provincia = Column(String(100))
    lat = Column(Numeric(10, 6), nullable=False)
    lon = Column(Numeric(10, 6), nullable=False)
    municipio_id = Column(Integer, ForeignKey("municipios.id", ondelete="SET NULL"))
    created_at = Column(TIMESTAMP, server_default=func.now())

    municipio = relationship("Municipio", back_populates="estaciones")
    mediciones = relationship("Medicion", back_populates="estacion")
