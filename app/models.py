from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True, nullable=False)
    cif = Column(String, unique=True, index=True)
    sector = Column(String, index=True)
    subsector = Column(String)
    comunidad_autonoma = Column(String, index=True)
    provincia = Column(String)
    facturacion = Column(Float)  # en millones de euros
    año_facturacion = Column(Integer)
    inversion_publicidad = Column(Float, nullable=True)  # en millones de euros
    empleados = Column(Integer, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fuente = Column(String)  # fuente de los datos
    publicidad_verificada = Column(String, default="estimación")  # "real" o "estimación"

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "cif": self.cif,
            "sector": self.sector,
            "subsector": self.subsector,
            "comunidad_autonoma": self.comunidad_autonoma,
            "provincia": self.provincia,
            "facturacion": self.facturacion,
            "año_facturacion": self.año_facturacion,
            "inversion_publicidad": self.inversion_publicidad,
            "empleados": self.empleados,
            "fuente": self.fuente,
        }
