"""
Deduplicación de registros de empresas.

Estrategia:
  1. Prioridad absoluta: CIF normalizado (sin guiones, sin espacios,
     uppercase). Dos registros con el mismo CIF = misma empresa.
  2. Fallback: fuzzy matching del nombre con rapidfuzz (WRatio, threshold
     85) restringido a la misma comunidad_autonoma cuando esté disponible.
     Si una de las dos partes no tiene CA, se permite igualmente.

Merge:
  Gana el registro de mayor SOURCE_PRIORITY. Los campos vacíos del
  ganador se rellenan con los del perdedor.
"""

from __future__ import annotations

import logging
from typing import Iterable, Optional

from rapidfuzz import fuzz

from .source_priority import priority_of
from .validators import normalize_cif

logger = logging.getLogger(__name__)

FUZZY_THRESHOLD = 85


# ---------------------------------------------------------------------------
# Key helpers
# ---------------------------------------------------------------------------

def _name_key(nombre: str | None) -> str:
    """Clave de normalización para nombres (sólo para comparación fuzzy)."""
    if not nombre:
        return ""
    return (
        nombre.strip()
              .lower()
              .replace(",", "")
              .replace(".", "")
              .replace("s.a.", "")
              .replace("s.l.", "")
              .replace("  ", " ")
    )


def same_company(a: dict, b: dict, threshold: int = FUZZY_THRESHOLD) -> bool:
    """True si a y b parecen ser la misma empresa."""
    cif_a = normalize_cif(a.get("cif"))
    cif_b = normalize_cif(b.get("cif"))
    if cif_a and cif_b and cif_a == cif_b:
        return True

    name_a = _name_key(a.get("nombre"))
    name_b = _name_key(b.get("nombre"))
    if not name_a or not name_b:
        return False

    ca_a = (a.get("comunidad_autonoma") or "").strip().lower()
    ca_b = (b.get("comunidad_autonoma") or "").strip().lower()
    if ca_a and ca_b and ca_a != ca_b:
        return False

    score = fuzz.WRatio(name_a, name_b)
    return score >= threshold


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

_MERGE_FIELDS = (
    "nombre", "cif", "sector", "subsector",
    "comunidad_autonoma", "provincia",
    "facturacion", "año_facturacion",
    "inversion_publicidad", "empleados",
    "fuente", "publicidad_verificada",
    "fuente_publicidad",
)


def _is_empty(v) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


def merge(primary: dict, secondary: dict) -> dict:
    """
    Fusiona `primary` (ganador) con `secondary` (perdedor).
    El ganador se decide por prioridad de fuente; si empatan, gana primary.

    Reglas específicas anti-corrupción:
      - 'sector' numérico (CNAE) nunca sobreescribe un sector textual
        existente; si primary tiene texto y secondary trae número, se
        descarta secondary.sector en el fill.
    """
    p_pri = priority_of(primary.get("fuente"))
    s_pri = priority_of(secondary.get("fuente"))

    if s_pri > p_pri:
        primary, secondary = secondary, primary

    result = dict(primary)
    for f in _MERGE_FIELDS:
        cur = result.get(f)
        alt = secondary.get(f)
        if _is_empty(cur) and not _is_empty(alt):
            # Evitar propagar CNAEs numéricos como "sector"
            if f == "sector" and isinstance(alt, str) and alt.strip().isdigit():
                continue
            result[f] = alt
    return result


# ---------------------------------------------------------------------------
# Batch deduplication for in-memory lists
# ---------------------------------------------------------------------------

def deduplicate(records: Iterable[dict]) -> list[dict]:
    """
    Deduplica una iterable de registros en memoria. Hace un pase O(n·k)
    donde k es el tamaño del bucket (pequeño en la práctica).
    """
    buckets: list[dict] = []
    for rec in records:
        matched: Optional[int] = None
        for i, existing in enumerate(buckets):
            if same_company(rec, existing):
                matched = i
                break
        if matched is None:
            buckets.append(dict(rec))
        else:
            buckets[matched] = merge(buckets[matched], rec)
    return buckets
