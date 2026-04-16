"""
Pipeline ETL: recibe una lista de dicts con datos de empresa y los
upserta en la BD.

Flujo por registro:
  1. Validar con validators.py (nombre obligatorio; el resto se avisa).
  2. Buscar si ya existe (por CIF normalizado; si no, fuzzy por nombre
     dentro de la misma comunidad_autonoma).
  3. Si existe -> merge según source_priority; si no -> insert.
  4. Calcular y guardar data_quality_score (rúbrica abajo).
  5. Actualizar fecha_ultima_actualizacion = now().

Rúbrica data_quality_score (máximo 100):
  +20  CIF real (pasa regex y NO es fake A-28000xxx)
  +20  facturacion válida con año_facturacion >= 2025
  +20  empleados informado
  +20  comunidad_autonoma informada
  +10  inversion_publicidad informada
  +10  publicidad_verificada == "real"
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterable, Sequence

from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal

from . import deduplicator
from .source_priority import priority_of
from .validators import (
    is_fake_cif,
    is_valid_cif_format,
    normalize_cif,
    validate_record,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Quality score
# ---------------------------------------------------------------------------

def compute_quality_score(rec: dict) -> float:
    score = 0.0
    cif = rec.get("cif")
    if cif and is_valid_cif_format(cif) and not is_fake_cif(cif):
        score += 20
    facturacion = rec.get("facturacion")
    año = rec.get("año_facturacion")
    if facturacion and año and int(año) >= 2025:
        score += 20
    if rec.get("empleados"):
        score += 20
    if rec.get("comunidad_autonoma"):
        score += 20
    if rec.get("inversion_publicidad") is not None:
        score += 10
    if rec.get("publicidad_verificada") == "real":
        score += 10
    return round(float(score), 1)


# ---------------------------------------------------------------------------
# Find existing empresa
# ---------------------------------------------------------------------------

def _find_existing(db: Session, rec: dict) -> models.Empresa | None:
    """
    Busca una empresa existente en BD que coincida con `rec`.
    1) CIF normalizado.
    2) Fuzzy por nombre dentro de misma comunidad_autonoma.
    """
    cif_norm = normalize_cif(rec.get("cif"))
    if cif_norm:
        candidates = db.query(models.Empresa).filter(
            models.Empresa.cif.isnot(None)
        ).all()
        for emp in candidates:
            if normalize_cif(emp.cif) == cif_norm:
                return emp

    # Fuzzy match por nombre
    nombre = rec.get("nombre")
    if not nombre:
        return None

    q = db.query(models.Empresa)
    ca = rec.get("comunidad_autonoma")
    if ca:
        # no filtramos en SQL para poder comparar también con registros
        # cuya CA esté vacía (la deduplicadora lo permite)
        pass
    empresas = q.all()

    rec_like = {"nombre": nombre, "comunidad_autonoma": ca, "cif": rec.get("cif")}
    for emp in empresas:
        emp_like = {
            "nombre": emp.nombre,
            "comunidad_autonoma": emp.comunidad_autonoma,
            "cif": emp.cif,
        }
        if deduplicator.same_company(rec_like, emp_like):
            return emp
    return None


# ---------------------------------------------------------------------------
# Apply a merged dict to a model instance
# ---------------------------------------------------------------------------

_APPLIABLE_FIELDS = (
    "nombre", "cif", "sector", "subsector",
    "comunidad_autonoma", "provincia",
    "facturacion", "año_facturacion",
    "inversion_publicidad", "empleados",
    "fuente", "publicidad_verificada",
    "fuente_publicidad",
)


def _empresa_to_dict(emp: models.Empresa) -> dict:
    return {
        "nombre": emp.nombre,
        "cif": emp.cif,
        "sector": emp.sector,
        "subsector": emp.subsector,
        "comunidad_autonoma": emp.comunidad_autonoma,
        "provincia": emp.provincia,
        "facturacion": emp.facturacion,
        "año_facturacion": emp.año_facturacion,
        "inversion_publicidad": emp.inversion_publicidad,
        "empleados": emp.empleados,
        "fuente": emp.fuente,
        "publicidad_verificada": emp.publicidad_verificada,
        "fuente_publicidad": emp.fuente_publicidad,
    }


def _apply_dict(emp: models.Empresa, data: dict) -> None:
    for f in _APPLIABLE_FIELDS:
        if f in data:
            setattr(emp, f, data[f])


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------

def run(
    records: Iterable[dict],
    db: Session | None = None,
    dedupe_inputs: bool = True,
) -> dict:
    """
    Ejecuta el pipeline completo sobre una lista de dicts.

    Es idempotente: si los mismos datos se vuelven a pasar, no cambia nada
    (el score vuelve a calcularse con el mismo resultado).
    """
    owns_session = db is None
    db = db or SessionLocal()

    stats = {
        "total_input": 0,
        "invalid": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "errors": [],
    }

    try:
        records = list(records)
        stats["total_input"] = len(records)

        if dedupe_inputs:
            records = deduplicator.deduplicate(records)

        ahora = datetime.utcnow()

        for rec in records:
            ok, errors = validate_record(rec)
            if not ok:
                stats["invalid"] += 1
                stats["errors"].extend(errors[:3])
                continue
            if errors:
                logger.debug("validator warnings for %s: %s", rec.get("nombre"), errors)

            existing = _find_existing(db, rec)

            if existing is None:
                # Insert
                score = compute_quality_score(rec)
                new = models.Empresa(
                    nombre=rec.get("nombre"),
                    cif=rec.get("cif"),
                    sector=rec.get("sector"),
                    subsector=rec.get("subsector"),
                    comunidad_autonoma=rec.get("comunidad_autonoma"),
                    provincia=rec.get("provincia"),
                    facturacion=rec.get("facturacion"),
                    año_facturacion=rec.get("año_facturacion"),
                    inversion_publicidad=rec.get("inversion_publicidad"),
                    empleados=rec.get("empleados"),
                    fuente=rec.get("fuente"),
                    publicidad_verificada=rec.get("publicidad_verificada") or "estimación",
                    fuente_publicidad=rec.get("fuente_publicidad"),
                    data_quality_score=score,
                    fecha_ultima_actualizacion=ahora,
                )
                db.add(new)
                try:
                    db.flush()
                    stats["inserted"] += 1
                except Exception as e:  # p.ej. UNIQUE violation en carrera
                    db.rollback()
                    logger.warning("insert falló para %s: %s", rec.get("nombre"), e)
                    stats["errors"].append(f"insert_fail:{rec.get('nombre')}")
                    stats["skipped"] += 1
            else:
                existing_dict = _empresa_to_dict(existing)
                merged = deduplicator.merge(existing_dict, rec)

                changed = merged != existing_dict
                _apply_dict(existing, merged)
                existing.data_quality_score = compute_quality_score(merged)
                existing.fecha_ultima_actualizacion = ahora

                if changed:
                    stats["updated"] += 1
                else:
                    # mismo contenido → recomputamos score+timestamp (idempotente)
                    stats["skipped"] += 1

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        if owns_session:
            db.close()

    return stats
