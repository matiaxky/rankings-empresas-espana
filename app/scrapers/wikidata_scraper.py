"""
Scraper de empresas españolas via Wikidata SPARQL.
Obtiene empresas con datos de ingresos, empleados, sector y sede.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
TIMEOUT = 30.0

# Mapeado de sectores Wikidata → taxonomía de la app
SECTOR_MAP: dict[str, str] = {
    "servicios financieros": "Banca",
    "banca": "Banca",
    "banco": "Banca",
    "seguro": "Seguros",
    "seguros": "Seguros",
    "generación de energía eléctrica": "Energía",
    "empresa de electricidad": "Energía",
    "petróleo": "Energía",
    "gas natural": "Energía",
    "energía": "Energía",
    "energías renovables": "Energía",
    "petroquímica": "Química",
    "química": "Química",
    "industria textil": "Moda",
    "moda": "Moda",
    "industria del vestido": "Moda",
    "minorista": "Retail",
    "comercio minorista": "Retail",
    "supermercado": "Distribución",
    "distribución": "Distribución",
    "telecomunicaciones": "Telecomunicaciones",
    "telefonía": "Telecomunicaciones",
    "tecnología de la información": "Tecnología",
    "tecnología": "Tecnología",
    "software": "Tecnología",
    "construcción": "Construcción",
    "ingeniería": "Construcción",
    "infraestructura": "Construcción",
    "inmobiliaria": "Inmobiliaria",
    "bienes raíces": "Inmobiliaria",
    "alimentación": "Alimentación",
    "industria alimentaria": "Alimentación",
    "bebidas": "Bebidas",
    "cerveza": "Bebidas",
    "vino": "Bebidas",
    "automoción": "Automoción",
    "automóvil": "Automoción",
    "fabricación de automóviles": "Automoción",
    "transporte": "Transporte",
    "logística": "Logística",
    "aerolínea": "Transporte",
    "aviación": "Transporte",
    "turismo": "Turismo",
    "hotelería": "Turismo",
    "hotel": "Turismo",
    "farmacéutica": "Farmacéutico",
    "farmacéutico": "Farmacéutico",
    "sanidad": "Sanidad",
    "salud": "Sanidad",
    "medios de comunicación": "Medios",
    "medios": "Medios",
    "prensa": "Medios",
    "televisión": "Medios",
    "mineral, metales": "Industria",
    "siderurgia": "Industria",
    "acero": "Industria",
    "minería": "Industria",
}

# Mapeado ciudad/provincia → comunidad autónoma
CIUDAD_TO_CA: dict[str, str] = {
    "madrid": "Comunidad de Madrid",
    "barcelona": "Cataluña",
    "bilbao": "País Vasco",
    "vitoria": "País Vasco",
    "san sebastián": "País Vasco",
    "donostia": "País Vasco",
    "pamplona": "Navarra",
    "zaragoza": "Aragón",
    "sevilla": "Andalucía",
    "málaga": "Andalucía",
    "granada": "Andalucía",
    "córdoba": "Andalucía",
    "valencia": "Comunitat Valenciana",
    "alicante": "Comunitat Valenciana",
    "la coruña": "Galicia",
    "a coruña": "Galicia",
    "arteijo": "Galicia",
    "arteixo": "Galicia",
    "vigo": "Galicia",
    "oviedo": "Asturias",
    "gijón": "Asturias",
    "santander": "Cantabria",
    "valladolid": "Castilla y León",
    "burgos": "Castilla y León",
    "salamanca": "Castilla y León",
    "toledo": "Castilla-La Mancha",
    "albacete": "Castilla-La Mancha",
    "mérida": "Extremadura",
    "badajoz": "Extremadura",
    "palma": "Islas Baleares",
    "palma de mallorca": "Islas Baleares",
    "las palmas": "Canarias",
    "santa cruz de tenerife": "Canarias",
    "murcia": "Región de Murcia",
    "logroño": "La Rioja",
    "alcobendas": "Comunidad de Madrid",
    "ciudad bbva": "Comunidad de Madrid",
    "boadilla del monte": "Comunidad de Madrid",
}

# Query única: empresas españolas con ingresos, empleados, sector y sede
# Usa MAX para evitar duplicados por múltiples valores de sector/ingresos
QUERY = """
SELECT ?empresa ?empresaLabel
       (MAX(?ingresos) AS ?max_ingresos)
       (MAX(?empleados) AS ?max_empleados)
       (SAMPLE(?sectorLabel) AS ?sector_sample)
       (SAMPLE(?sedeLabel) AS ?sede_sample)
