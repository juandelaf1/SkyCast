from app.db.base import Base
from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class FuenteDato(Base):
    __tablename__ = "fuentes_dato"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    nombre = Column(String(100))
    url = Column(String(255))
    cobertura = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())

    mediciones = relationship("Medicion", back_populates="fuente")