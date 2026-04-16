"""
Prioridad relativa de las fuentes de datos.

El pipeline utiliza estos valores para decidir qué dato "gana" al hacer
merge entre dos registros de la misma empresa procedentes de fuentes
distintas. Mayor valor = más fiable.
"""

from __future__ import annotations

SOURCE_PRIORITY: dict[str, int] = {
    "CNMV XBRL": 100,
    "Informe Anual PDF": 90,
    "Expansión Top 500": 70,
    "El Economista": 60,
    "Informa D&B": 80,
    "estimación_sectorial": 10,
    "seed": 5,
}


def priority_of(source: str | None) -> int:
    """
    Devuelve la prioridad numérica de una fuente. Si la fuente no está
    registrada explícitamente, intenta un match prefijo razonable (p.ej.
    'Informe Anual 2024' cae en 'Informe Anual PDF'). En último caso, 0.
    """
    if not source:
        return 0
    if source in SOURCE_PRIORITY:
        return SOURCE_PRIORITY[source]

    s = source.lower()
    if "cnmv" in s:
        return SOURCE_PRIORITY["CNMV XBRL"]
    if "informe anual" in s or "informe_anual" in s or "annual report" in s:
        return SOURCE_PRIORITY["Informe Anual PDF"]
    if "expansión" in s or "expansion" in s:
        return SOURCE_PRIORITY["Expansión Top 500"]
    if "economista" in s:
        return SOURCE_PRIORITY["El Economista"]
    if "informa" in s or "d&b" in s or "d and b" in s:
        return SOURCE_PRIORITY["Informa D&B"]
    if "estim" in s:
        return SOURCE_PRIORITY["estimación_sectorial"]
    if "seed" in s:
        return SOURCE_PRIORITY["seed"]
    return 0
