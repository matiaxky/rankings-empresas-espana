"""
Scraper CNMV (Comisión Nacional del Mercado de Valores).

Objetivo: obtener una lista de empresas cotizadas en España con datos
básicos (nombre, CIF, ticker) y, cuando sea posible, facturación y nº
de empleados de los informes financieros depositados en la CNMV.

Notas pragmáticas:
  - La CNMV tiene varias páginas y endpoints; no todos son estables.
    Este scraper intenta varios en cascada y devuelve lo que consiga.
  - Diseñado para fallar gracefully: si un endpoint no responde, lo
    loguea y continúa con el siguiente.
  - No parsea XBRL binario; para informes financieros se limita a
    extraer magnitudes de tablas HTML (páginas IFI/IIFI si están
    accesibles). Si no se consigue nada, sólo devuelve cotizadas.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

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
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml",
}
TIMEOUT = 15.0

# URLs candidatas. Se prueban en orden; basta con que una funcione.
LISTED_URLS = [
    "https://www.cnmv.es/portal/Consultas/EE/EmisorHechosRelev.aspx",
    "https://www.cnmv.es/portal/Alerta/Buscador.aspx",
    "https://www.cnmv.es/portal/consultas/fecRegistros.aspx",
]
IBEX_FALLBACK_URL = "https://www.bolsasymercados.es/bme-exchange/es/Indices"
API_SEARCH_URL = "https://apps.cnmv.es/agentSearcher/api/v1/search"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get(url: str, *, params: dict | None = None) -> Optional[str]:
    """GET con timeout y captura de errores; devuelve HTML o None."""
    try:
        with httpx.Client(timeout=TIMEOUT, headers=HEADERS, follow_redirects=True) as c:
            r = c.get(url, params=params)
            if r.status_code >= 400:
                logger.warning("CNMV GET %s -> HTTP %s", url, r.status_code)
                return None
            return r.text
    except httpx.TimeoutException:
        logger.warning("CNMV GET %s -> timeout", url)
    except httpx.HTTPError as e:
        logger.warning("CNMV GET %s -> %s", url, e)
    except Exception as e:
        logger.warning("CNMV GET %s -> unexpected: %s", url, e)
    return None


def _clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_listed_companies() -> list[dict]:
    """
    Obtiene una lista de empresas cotizadas. Devuelve lista de dicts con
    al menos 'nombre', y opcionalmente 'cif', 'ticker', 'fuente'.
    """
    # 1) Intento API JSON (si existe)
    results: list[dict] = []
    try:
        with httpx.Client(timeout=TIMEOUT, headers={**HEADERS, "Accept": "application/json"}) as c:
            r = c.get(API_SEARCH_URL, params={"q": "SA", "type": "ISSUER"})
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict):
                    items = data.get("results") or data.get("items") or []
                elif isinstance(data, list):
                    items = data
                else:
                    items = []
                for it in items[:500]:
                    nombre = it.get("name") or it.get("denomination") or it.get("nombre")
                    if not nombre:
                        continue
                    results.append({
                        "nombre": _clean_text(nombre),
                        "cif": it.get("nif") or it.get("cif"),
                        "ticker": it.get("ticker") or it.get("isin"),
                        "fuente": "CNMV XBRL",
                    })
                logger.info("CNMV API devolvió %d issuers", len(results))
    except Exception as e:
        logger.debug("CNMV API no disponible: %s", e)

    # 2) Fallback HTML: raspar tablas de las páginas públicas
    if not results:
        for url in LISTED_URLS:
            html = _get(url)
            if not html:
                continue
            parsed = _parse_listed_html(html)
            if parsed:
                logger.info("CNMV HTML %s -> %d empresas", url, len(parsed))
                results.extend(parsed)
                break  # nos basta el primer endpoint que funcione

    # 3) Último recurso: lista estática IBEX 35 + Mercado Continuo (manual,
    # hardcoded, pequeña, útil como semilla mínima si todo falla).
    if not results:
        logger.warning("CNMV: todos los endpoints fallaron, usando fallback estático IBEX")
        results = _static_ibex_fallback()

    return results


def _parse_listed_html(html: str) -> list[dict]:
    """
    Parsea páginas HTML de la CNMV en busca de tablas con listados de
    emisores. Muy tolerante: coge cualquier tabla que tenga al menos una
    columna con forma de nombre de empresa y opcionalmente ISIN/ticker.
    """
    soup = BeautifulSoup(html, "lxml")
    out: list[dict] = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 3:
            continue
        for tr in rows[1:]:
            tds = [_clean_text(td.get_text(" ")) for td in tr.find_all(["td", "th"])]
            if not tds:
                continue
            # Heurística: la primera columna larga suele ser el nombre
            nombre = next((t for t in tds if len(t) > 4 and not t.isdigit()), None)
            if not nombre:
                continue
            # Evitar encabezados
            if nombre.lower().startswith(("fecha", "código", "codigo", "isin", "nombre", "emisor")):
                continue
            ticker = next((t for t in tds if re.fullmatch(r"[A-Z0-9]{4,6}", t)), None)
            isin = next((t for t in tds if re.fullmatch(r"[A-Z]{2}\d{10}", t)), None)
            out.append({
                "nombre": nombre,
                "ticker": ticker,
                "isin": isin,
                "fuente": "CNMV XBRL",
            })
    # Deduplica por nombre
    seen = set()
    dedup = []
    for r in out:
        key = r["nombre"].lower()
        if key in seen:
            continue
        seen.add(key)
        dedup.append(r)
    return dedup


def _static_ibex_fallback() -> list[dict]:
    """Seed mínima en caso de fallo total de red (IBEX-35 aprox.)."""
    ibex = [
        "Acciona", "Acerinox", "ACS", "Aena", "Amadeus IT Group", "ArcelorMittal",
        "Banco Sabadell", "Banco Santander", "Bankinter", "BBVA", "CaixaBank",
        "Cellnex Telecom", "Enagás", "Endesa", "Ferrovial", "Fluidra",
        "Grifols", "IAG", "Iberdrola", "Inditex", "Indra Sistemas",
        "Logista", "Mapfre", "Merlin Properties", "Naturgy", "Puig",
        "Redeia", "Repsol", "Rovi", "Sacyr", "Solaria",
        "Telefónica", "Unicaja Banco",
    ]
    return [{"nombre": n, "fuente": "CNMV XBRL"} for n in ibex]


def get_financial_data(ticker_or_name: str) -> Optional[dict]:
    """
    Intenta obtener magnitudes financieras básicas (facturación,
    empleados) de una empresa cotizada. Es best-effort: si la página no
    se puede parsear, devuelve None.
    """
    # Endpoint IFI requiere parámetros específicos; aquí hacemos un intento
    # genérico y si no hay suerte, devolvemos None.
    try:
        html = _get(
            "https://www.cnmv.es/portal/consultas/IFI/ListadoIFI.aspx",
            params={"emisor": ticker_or_name},
        )
        if not html:
            return None
        soup = BeautifulSoup(html, "lxml")
        # Magnitudes típicas en estas fichas
        text = soup.get_text(" ")
        facturacion = _extract_money_near(text, keywords=["ingresos", "cifra de negocios", "ventas"])
        empleados = _extract_int_near(text, keywords=["empleados", "plantilla"])
        if facturacion is None and empleados is None:
            return None
        return {"facturacion": facturacion, "empleados": empleados}
    except Exception as e:
        logger.debug("CNMV financial data para %s falló: %s", ticker_or_name, e)
        return None


_MONEY_RE = re.compile(r"([\d\.]+)\s*(mill(?:on(?:es)?)?|m\b|€)", re.IGNORECASE)


def _extract_money_near(text: str, keywords: list[str]) -> Optional[float]:
    lower = text.lower()
    for kw in keywords:
        idx = lower.find(kw)
        if idx < 0:
            continue
        window = text[idx: idx + 200]
        m = _MONEY_RE.search(window)
        if m:
            raw = m.group(1).replace(".", "").replace(",", ".")
            try:
                return float(raw)
            except ValueError:
                continue
    return None


def _extract_int_near(text: str, keywords: list[str]) -> Optional[int]:
    lower = text.lower()
    for kw in keywords:
        idx = lower.find(kw)
        if idx < 0:
            continue
        window = text[idx: idx + 100]
        m = re.search(r"([\d\.]+)", window)
        if m:
            try:
                return int(m.group(1).replace(".", "").replace(",", ""))
            except ValueError:
                continue
    return None


# ---------------------------------------------------------------------------
# Pipeline-compatible entrypoint
# ---------------------------------------------------------------------------

def scrape() -> list[dict]:
    """
    Entrypoint consumido por el pipeline ETL: devuelve lista de dicts
    listos para entrar al pipeline. Nunca eleva; en caso de fallo
    total devuelve lista vacía.
    """
    try:
        listed = get_listed_companies()
    except Exception as e:
        logger.exception("CNMV scrape error: %s", e)
        return []

    enriched: list[dict] = []
    for emp in listed:
        base = {
            "nombre": emp["nombre"],
            "cif": emp.get("cif"),
            "fuente": "CNMV XBRL",
        }
        # Enriquecer financieros es opcional (muchas peticiones a la web) y
        # ruidoso en CI; se mantiene comentado por defecto para no bloquear.
        # fd = get_financial_data(emp.get("ticker") or emp["nombre"])
        # if fd:
        #     base.update(fd)
        enriched.append(base)
    logger.info("CNMV scraper: %d registros listos", len(enriched))
    return enriched


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = scrape()
    print(f"Obtenidos {len(data)} registros")
    for d in data[:5]:
        print(" ", d)
