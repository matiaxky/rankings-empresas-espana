from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class EmpresaBase(BaseModel):
    nombre: str
    cif: str
    sector: Optional[str] = None
    subsector: Optional[str] = None
    comunidad_autonoma: Optional[str] = None
    provincia: Optional[str] = None
    facturacion: Optional[float] = None
    año_facturacion: Optional[int] = None
    inversion_publicidad: Optional[float] = None
    empleados: Optional[int] = None
    fuente: Optional[str] = None
    publicidad_verificada: Optional[str] = "estimación"  # "real" o "estimación"


class EmpresaCreate(EmpresaBase):
    pass


class EmpresaResponse(EmpresaBase):
    id: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True


class RankingResponse(BaseModel):
    rank: int
    empresa: EmpresaResponse
    metrica: float
    tipo_ranking: str  # "facturacion" o "inversion_publicidad"


class SectorStats(BaseModel):
    sector: str
    num_empresas: int
    facturacion_total: float
    facturacion_media: float
    top_empresa: str


class ComunidadStats(BaseModel):
    comunidad: str
    num_empresas: int
    facturacion_total: float
    porcentaje_nacional: float


class StatsResponse(BaseModel):
    total_empresas: int
    total_sectores: int
    total_comunidades: int
    facturacion_total: float
    año_facturacion_min: Optional[int] = None
    año_facturacion_max: Optional[int] = None


class ReloadResponse(BaseModel):
    status: str
    empresas_insertadas: int
    message: str
