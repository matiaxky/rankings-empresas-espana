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

    # Nuevos campos de calidad / trazabilidad
    data_quality_score = Column(Float, default=0.0)  # 0-100
    fuente_publicidad = Column(String, nullable=True)  # fuente específica del dato publicitario
    fecha_ultima_actualizacion = Column(DateTime, nullable=True)

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
            "publicidad_verificada": self.publicidad_verificada,
            "data_quality_score": self.data_quality_score,
            "fuente_publicidad": self.fuente_publicidad,
            "fecha_ultima_actualizacion": (
                self.fecha_ultima_actualizacion.isoformat()
                if self.fecha_ultima_actualizacion else None
            ),
        }
