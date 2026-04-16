"""
Scraper para el BORME (Boletín Oficial del Registro Mercantil)
Extrae datos de empresas del BORME para obtener información actualizada.
"""

import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BORMEScraper:
    """Scraper para extraer datos del BORME"""

    BASE_URL = "https://www.boe.es/diario_borme/"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    async def fetch_url(self, url: str) -> Optional[str]:
        """Hacer petición HTTP con manejo de errores"""
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return response.text
                logger.warning(f"Error {response.status_code} al obtener {url}")
        except httpx.RequestError as e:
            logger.error(f"Error de red en {url}: {e}")
        except Exception as e:
            logger.error(f"Error inesperado en {url}: {e}")
        return None

    async def fetch_empresa(self, cif: str) -> Optional[Dict]:
        """
        Buscar una empresa por CIF en el BORME
        """
        logger.info(f"Buscando empresa con CIF: {cif}")

        url = f"{self.BASE_URL}?cif={cif}"
        html = await self.fetch_url(url)
        if html:
            return self.parse_borme_entry(html)
        return None

    async def get_empresas_por_sector(self, sector: str, limit: int = 50) -> List[Dict]:
        """
        Obtener empresas de un sector específico buscando en el BORME
        """
        logger.info(f"Obteniendo empresas del sector: {sector}")

        # Buscar en el BORME por sector
        url = f"{self.BASE_URL}?sector={sector}"
        html = await self.fetch_url(url)
        if html:
            return self._parse_busqueda_sector(html, sector, limit)
        return []

    def _parse_busqueda_sector(self, html: str, sector: str, limit: int) -> List[Dict]:
        """Parsear resultados de búsqueda por sector"""
        soup = BeautifulSoup(html, 'lxml')
        empresas = []

        for item in soup.find_all(['div', 'li'], limit=limit):
            nombre = item.find(['h3', 'h4', 'strong'])
            if nombre:
                empresas.append({
                    "nombre": nombre.text.strip(),
                    "sector": sector,
                    "fuente": "BORME"
                })

        return empresas

    async def get_sociedades_anonimas(self, comunidad: str = None) -> List[Dict]:
        """
        Obtener listado de Sociedades Anónimas del BORME
        """
        logger.info(f"Obteniendo SA{' en ' + comunidad if comunidad else ''}")

        url = self.BASE_URL
        if comunidad:
            url += f"?comunidad={comunidad}"

        html = await self.fetch_url(url)
        if html:
            return self._parse_sa(html, comunidad)
        return []

    def _parse_sa(self, html: str, comunidad: str = None) -> List[Dict]:
        """Parsear listado de SA del BORME"""
        soup = BeautifulSoup(html, 'lxml')
        empresas = []

        # Buscar entradas de sociedades anónimas
        for entry in soup.find_all('div', class_=lambda x: x and 'borme-entry' in x if x else False):
            nombre = entry.find('strong')
            if nombre:
                cif_match = re.search(r'([A-Z]\d{8})', entry.text)
                empresas.append({
                    "nombre": nombre.text.strip(),
                    "cif": cif_match.group(0) if cif_match else None,
                    "comunidad_autonoma": comunidad,
                    "fuente": "BORME"
                })

        return empresas

    async def get_ultima_hora(self, days: int = 7) -> List[Dict]:
        """
        Obtener empresas registradas en los últimos días
        """
        logger.info(f"Obteniendo empresas de los últimos {days} días")

        empresas = []
        for i in range(days):
            fecha = datetime.now()
            url = f"{self.BASE_URL}fecha/{fecha.strftime('%Y-%m-%d')}"
            html = await self.fetch_url(url)
            if html:
                empresas.extend(self._parse_borme_dia(html))

        return empresas

    def _parse_borme_dia(self, html: str) -> List[Dict]:
        """Parsear BORME de un día específico"""
        soup = BeautifulSoup(html, 'lxml')
        empresas = []

        for entry in soup.find_all('div', class_='entrada'):
            datos = self.parse_borme_entry(str(entry))
            if datos:
                empresas.append(datos)

        return empresas

    def parse_borme_entry(self, html: str) -> Optional[Dict]:
        """
        Parsear una entrada del BORME
        """
        soup = BeautifulSoup(html, 'lxml')

        # Extraer nombre
        nombre = None
        nombre_tag = soup.find(['strong', 'h3', 'h4'])
        if nombre_tag:
            nombre = nombre_tag.text.strip()

        # Extraer CIF
        cif = None
        cif_match = re.search(r'([A-Z]\d{8})', soup.text)
        if cif_match:
            cif = cif_match.group(0)

        # Extraer domicilio
        domicilio = None
        dom_match = re.search(r'Domicilio:\s*(.+?)(?:\n|$)', soup.text, re.IGNORECASE)
        if dom_match:
            domicilio = dom_match.group(1).strip()

        # Extraer capital social
        capital = None
        cap_match = re.search(r'Capital:\s*([\d.,]+\s*€)', soup.text, re.IGNORECASE)
        if cap_match:
            capital_str = cap_match.group(1).replace('.', '').replace(',', '.')
            capital = float(re.search(r'[\d.]+', capital_str).group(0))

        # Extraer fecha de constitución
        fecha_const = None
        fecha_match = re.search(r'(\d{2}/\d{2}/\d{4})', soup.text)
        if fecha_match:
            fecha_const = fecha_match.group(1)

        # Determinar sector
        sector = self._inferir_sector(soup.text)

        return {
            "nombre": nombre,
            "cif": cif,
            "domicilio": domicilio,
            "capital_social": capital,
            "fecha_constitucion": fecha_const,
            "objeto_social": None,
            "sector": sector,
            "fuente": "BORME"
        }

    def _inferir_sector(self, texto: str) -> str:
        """Inferir sector del objeto social"""
        texto_lower = texto.lower()

        sectores_keywords = {
            "Medios": ["prensa", "medios", "comunicación", "publicidad", "editorial", "radio", "televisión"],
            "Banca": ["banca", "banco", "financiero", "crédito"],
            "Energía": ["energía", "eléctrica", "gas", "petróleo"],
            "Construcción": ["construcción", "obra", "infraestructura"],
            "Retail": ["comercio", "venta", "distribución", "tienda"],
            "Tecnología": ["tecnología", "software", "informática", "digital"],
            "Turismo": ["turismo", "hotel", "hostelería"],
            "Transporte": ["transporte", "logística"],
        }

        for sector, keywords in sectores_keywords.items():
            if any(kw in texto_lower for kw in keywords):
                return sector

        return "Otros"
