"""
Scraper de rankings de elEconomista.es.

Targets:
  - https://ranking-empresas.eleconomista.es/  (redirige aquí)
  - https://empresas.eleconomista.es/
  - https://www.eleconomista.es/ranking-empresas/

Es best-effort. Devuelve una lista de dicts con el nombre como único
campo obligatorio y los demás si se pueden extraer.
"""

from __future__ import annotations

import logging
import re
from typing import Iterable

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
}
TIMEOUT = 15.0

URLS = [
    "https://ranking-empresas.eleconomista.es/",
    "https://empresas.eleconomista.es/",
    "https://www.eleconomista.es/ranking-empresas/",
]


def _get(url: str) -> str | None:
    try:
        with httpx.Client(timeout=TIMEOUT, headers=HEADERS, follow_redirects=True) as c:
            r = c.get(url)
            if r.status_code >= 400:
                logger.warning("elEconomista GET %s -> HTTP %s", url, r.status_code)
                return None
            return r.text
    except httpx.HTTPError as e:
        logger.warning("elEconomista GET %s -> %s", url, e)
    except Exception as e:
        logger.warning("elEconomista GET %s -> unexpected: %s", url, e)
    return None


def _to_float_m(text: str) -> float | None:
    if not text:
        return None
    t = text.replace("€", "").replace("M", "").replace("\xa0", " ").strip()
    t = re.sub(r"[a-zA-Z\.\s]+$", "", t)
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def _first_index(items: list[str], keywords: Iterable[str]) -> int | None:
    for i, s in enumerate(items):
        for kw in keywords:
            if kw in s:
                return i
    return None


def _parse(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    out: list[dict] = []

    # Estrategia A: tablas con encabezados reconocibles
    for table in soup.find_all("table"):
        headers = [th.get_text(" ", strip=True).lower() for th in table.find_all("th")]
        if not headers:
            continue
        idx_nombre = _first_index(headers, ("empresa", "nombre", "compañía"))
        idx_fact = _first_index(headers, ("ingresos", "facturación", "facturacion", "ventas"))
        idx_sector = _first_index(headers, ("sector", "actividad"))
        idx_ca = _first_index(headers, ("comunidad", "provincia", "localidad"))

        if idx_nombre is None:
            continue
        for tr in table.find_all("tr"):
            tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
            if not tds or len(tds) <= idx_nombre:
                continue
            nombre = tds[idx_nombre].strip()
            if not nombre or len(nombre) < 2:
                continue
            rec: dict = {"nombre": nombre, "fuente": "El Economista"}
            if idx_fact is not None and idx_fact < len(tds):
                v = _to_float_m(tds[idx_fact])
                if v is not None:
                    rec["facturacion"] = v
            if idx_sector is not None and idx_sector < len(tds):
                raw_sector = (tds[idx_sector] or "").strip()
                # elEconomista suele publicar el CNAE como número (ej. "1920").
                # Descartamos códigos puramente numéricos para no sobreescribir
                # un sector textual válido en BD.
                if raw_sector and not raw_sector.isdigit():
                    rec["sector"] = raw_sector
            if idx_ca is not None and idx_ca < len(tds):
                rec["comunidad_autonoma"] = tds[idx_ca] or None
            out.append(rec)

    # Estrategia B: listas li con enlaces a ficha de empresa
    if not out:
        for li in soup.select("ul li a, ol li a"):
            name = li.get_text(" ", strip=True)
            href = li.get("href") or ""
            if not name or len(name) < 3 or len(name) > 80:
                continue
            if "empresa" not in href.lower() and "ranking" not in href.lower():
                continue
            out.append({"nombre": name, "fuente": "El Economista"})

    # Deduplicar por nombre (case-insensitive)
    seen = set()
    dedup = []
    for r in out:
        k = r["nombre"].lower()
        if k in seen:
            continue
        seen.add(k)
        dedup.append(r)
    return dedup


def scrape() -> list[dict]:
    for url in URLS:
        html = _get(url)
        if not html:
            continue
        parsed = _parse(html)
        if parsed:
            logger.info("elEconomista %s -> %d registros", url, len(parsed))
            return parsed
    logger.warning("elEconomista: 0 registros recuperados")
    return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = scrape()
    print(f"Obtenidos {len(data)} registros")
    for d in data[:5]:
        print(" ", d)
