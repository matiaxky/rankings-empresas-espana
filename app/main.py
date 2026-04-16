from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, desc, select as sa_select
from typing import List, Optional
from app import models
from app.database import engine, get_db
from app.schemas import (
    EmpresaCreate, EmpresaResponse, RankingResponse,
    SectorStats, ComunidadStats, StatsResponse, ReloadResponse,
    EnrichResponse,
)

# Crear tablas
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Rankings Empresas España",
    description="API para consultar rankings de empresas españolas por facturación e inversión",
    version="1.0.0"
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(
    sector: Optional[str] = Query(None),
    comunidad: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    base = db.query(models.Empresa)
    if sector:
        base = base.filter(models.Empresa.sector == sector)
    if comunidad:
        base = base.filter(models.Empresa.comunidad_autonoma == comunidad)

    total_empresas = base.with_entities(func.count(models.Empresa.id)).scalar() or 0
    total_sectores = base.filter(models.Empresa.sector != None).with_entities(
        func.count(func.distinct(models.Empresa.sector))
    ).scalar() or 0
    total_comunidades = base.filter(models.Empresa.comunidad_autonoma != None).with_entities(
        func.count(func.distinct(models.Empresa.comunidad_autonoma))
    ).scalar() or 0
    facturacion_total = base.filter(models.Empresa.facturacion != None).with_entities(
        func.sum(models.Empresa.facturacion)
    ).scalar() or 0
    año_min = base.with_entities(func.min(models.Empresa.año_facturacion)).scalar()
    año_max = base.with_entities(func.max(models.Empresa.año_facturacion)).scalar()
    quality_avg = base.with_entities(func.avg(models.Empresa.data_quality_score)).scalar()

    return StatsResponse(
        total_empresas=total_empresas,
        total_sectores=total_sectores,
        total_comunidades=total_comunidades,
        facturacion_total=float(facturacion_total),
        año_facturacion_min=año_min,
        año_facturacion_max=año_max,
        data_quality_score_avg=round(float(quality_avg), 2) if quality_avg is not None else None,
    )


@app.get("/api/empresas", response_model=List[EmpresaResponse])
async def get_empresas(
    sector: Optional[str] = Query(None),
    comunidad: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    query = db.query(models.Empresa)

    if sector:
        query = query.filter(models.Empresa.sector == sector)
    if comunidad:
        query = query.filter(models.Empresa.comunidad_autonoma == comunidad)

    return query.order_by(desc(models.Empresa.facturacion)).limit(limit).all()


@app.get("/api/empresas/{empresa_id}", response_model=EmpresaResponse)
async def get_empresa(empresa_id: int, db: Session = Depends(get_db)):
    empresa = db.query(models.Empresa).filter(models.Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return empresa


@app.get("/api/ranking/facturacion", response_model=List[RankingResponse])
async def ranking_facturacion(
    sector: Optional[str] = Query(None),
    comunidad: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(models.Empresa)

    if sector:
        query = query.filter(models.Empresa.sector == sector)
    if comunidad:
        query = query.filter(models.Empresa.comunidad_autonoma == comunidad)

    empresas = query.filter(
        models.Empresa.facturacion != None
    ).order_by(desc(models.Empresa.facturacion)).limit(limit).all()

    return [
        RankingResponse(
            rank=i+1,
            empresa=e,
            metrica=e.facturacion,
            tipo_ranking="facturacion"
        )
        for i, e in enumerate(empresas)
    ]


@app.get("/api/ranking/publicidad", response_model=List[RankingResponse])
async def ranking_publicidad(
    sector: Optional[str] = Query(None),
    comunidad: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(models.Empresa)

    if sector:
        query = query.filter(models.Empresa.sector == sector)
    if comunidad:
        query = query.filter(models.Empresa.comunidad_autonoma == comunidad)

    empresas = query.filter(
        models.Empresa.inversion_publicidad != None
    ).order_by(desc(models.Empresa.inversion_publicidad)).limit(limit).all()

    return [
        RankingResponse(
            rank=i+1,
            empresa=e,
            metrica=e.inversion_publicidad,
            tipo_ranking="inversion_publicidad"
        )
        for i, e in enumerate(empresas)
    ]


@app.get("/api/sectores", response_model=List[SectorStats])
async def stats_sectores(
    sector: Optional[str] = Query(None),
    comunidad: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    # Correlated subquery — single query, no N+1
    inner = aliased(models.Empresa)
    top_empresa_subq = (
        sa_select(inner.nombre)
        .where(inner.sector == models.Empresa.sector)
        .order_by(desc(inner.facturacion))
        .limit(1)
        .correlate(models.Empresa)
        .scalar_subquery()
    )

    query = db.query(
        models.Empresa.sector,
        func.count(models.Empresa.id).label("num_empresas"),
        func.sum(models.Empresa.facturacion).label("facturacion_total"),
        func.avg(models.Empresa.facturacion).label("facturacion_media"),
        top_empresa_subq.label("top_empresa"),
    ).filter(
        models.Empresa.sector != None,
        models.Empresa.facturacion != None
    )

    if sector:
        query = query.filter(models.Empresa.sector == sector)
    if comunidad:
        query = query.filter(models.Empresa.comunidad_autonoma == comunidad)

    resultados = query.group_by(models.Empresa.sector).all()

    stats = [
        SectorStats(
            sector=r.sector,
            num_empresas=r.num_empresas,
            facturacion_total=r.facturacion_total or 0,
            facturacion_media=r.facturacion_media or 0,
            top_empresa=r.top_empresa or "N/A"
        )
        for r in resultados
    ]

    return sorted(stats, key=lambda x: x.facturacion_total, reverse=True)


@app.get("/api/comunidades", response_model=List[ComunidadStats])
async def stats_comunidades(
    sector: Optional[str] = Query(None),
    comunidad: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    base = db.query(models.Empresa).filter(
        models.Empresa.facturacion != None
    )
    if sector:
        base = base.filter(models.Empresa.sector == sector)
    if comunidad:
        base = base.filter(models.Empresa.comunidad_autonoma == comunidad)

    total = base.with_entities(func.sum(models.Empresa.facturacion)).scalar() or 1

    resultados = base.filter(
        models.Empresa.comunidad_autonoma != None,
    ).with_entities(
        models.Empresa.comunidad_autonoma,
        func.count(models.Empresa.id).label("num_empresas"),
        func.sum(models.Empresa.facturacion).label("facturacion_total"),
    ).group_by(models.Empresa.comunidad_autonoma).all()

    return sorted([
        ComunidadStats(
            comunidad=r.comunidad_autonoma,
            num_empresas=r.num_empresas,
            facturacion_total=r.facturacion_total or 0,
            porcentaje_nacional=((r.facturacion_total or 0) / total * 100) if total > 0 else 0
        )
        for r in resultados
    ], key=lambda x: x.facturacion_total, reverse=True)


@app.get("/api/filtros/sectores")
async def listar_sectores(db: Session = Depends(get_db)):
    sectores = db.query(models.Empresa.sector).distinct().all()
    return sorted([s.sector for s in sectores if s.sector])


@app.get("/api/filtros/comunidades")
async def listar_comunidades(db: Session = Depends(get_db)):
    comunidades = db.query(models.Empresa.comunidad_autonoma).distinct().all()
    return sorted([c.comunidad_autonoma for c in comunidades if c.comunidad_autonoma])


@app.post("/api/empresas", response_model=EmpresaResponse)
async def crear_empresa(empresa: EmpresaCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Empresa).filter(models.Empresa.cif == empresa.cif).first()
    if existing:
        raise HTTPException(status_code=400, detail="Empresa con este CIF ya existe")

    db_empresa = models.Empresa(**empresa.model_dump())
    db.add(db_empresa)
    db.commit()
    db.refresh(db_empresa)
    return db_empresa


@app.post("/api/admin/reload", response_model=ReloadResponse)
async def reload_data(db: Session = Depends(get_db)):
    try:
        from app.seed import seed_database
        seed_database()
        count = db.query(func.count(models.Empresa.id)).scalar() or 0
        return ReloadResponse(
            status="ok",
            empresas_insertadas=count,
            message=f"Base de datos recargada con {count} empresas."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/enrich", response_model=EnrichResponse)
async def enrich_data(db: Session = Depends(get_db)):
    """
    Ejecuta el pipeline de enriquecimiento: scrapers + ETL + estimador
    de publicidad. Devuelve conteos antes/después y métricas de calidad.

    Ejecución sincrónica (en thread pool de FastAPI), ya que la mayor
    parte del tiempo está en I/O HTTP a las fuentes externas. Si algún
    scraper falla, el endpoint no aborta: registra el fallo y continúa.
    """
    try:
        import asyncio
        from app.management.refresh_data import refresh
        # refresh() hace trabajo bloqueante (httpx sync + SQL); lo movemos
        # a un thread para no ocupar el loop.
        loop = asyncio.get_event_loop()
        report = await loop.run_in_executor(None, refresh)

        return EnrichResponse(
            status="ok",
            empresas_antes=report.empresas_antes,
            empresas_despues=report.empresas_despues,
            nuevas=report.nuevas,
            actualizadas=report.actualizadas,
            publicidad_estimada=report.publicidad_estimada,
            data_quality_score_avg=report.data_quality_score_avg,
            detalles=report.por_scraper,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