WHERE {
  ?empresa wdt:P17 wd:Q29.
  ?empresa wdt:P31 wd:Q4830453.
  ?empresa wdt:P2295 ?ingresos.
  FILTER NOT EXISTS { ?empresa wdt:P576 ?disolucion. }
  OPTIONAL { ?empresa wdt:P1128 ?empleados. }
  OPTIONAL {
    ?empresa wdt:P452 ?sector.
    ?sector rdfs:label ?sectorLabel.
    FILTER(LANG(?sectorLabel) = "es")
  }
  OPTIONAL {
    ?empresa wdt:P159 ?sede.
    ?sede rdfs:label ?sedeLabel.
    FILTER(LANG(?sedeLabel) = "es")
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". }
}
GROUP BY ?empresa ?empresaLabel
ORDER BY DESC(?max_ingresos)
LIMIT 250
"""


def _sparql(query: str) -> list[dict[str, Any]]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "RankingsEmpresasEspana/1.0 (educational project)",
    }
    try:
        with httpx.Client(timeout=TIMEOUT) as c:
            r = c.get(SPARQL_ENDPOINT, params={"query": query}, headers=headers)
            r.raise_for_status()
            return r.json().get("results", {}).get("bindings", [])
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            logger.warning("Wikidata rate-limit, esperando 10s...")
            time.sleep(10)
        logger.error("Wikidata SPARQL error: %s", e)
        return []
    except Exception as e:
        logger.error("Wikidata SPARQL error: %s", e)
        return []


def _map_sector(sector_raw: str) -> str:
    s = sector_raw.lower().strip()
    for key, mapped in SECTOR_MAP.items():
        if key in s:
            return mapped
    return "Servicios"


def _map_comunidad(sede_raw: str) -> str | None:
    s = sede_raw.lower().strip()
    for ciudad, ca in CIUDAD_TO_CA.items():
        if ciudad in s:
            return ca
    return None


def scrape() -> list[dict]:
    logger.info("Wikidata: ejecutando query de empresas...")
    bindings = _sparql(QUERY)

    results: list[dict] = []
    for b in bindings:
        nombre = b.get("empresaLabel", {}).get("value", "")
        if not nombre or nombre.startswith("Q"):
            continue

        ingresos_raw = b.get("max_ingresos", {}).get("value")
        empleados_raw = b.get("max_empleados", {}).get("value")
        sector_raw = b.get("sector_sample", {}).get("value", "")
        sede_raw = b.get("sede_sample", {}).get("value", "")

        facturacion = None
        if ingresos_raw:
            try:
                facturacion = round(float(ingresos_raw) / 1_000_000, 2)
            except ValueError:
                pass

        empleados = None
        if empleados_raw:
            try:
                empleados = int(float(empleados_raw))
            except ValueError:
                pass

        results.append({
            "nombre": nombre,
            "sector": _map_sector(sector_raw) if sector_raw else None,
            "comunidad_autonoma": _map_comunidad(sede_raw) if sede_raw else None,
            "empleados": empleados,
            "facturacion": facturacion,
            "fuente": "Wikidata",
            "año_facturacion": 2024,
        })

    logger.info("Wikidata scraper: %d empresas", len(results))
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = scrape()
    print(f"Total: {len(data)}")
    for d in data[:10]:
        print(" ", d)
