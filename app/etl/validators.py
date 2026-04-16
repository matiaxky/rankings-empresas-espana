"""
Validadores para registros de empresas antes de entrar al pipeline.

Reglas actuales:
  • CIF: regex español (ej. A12345678, A12345678J) o formato con guion
    (A-12345678). No valida el dígito de control con algoritmo (sería
    estricto de más para el alcance actual del ranking).
  • CIFs falsos: serie 'A-28000xxx' / 'A28000xxx' usada para semilla.
  • Facturación: > 0 y < 500.000 M€.
  • Empleados: > 0 y < 500.000.
"""

from __future__ import annotations

import re
from typing import Any

# Formato canónico (sin guion):  letra + 7 dígitos + (dígito o letra A-J)
_CIF_REGEX_CANONICAL = re.compile(r"^[A-Z]\d{7}[0-9A-J]$")
# Formato con guion: letra + '-' + 8 dígitos (usado por la semilla)
_CIF_REGEX_DASH = re.compile(r"^[A-Z]-\d{8}$")

# Serie de CIFs ficticios en la base inicial
_FAKE_CIF_PATTERNS = (
    re.compile(r"A-?28000\d{3}$", re.IGNORECASE),
)


def normalize_cif(cif: str | None) -> str:
    """Normaliza un CIF: mayúsculas, sin espacios ni guiones."""
    if not cif:
        return ""
    return cif.strip().upper().replace("-", "").replace(" ", "")


def is_valid_cif_format(cif: str | None) -> bool:
    """True si el CIF tiene un formato español aceptable."""
    if not cif:
        return False
    c = cif.strip().upper()
    if _CIF_REGEX_DASH.match(c):
        return True
    c_norm = c.replace("-", "").replace(" ", "")
    return bool(_CIF_REGEX_CANONICAL.match(c_norm))


def is_fake_cif(cif: str | None) -> bool:
    """True si el CIF parece generado artificialmente (serie A-28000xxx)."""
    if not cif:
        return True
    c = cif.strip().upper()
    return any(p.match(c) for p in _FAKE_CIF_PATTERNS)


def validate_facturacion(value: Any) -> bool:
    """Facturación en M€: debe ser numérica, > 0 y < 500.000."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return False
    return 0 < v < 500_000


def validate_empleados(value: Any) -> bool:
    """Empleados: entero > 0 y < 500.000."""
    try:
        v = int(value)
    except (TypeError, ValueError):
        return False
    return 0 < v < 500_000


def validate_record(rec: dict) -> tuple[bool, list[str]]:
    """
    Valida un dict de empresa. Devuelve (ok, errores).

    Reglas mínimas:
      - 'nombre' presente y no vacío.
      - Si trae 'cif', debe ser formato válido.
      - Si trae 'facturacion', debe estar en rango.
      - Si trae 'empleados', debe estar en rango.
    El registro se considera OK aunque carezca de CIF (algunos scrapers
    sólo entregan nombre + facturación). Los errores se devuelven igual
    para logging.
    """
    errors: list[str] = []

    nombre = rec.get("nombre")
    if not nombre or not str(nombre).strip():
        errors.append("nombre vacío")

    cif = rec.get("cif")
    if cif and not is_valid_cif_format(cif):
        errors.append(f"cif con formato inválido: {cif!r}")

    if "facturacion" in rec and rec["facturacion"] is not None:
        if not validate_facturacion(rec["facturacion"]):
            errors.append(f"facturacion fuera de rango: {rec['facturacion']!r}")

    if "empleados" in rec and rec["empleados"] is not None:
        if not validate_empleados(rec["empleados"]):
            errors.append(f"empleados fuera de rango: {rec['empleados']!r}")

    # OK salvo que falte el nombre
    ok = not any(e.startswith("nombre") for e in errors)
    return ok, errors
