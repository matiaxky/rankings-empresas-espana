"""
Scraper de empresas cotizadas españolas via Wikipedia IBEX 35.

Fuentes:
  1. Wikipedia IBEX 35 (componentes actuales + históricos) — da nombre, sector, sede
  2. Wikipedia "Empresas del IBEX 35" como respaldo

La facturación no está en Wikipedia, pero el pipeline ETL la cruzará con
datos de Wikidata y el seed existente.
"""

from __future__ import annotations

import logging
import re

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; RankingsEmpresasBot/1.0)",
    "Accept-Language": "es-ES,es;q=0.9",
}
TIMEOUT = 20.0

IBEX_URL = "https://es.wikipedia.org/wiki/IBEX_35"

# Mapeado sede → comunidad autónoma
SEDE_TO_CA: dict[str, str] = {
    "madrid": "Comunidad de Madrid",
    "alcobendas": "Comunidad de Madrid",
    "boadilla": "Comunidad de Madrid",
    "tres cantos": "Comunidad de Madrid",
    "getafe": "Comunidad de Madrid",
    "barcelona": "Cataluña",
    "sant cugat": "Cataluña",
    "hospitalet": "Cataluña",
    "bilbao": "País Vasco",
    "vitoria": "País Vasco",
    "san sebastián": "País Vasco",
    "donostia": "País Vasco",
    "pamplona": "Navarra",
    "zaragoza": "Aragón",
    "sevilla": "Andalucía",
    "málaga": "Andalucía",
    "valencia": "Comunitat Valenciana",
    "alicante": "Comunitat Valenciana",
    "a coruña": "Galicia",
    "arteixo": "Galicia",
    "arteijo": "Galicia",
    "vigo": "Galicia",
    "oviedo": "Asturias",
    "santander": "Cantabria",
    "valladolid": "Castilla y León",
    "palma": "Islas Baleares",
}

# Mapeado sector Wikipedia → taxonomía app
SECTOR_MAP: dict[str, str] = {
    "construcción": "Construcción",
    "energías renovables": "Energía",
    "mineral, metales": "Industria",
    "petróleo": "Energía",
    "gas": "Energía",
    "banca": "Banca",
    "bancos": "Banca",
    "seguros": "Seguros",
    "telecomunicaciones": "Telecomunicaciones",
    "tecnología": "Tecnología",
    "inmobiliaria": "Inmobiliaria",
    "turismo": "Turismo",
    "alimentación": "Alimentación",
    "distribución": "Distribución",
    "textil": "Moda",
    "moda": "Moda",
    "farmacéutico": "Farmacéutico",
    "sanidad": "Sanidad",
    "transporte": "Transporte",
    "logística": "Logística",
    "medios": "Medios",
    "química": "Química",
    "automoción": "Automoción",
}


def _get(url: str) -> str | None:
    try:
        with httpx.Client(timeout=TIMEOUT, headers=HEADERS, follow_redirects=True) as c:
            r = c.get(url)
            if r.status_code >= 400:
                logger.warning("Wikipedia GET %s -> HTTP %s", url, r.status_code)
                return None
            return r.text
    except Exception as e:
        logger.warning("Wikipedia GET %s -> %s", url, e)
        return None


def _map_sector(raw: str) -> str:
    s = raw.lower()
    for key, mapped in SECTOR_MAP.items():
        if key in s:
            return mapped
    return "Servicios"


def _map_ca(sede: str) -> str | None:
    s = sede.lower()
    for ciudad, ca in SEDE_TO_CA.items():
        if ciudad in s:
            return ca
    return None


def _parse_ibex_wikipedia(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    results: list[dict] = []
    seen: set[str] = set()

    wikitables = soup.find_all("table", class_="wikitable")
    for table in wikitables:
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if "empresa" not in " ".join(headers):
            continue

        # Detectar índices de columnas relevantes
        idx_empresa = next((i for i, h in enumerate(headers) if "empresa" in h), None)
        idx_sede = next((i for i, h in enumerate(headers) if "sede" in h), None)
        idx_sector = next((i for i, h in enumerate(headers) if "sector" in h), None)

        if idx_empresa is None:
            continue

        for tr in table.find_all("tr")[1:]:
            cells = tr.find_all(["td", "th"])
            if not cells or len(cells) <= idx_empresa:
                continue

            nombre = cells[idx_empresa].get_text(strip=True)
            if not nombre or len(nombre) < 2:
                continue
            # Limpiar referencias de Wikipedia [n]
            nombre = re.sub(r"\[\d+\]", "", nombre).strip()
            if nombre.lower() in seen:
                continue
            seen.add(nombre.lower())

            rec: dict = {"nombre": nombre, "fuente": "Wikipedia IBEX 35"}

            if idx_sede is not None and idx_sede < len(cells):
                sede = cells[idx_sede].get_text(strip=True)
                sede = re.sub(r"\[\d+\]", "", sede).strip()
                ca = _map_ca(sede)
                if ca:
                    rec["comunidad_autonoma"] = ca
                    rec["provincia"] = sede

            if idx_sector is not None and idx_sector < len(cells):
                sector_raw = cells[idx_sector].get_text(strip=True)
                sector_raw = re.sub(r"\[\d+\]", "", sector_raw).strip()
                if sector_raw:
                    rec["sector"] = _map_sector(sector_raw)

            results.append(rec)

    return results


def scrape() -> list[dict]:
    html = _get(IBEX_URL)
    if not html:
        logger.warning("Wikipedia IBEX 35: no se pudo obtener la página")
        return []

    results = _parse_ibex_wikipedia(html)
    logger.info("Wikipedia IBEX 35: %d empresas", len(results))
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = scrape()
    print(f"Total: {len(data)}")
    for d in data[:5]:
        print(" ", d)
