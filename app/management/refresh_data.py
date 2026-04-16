"""
Script de refresco y enriquecimiento de datos.

Orquesta:
  1. Scrapers (CNMV, Expansión, elEconomista) → registros crudos.
  2. Pipeline ETL → validar, deduplicar, upsert en BD.
  3. publicidad_estimator → rellenar inversion_publicidad donde falte.
  4. Estadísticas finales.

Uso:
    python3 -m app.management.refresh_data
"""

from __future__ import annotations

import logging
import sys
from dataclasses import asdict, dataclass, field
from typing import Any

from sqlalchemy import func

from app import models
from app.database import SessionLocal
from app.etl import pipeline, publicidad_estimator
from app.scrapers import cnmv_xbrl, eleconomista_scraper, expansion_top500, wikidata_scraper

logger = logging.getLogger(__name__)


@dataclass
class RefreshReport:
    empresas_antes: int = 0
    empresas_despues: int = 0
    nuevas: int = 0
    actualizadas: int = 0
    publicidad_estimada: int = 0
    data_quality_score_avg: float = 0.0
    por_scraper: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)


def _count(db) -> int:
    return db.query(func.count(models.Empresa.id)).scalar() or 0


def _avg_quality(db) -> float:
    v = db.query(func.avg(models.Empresa.data_quality_score)).scalar()
    return round(float(v or 0.0), 2)


def _run_scraper(name: str, fn) -> list[dict]:
    try:
        data = fn()
        logger.info("Scraper %s: %d registros", name, len(data))
        return data or []
    except Exception as e:
        logger.warning("Scraper %s falló: %s", name, e)
        return []


def refresh() -> RefreshReport:
    report = RefreshReport()

    db = SessionLocal()
    try:
        report.empresas_antes = _count(db)

        # 1) Scrapers
        scrapers = [
            ("cnmv", cnmv_xbrl.scrape),
            ("wikipedia_ibex", expansion_top500.scrape),
            ("eleconomista", eleconomista_scraper.scrape),
            ("wikidata", wikidata_scraper.scrape),
        ]

        all_records: list[dict] = []
        for name, fn in scrapers:
            data = _run_scraper(name, fn)
            report.por_scraper[name] = {"registros": len(data)}
            all_records.extend(data)

        # 2) Pipeline ETL
        if all_records:
            stats = pipeline.run(all_records, db=db)
            logger.info("Pipeline ETL: %s", stats)
            report.nuevas = stats.get("inserted", 0)
            report.actualizadas = stats.get("updated", 0)
            report.por_scraper["_pipeline"] = stats
        else:
            logger.warning("Ningún scraper devolvió datos. Se mantiene la BD sin cambios.")

        # 3) Estimador de publicidad sobre empresas sin dato
        pub_stats = publicidad_estimator.estimate_all_missing(db)
        report.publicidad_estimada = pub_stats["updated"]

        # 4) Stats finales
        report.empresas_despues = _count(db)
        report.data_quality_score_avg = _avg_quality(db)
    finally:
        db.close()

    return report


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    print("=" * 60)
    print("🔄  Refresh & enriquecimiento de datos")
    print("=" * 60)

    report = refresh()
    d = report.as_dict()

    print()
    print(f"  Empresas antes         : {d['empresas_antes']}")
    print(f"  Empresas después       : {d['empresas_despues']}")
    print(f"  Nuevas                 : {d['nuevas']}")
    print(f"  Actualizadas           : {d['actualizadas']}")
    print(f"  Publicidad estimada    : {d['publicidad_estimada']}")
    print(f"  Calidad media (0-100)  : {d['data_quality_score_avg']}")
    print()
    print("  Por scraper:")
    for name, meta in d["por_scraper"].items():
        print(f"    - {name}: {meta}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
