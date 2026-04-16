# Rankings Empresas España 📊

Aplicación web para visualizar rankings de empresas españolas por facturación e inversión publicitaria.

## Características

- 🏆 **Rankings** por facturación e inversión en publicidad
- 🔍 **Filtros** por sector y comunidad autónoma
- 📈 **Gráficos interactivos** con Chart.js
- 📥 **Exportación** a CSV
- 🎨 **Interfaz moderna** con TailwindCSS

## Instalación

### Requisitos

- Python 3.9+
- pip

### Pasos

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Inicializar base de datos con datos de ejemplo
python -m app.seed

# 3. Iniciar servidor
python run.py
```

## Uso

1. Abre http://localhost:8000 en tu navegador
2. Usa los filtros para seleccionar sector/comunidad
3. Cambia entre ranking por facturación o publicidad
4. Exporta los datos a CSV si lo necesitas

## API Endpoints

| Endpoint | Descripción |
|----------|-------------|
| `GET /` | Frontend web |
| `GET /api/empresas` | Listar empresas |
| `GET /api/ranking/facturacion` | Ranking por facturación |
| `GET /api/ranking/publicidad` | Ranking por inversión publicidad |
| `GET /api/sectores` | Estadísticas por sector |
| `GET /api/comunidades` | Estadísticas por CCAA |
| `GET /api/filtros/sectores` | Listar sectores disponibles |
| `GET /api/filtros/comunidades` | Listar CCAA disponibles |
| `POST /api/empresas` | Crear nueva empresa |

## Estructura

```
.
├── app/
│   ├── main.py          # API FastAPI
│   ├── database.py      # Configuración DB
│   ├── models.py        # Modelos SQLAlchemy
│   ├── schemas.py       # Esquemas Pydantic
│   ├── seed.py          # Datos de ejemplo
│   └── scrapers/        # Módulos de scraping
│       ├── borme.py     # Scraper BORME
│       └── rankings.py  # Rankings públicos
├── static/
│   └── index.html       # Frontend web
├── requirements.txt
└── run.py               # Script de inicio
```

## Notas

- Los datos incluidos son **demostrativos** basados en empresas reales
- Para datos oficiales consulte el [BORME](https://www.boe.es/diario_borme/)
- Los scrapers reales requieren adaptación constante por cambios en las webs fuente

## Tecnologías

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Frontend**: HTML, TailwindCSS, Chart.js
- **Scraping**: BeautifulSoup4, httpx

## Licencia

MIT
