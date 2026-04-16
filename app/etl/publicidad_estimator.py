"""
Estimador de inversión publicitaria a partir de intensidad publicitaria
por sector (ad spend / revenue).

Los coeficientes son órdenes de magnitud razonables basados en datos
públicos de InfoAdex y benchmarks sectoriales. Sólo se aplican cuando:
  - el registro NO tiene 'inversion_publicidad' fiable
  - (publicidad_verificada is None o == "estimación")
  - hay 'facturacion' numérica

El resultado se marca publicidad_verificada = "estimación_sectorial" y
fuente_publicidad = "modelo_sectorial".
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterable

from sqlalchemy.orm import Session

from app import models

logger = logging.getLogger(__name__)


SECTOR_AD_INTENSITY: dict[str, float] = {
    "Gran Consumo": 0.08,
    "Cosmética": 0.12,
    "Farmacéutico": 0.05,
    "Retail": 0.015,
    "Distribución": 0.012,
    "Banca": 0.008,
    "Seguros": 0.007,
    "Telecomunicaciones": 0.025,
    "Energía": 0.002,
    "Construcción": 0.001,
    "Inmobiliaria": 0.005,
    "Automoción": 0.03,
    "Tecnología": 0.04,
    "Turismo": 0.03,
    "Transporte": 0.008,
    "Alimentación": 0.04,
    "Bebidas": 0.06,
    "Medios": 0.05,
    "Moda": 0.05,
    "Logística": 0.003,
    "Sanidad": 0.015,
    "Química": 0.01,
    "Servicios": 0.02,
}

DEFAULT_INTENSITY = 0.015


def _should_estimate(rec) -> bool:
    """
    Determina si un registro (dict o modelo) es candidato a estimación.
    """
    # soporta dicts y objetos ORM indistintamente
    facturacion = rec.get("facturacion") if isinstance(rec, dict) else rec.facturacion
    inversion = rec.get("inversion_publicidad") if isinstance(rec, dict) else rec.inversion_publicidad
    verificada = rec.get("publicidad_verificada") if isinstance(rec, dict) else rec.publicidad_verificada

    if facturacion is None:
        return False

    # Si ya hay dato real, no tocar.
    if inversion is not None and verificada == "real":
        return False

    # Si ya hay dato y no es una estimación, respetar.
    if inversion is not None and verificada not in (None, "estimación", "estimación_sectorial"):
        return False

    return True


def estimate_for_sector(facturacion: float, sector: str | None) -> float:
    """Estimación sencilla: facturacion × intensidad(sector)."""
    intensity = SECTOR_AD_INTENSITY.get(sector or "", DEFAULT_INTENSITY)
    # Redondeo a 1 decimal (M€)
    return round(facturacion * intensity, 1)


def estimate_record(rec: dict) -> dict:
    """
    Aplica la estimación a un dict de empresa (uso en pipeline). Devuelve
    el mismo dict mutado si procede, sino sin cambios.
    """
    if not _should_estimate(rec):
        return rec
    estimated = estimate_for_sector(rec["facturacion"], rec.get("sector"))
    rec["inversion_publicidad"] = estimated
    rec["publicidad_verificada"] = "estimación_sectorial"
    rec["fuente_publicidad"] = "modelo_sectorial"
    return rec


def estimate_all_missing(db: Session) -> dict:
    """
    Itera todas las empresas en BD y rellena inversion_publicidad
    cuando falte, basándose en intensidad sectorial. Devuelve métricas.
    """
    updated = 0
    skipped = 0
    ahora = datetime.utcnow()

    empresas = db.query(models.Empresa).all()
    for emp in empresas:
        if not _should_estimate(emp):
            skipped += 1
            continue
        emp.inversion_publicidad = estimate_for_sector(emp.facturacion, emp.sector)
        emp.publicidad_verificada = "estimación_sectorial"
        emp.fuente_publicidad = "modelo_sectorial"
        emp.fecha_ultima_actualizacion = ahora
        updated += 1

    if updated:
        db.commit()
    logger.info("publicidad_estimator: updated=%d skipped=%d", updated, skipped)
    return {"updated": updated, "skipped": skipped}
