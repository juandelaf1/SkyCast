from sqlalchemy import Column, Integer, Numeric, String, UniqueConstraint

from app.db.base import Base


class UmbralAlerta(Base):
    __tablename__ = "umbrales_alerta"

    id = Column(Integer, primary_key=True, index=True)
    variable = Column(String(50), nullable=False, index=True)
    nivel = Column(String(20), nullable=False)
    valor = Column(Numeric(10, 4), nullable=False)
    descripcion = Column(String(200))
    color_hex = Column(String(7))
    icono = Column(String(10))

    __table_args__ = (UniqueConstraint("variable", "nivel", name="uq_umbral_variable_nivel"),)
