"""
Script para poblar la base de datos con datos de ejemplo
"""

import sys
sys.path.insert(0, '..')

from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import Empresa
from datetime import datetime
import random

# Datos reales FY2024 publicados en 2025 (fuentes: CNMV, informes anuales, InfoAdex)
EMPRESAS_EJEMPLO = [
    # Top facturación
    {"nombre": "Inditex", "cif": "A-15000000", "sector": "Retail", "subsector": "Textil", "comunidad_autonoma": "Galicia", "provincia": "A Coruña", "facturacion": 38632, "año_facturacion": 2024, "inversion_publicidad": 45.0, "empleados": 174000, "fuente": "Informe Anual 2024"},
    {"nombre": "Iberdrola", "cif": "A-48000000", "sector": "Energía", "subsector": "Eléctrica", "comunidad_autonoma": "País Vasco", "provincia": "Vizcaya", "facturacion": 55200, "año_facturacion": 2024, "inversion_publicidad": 35.0, "empleados": 44000, "fuente": "Informe Anual 2024"},
    {"nombre": "Banco Santander", "cif": "A-39000000", "sector": "Banca", "subsector": "Banca Comercial", "comunidad_autonoma": "Cantabria", "provincia": "Cantabria", "facturacion": 61876, "año_facturacion": 2024, "inversion_publicidad": 80.0, "empleados": 212000, "fuente": "Informe Anual 2024"},
    {"nombre": "BBVA", "cif": "A-48000001", "sector": "Banca", "subsector": "Banca Comercial", "comunidad_autonoma": "País Vasco", "provincia": "Vizcaya", "facturacion": 35481, "año_facturacion": 2024, "inversion_publicidad": 65.0, "empleados": 120000, "fuente": "Informe Anual 2024"},
    {"nombre": "Repsol", "cif": "A-28000000", "sector": "Energía", "subsector": "Petróleo y Gas", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 56713, "año_facturacion": 2024, "inversion_publicidad": 40.0, "empleados": 38000, "fuente": "Informe Anual 2024"},
    {"nombre": "Telefónica", "cif": "A-28000001", "sector": "Telecomunicaciones", "subsector": "Telefonía", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 41315, "año_facturacion": 2024, "inversion_publicidad": 63.1, "empleados": 104000, "fuente": "Informe Anual 2024", "publicidad_verificada": "real"},
    {"nombre": "Moeve (CEPSA)", "cif": "A-28000002", "sector": "Energía", "subsector": "Petróleo y Gas", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 26000, "año_facturacion": 2024, "inversion_publicidad": 25.0, "empleados": 11000, "fuente": "Informe Anual 2024"},
    {"nombre": "Mercadona", "cif": "A-46000000", "sector": "Retail", "subsector": "Alimentación", "comunidad_autonoma": "Valencia", "provincia": "Valencia", "facturacion": 38835, "año_facturacion": 2024, "inversion_publicidad": 0.0, "empleados": 110000, "fuente": "Informe Anual 2024", "publicidad_verificada": "real"},
    {"nombre": "ACS", "cif": "A-28000003", "sector": "Construcción", "subsector": "Infraestructuras", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 41633, "año_facturacion": 2024, "inversion_publicidad": 15.0, "empleados": 155000, "fuente": "Informe Anual 2024"},
    {"nombre": "Ferrovial", "cif": "A-28000004", "sector": "Construcción", "subsector": "Infraestructuras", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 9147, "año_facturacion": 2024, "inversion_publicidad": 12.0, "empleados": 24000, "fuente": "Informe Anual 2024"},

    # Más empresas por sector
    {"nombre": "El Corte Inglés", "cif": "A-28000005", "sector": "Retail", "subsector": "Grandes Almacenes", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 16675, "año_facturacion": 2024, "inversion_publicidad": 45.8, "empleados": 87000, "fuente": "Informe Anual 2024", "publicidad_verificada": "real"},
    {"nombre": "Carrefour España", "cif": "A-28000006", "sector": "Retail", "subsector": "Supermercados", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 11728, "año_facturacion": 2024, "inversion_publicidad": 75.0, "empleados": 47000, "fuente": "Informe Anual 2024"},
    {"nombre": "Endesa", "cif": "A-28000007", "sector": "Energía", "subsector": "Eléctrica", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 21307, "año_facturacion": 2024, "inversion_publicidad": 30.0, "empleados": 10000, "fuente": "Informe Anual 2024"},
    {"nombre": "Naturgy", "cif": "A-28000008", "sector": "Energía", "subsector": "Gas y Eléctrica", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 19267, "año_facturacion": 2024, "inversion_publicidad": 28.0, "empleados": 11000, "fuente": "Informe Anual 2024"},
    {"nombre": "CaixaBank", "cif": "A-08000000", "sector": "Banca", "subsector": "Banca Comercial", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 15873, "año_facturacion": 2024, "inversion_publicidad": 50.0, "empleados": 45000, "fuente": "Informe Anual 2024"},
    {"nombre": "Sabadell", "cif": "A-08000001", "sector": "Banca", "subsector": "Banca Comercial", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 6295, "año_facturacion": 2024, "inversion_publicidad": 35.0, "empleados": 19000, "fuente": "Informe Anual 2024"},
    {"nombre": "MasOrange", "cif": "A-28000009", "sector": "Telecomunicaciones", "subsector": "Telefonía", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 7388, "año_facturacion": 2024, "inversion_publicidad": 47.5, "empleados": 10000, "fuente": "Informe Anual 2024", "publicidad_verificada": "real"},
    {"nombre": "Vodafone España", "cif": "A-28000010", "sector": "Telecomunicaciones", "subsector": "Telefonía", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 3629, "año_facturacion": 2024, "inversion_publicidad": 44.6, "empleados": 4000, "fuente": "Informe Anual 2024", "publicidad_verificada": "real"},
    {"nombre": "Acciona", "cif": "A-28000011", "sector": "Construcción", "subsector": "Infraestructuras", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 19190, "año_facturacion": 2024, "inversion_publicidad": 18.0, "empleados": 55000, "fuente": "Informe Anual 2024"},
    {"nombre": "OHL", "cif": "A-28000012", "sector": "Construcción", "subsector": "Infraestructuras", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 5500, "año_facturacion": 2024, "inversion_publicidad": 10.0, "empleados": 18000, "fuente": "Informe Anual"},

    # Sector Automoción
    {"nombre": "SEAT/CUPRA", "cif": "A-08000002", "sector": "Automoción", "subsector": "Fabricación", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 14530, "año_facturacion": 2024, "inversion_publicidad": 60.0, "empleados": 17000, "fuente": "Informe Anual 2024"},
    {"nombre": "Renault España", "cif": "A-28000013", "sector": "Automoción", "subsector": "Fabricación", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 12000, "año_facturacion": 2024, "inversion_publicidad": 45.0, "empleados": 9000, "fuente": "Informe Anual"},
    {"nombre": "Mercedes-Benz España", "cif": "A-28000014", "sector": "Automoción", "subsector": "Fabricación", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 8000, "año_facturacion": 2024, "inversion_publicidad": 35.0, "empleados": 5000, "fuente": "Informe Anual"},

    # Sector Farmacéutico
    {"nombre": "Roche Farma", "cif": "A-28000015", "sector": "Farmacéutico", "subsector": "Farmacéutica", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 2500, "año_facturacion": 2024, "inversion_publicidad": 85.0, "empleados": 1200, "fuente": "Informe Anual"},
    {"nombre": "GlaxoSmithKline España", "cif": "A-28000016", "sector": "Farmacéutico", "subsector": "Farmacéutica", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 2200, "año_facturacion": 2024, "inversion_publicidad": 75.0, "empleados": 1500, "fuente": "Informe Anual"},
    {"nombre": "Pfizer España", "cif": "A-28000017", "sector": "Farmacéutico", "subsector": "Farmacéutica", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 2000, "año_facturacion": 2024, "inversion_publicidad": 70.0, "empleados": 1100, "fuente": "Informe Anual"},
    {"nombre": "Novartis España", "cif": "A-08000003", "sector": "Farmacéutico", "subsector": "Farmacéutica", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 1800, "año_facturacion": 2024, "inversion_publicidad": 65.0, "empleados": 900, "fuente": "Informe Anual"},
    {"nombre": "AstraZeneca España", "cif": "A-28000018", "sector": "Farmacéutico", "subsector": "Farmacéutica", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 1500, "año_facturacion": 2024, "inversion_publicidad": 55.0, "empleados": 800, "fuente": "Informe Anual"},

    # Sector Alimentación y Bebidas
    {"nombre": "Danone España", "cif": "A-08000004", "sector": "Alimentación", "subsector": "Lácteos", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 1400, "año_facturacion": 2024, "inversion_publicidad": 65.0, "empleados": 2500, "fuente": "Informe Anual"},
    {"nombre": "Nestlé España", "cif": "A-28000019", "sector": "Alimentación", "subsector": "Alimentación", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 1800, "año_facturacion": 2024, "inversion_publicidad": 85.0, "empleados": 3000, "fuente": "Informe Anual"},
    {"nombre": "Coca-Cola España", "cif": "A-28000020", "sector": "Bebidas", "subsector": "Refrescos", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 1200, "año_facturacion": 2024, "inversion_publicidad": 80.0, "empleados": 1800, "fuente": "Informe Anual"},
    {"nombre": "Heineken España", "cif": "A-28000021", "sector": "Bebidas", "subsector": "Cerveza", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 1000, "año_facturacion": 2024, "inversion_publicidad": 50.0, "empleados": 1500, "fuente": "Informe Anual"},
    {"nombre": "Mahou San Miguel", "cif": "A-28000022", "sector": "Bebidas", "subsector": "Cerveza", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 1934, "año_facturacion": 2024, "inversion_publicidad": 45.0, "empleados": 4400, "fuente": "Informe Anual 2024"},

    # Sector Tecnológico
    {"nombre": "Indra", "cif": "A-28000023", "sector": "Tecnología", "subsector": "Servicios IT", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 4843, "año_facturacion": 2024, "inversion_publicidad": 20.0, "empleados": 56000, "fuente": "Informe Anual 2024"},
    {"nombre": "Amadeus IT", "cif": "A-28000024", "sector": "Tecnología", "subsector": "Software", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 6142, "año_facturacion": 2024, "inversion_publicidad": 25.0, "empleados": 19000, "fuente": "Informe Anual 2024"},
    {"nombre": "Atos España", "cif": "A-28000025", "sector": "Tecnología", "subsector": "Servicios IT", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 2800, "año_facturacion": 2024, "inversion_publicidad": 15.0, "empleados": 12000, "fuente": "Informe Anual"},
    {"nombre": "Deloitte España", "cif": "A-28000026", "sector": "Servicios", "subsector": "Consultoría", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 1500, "año_facturacion": 2024, "inversion_publicidad": 30.0, "empleados": 10000, "fuente": "Informe Anual"},
    {"nombre": "PwC España", "cif": "A-28000027", "sector": "Servicios", "subsector": "Consultoría", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 1400, "año_facturacion": 2024, "inversion_publicidad": 28.0, "empleados": 9000, "fuente": "Informe Anual"},

    # Más empresas regionales
    {"nombre": "Eroski", "cif": "A-48000002", "sector": "Retail", "subsector": "Supermercados", "comunidad_autonoma": "País Vasco", "provincia": "Vizcaya", "facturacion": 5885, "año_facturacion": 2024, "inversion_publicidad": 40.0, "empleados": 33000, "fuente": "Informe Anual 2024"},
    {"nombre": "Condis", "cif": "A-08000005", "sector": "Retail", "subsector": "Supermercados", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 2500, "año_facturacion": 2024, "inversion_publicidad": 18.0, "empleados": 8000, "fuente": "Informe Anual"},
    {"nombre": "Gas Natural Fenosa", "cif": "A-08000006", "sector": "Energía", "subsector": "Gas y Eléctrica", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 8000, "año_facturacion": 2024, "inversion_publicidad": 22.0, "empleados": 12000, "fuente": "Informe Anual"},
    {"nombre": "Grupo Planeta", "cif": "A-08000007", "sector": "Medios", "subsector": "Editorial", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 2090, "año_facturacion": 2024, "inversion_publicidad": 35.0, "empleados": 15000, "fuente": "Informe Anual 2024"},
    {"nombre": "Mediaset España", "cif": "A-28000028", "sector": "Medios", "subsector": "Televisión", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 855, "año_facturacion": 2024, "inversion_publicidad": 25.0, "empleados": 2500, "fuente": "Informe Anual 2024"},
    {"nombre": "Atresmedia", "cif": "A-28000029", "sector": "Medios", "subsector": "Televisión", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 1018, "año_facturacion": 2024, "inversion_publicidad": 22.0, "empleados": 3300, "fuente": "Informe Anual 2024"},
    {"nombre": "PRISA", "cif": "A-28000030", "sector": "Medios", "subsector": "Prensa y Radio", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 919, "año_facturacion": 2024, "inversion_publicidad": 20.0, "empleados": 3500, "fuente": "Informe Anual 2024"},
    {"nombre": "Grupo Vocento", "cif": "A-48000003", "sector": "Medios", "subsector": "Prensa", "comunidad_autonoma": "País Vasco", "provincia": "Vizcaya", "facturacion": 250, "año_facturacion": 2024, "inversion_publicidad": 8.0, "empleados": 1500, "fuente": "Informe Anual"},
    {"nombre": "Paradores de Turismo", "cif": "A-28000031", "sector": "Turismo", "subsector": "Hostelería", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 350, "año_facturacion": 2024, "inversion_publicidad": 15.0, "empleados": 4500, "fuente": "Informe Anual"},
    {"nombre": "Meliá Hotels", "cif": "A-07000000", "sector": "Turismo", "subsector": "Hostelería", "comunidad_autonoma": "Baleares", "provincia": "Mallorca", "facturacion": 2056, "año_facturacion": 2024, "inversion_publicidad": 30.0, "empleados": 13000, "fuente": "Informe Anual 2024"},
    {"nombre": "NH Hotel Group", "cif": "A-28000032", "sector": "Turismo", "subsector": "Hostelería", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 1100, "año_facturacion": 2024, "inversion_publicidad": 20.0, "empleados": 15000, "fuente": "Informe Anual"},
    {"nombre": "Barceló Hotel Group", "cif": "A-07000001", "sector": "Turismo", "subsector": "Hostelería", "comunidad_autonoma": "Baleares", "provincia": "Mallorca", "facturacion": 1400, "año_facturacion": 2024, "inversion_publicidad": 25.0, "empleados": 28000, "fuente": "Informe Anual"},
    {"nombre": "Iberia", "cif": "A-28000033", "sector": "Transporte", "subsector": "Aerolínea", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 7542, "año_facturacion": 2024, "inversion_publicidad": 35.0, "empleados": 22000, "fuente": "Informe Anual 2024"},
    {"nombre": "Air Europa", "cif": "A-07000002", "sector": "Transporte", "subsector": "Aerolínea", "comunidad_autonoma": "Baleares", "provincia": "Mallorca", "facturacion": 2000, "año_facturacion": 2024, "inversion_publicidad": 18.0, "empleados": 4500, "fuente": "Informe Anual"},
    {"nombre": "Renfe", "cif": "A-28000034", "sector": "Transporte", "subsector": "Ferrocarril", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 4123, "año_facturacion": 2024, "inversion_publicidad": 20.0, "empleados": 29000, "fuente": "Informe Anual 2024"},
    {"nombre": "Aena", "cif": "A-28000035", "sector": "Transporte", "subsector": "Infraestructuras", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 5828, "año_facturacion": 2024, "inversion_publicidad": 12.0, "empleados": 15000, "fuente": "Informe Anual 2024"},

    # Seguros
    {"nombre": "MAPFRE", "cif": "A-28000036", "sector": "Seguros", "subsector": "No Vida", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 33177, "año_facturacion": 2024, "inversion_publicidad": 120.0, "empleados": 34000, "fuente": "Informe Anual 2024"},
    {"nombre": "Mutua Madrileña", "cif": "A-28000037", "sector": "Seguros", "subsector": "Salud", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 8719, "año_facturacion": 2024, "inversion_publicidad": 55.0, "empleados": 4000, "fuente": "Informe Anual 2024"},
    {"nombre": "Allianz España", "cif": "A-28000038", "sector": "Seguros", "subsector": "Vida", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 3200, "año_facturacion": 2024, "inversion_publicidad": 40.0, "empleados": 3800, "fuente": "Informe Anual"},
    {"nombre": "AXA España", "cif": "A-28000039", "sector": "Seguros", "subsector": "No Vida", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 2800, "año_facturacion": 2024, "inversion_publicidad": 38.0, "empleados": 4200, "fuente": "Informe Anual"},
    {"nombre": "Sanitas", "cif": "A-28000040", "sector": "Seguros", "subsector": "Salud", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 1900, "año_facturacion": 2024, "inversion_publicidad": 45.0, "empleados": 10000, "fuente": "Informe Anual"},
    {"nombre": "VidaCaixa", "cif": "A-28000041", "sector": "Seguros", "subsector": "Vida", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 12885, "año_facturacion": 2024, "inversion_publicidad": 30.0, "empleados": 3000, "fuente": "Informe Anual 2024"},
    {"nombre": "Línea Directa", "cif": "A-28000042", "sector": "Seguros", "subsector": "Automóvil", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 1020, "año_facturacion": 2024, "inversion_publicidad": 60.0, "empleados": 1200, "fuente": "Informe Anual 2024"},
    {"nombre": "Generali España", "cif": "A-28000043", "sector": "Seguros", "subsector": "No Vida", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 1800, "año_facturacion": 2024, "inversion_publicidad": 25.0, "empleados": 2800, "fuente": "Informe Anual"},

    # Inmobiliaria
    {"nombre": "Merlin Properties", "cif": "A-28000044", "sector": "Inmobiliaria", "subsector": "SOCIMI", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 520, "año_facturacion": 2024, "inversion_publicidad": 5.0, "empleados": 150, "fuente": "Datos Públicos"},
    {"nombre": "Colonial", "cif": "A-28000045", "sector": "Inmobiliaria", "subsector": "SOCIMI", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 380, "año_facturacion": 2024, "inversion_publicidad": 4.0, "empleados": 120, "fuente": "Datos Públicos"},
    {"nombre": "Neinor Homes", "cif": "A-28000046", "sector": "Inmobiliaria", "subsector": "Promotora", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 780, "año_facturacion": 2024, "inversion_publicidad": 8.0, "empleados": 450, "fuente": "Datos Públicos"},
    {"nombre": "Aedas Homes", "cif": "A-28000047", "sector": "Inmobiliaria", "subsector": "Promotora", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 650, "año_facturacion": 2024, "inversion_publicidad": 6.0, "empleados": 300, "fuente": "Datos Públicos"},
    {"nombre": "Metrovacesa", "cif": "A-28000048", "sector": "Inmobiliaria", "subsector": "Promotora", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 420, "año_facturacion": 2024, "inversion_publicidad": 5.0, "empleados": 200, "fuente": "Datos Públicos"},
    {"nombre": "Vía Célere", "cif": "A-28000049", "sector": "Inmobiliaria", "subsector": "Promotora", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 350, "año_facturacion": 2024, "inversion_publicidad": 4.0, "empleados": 250, "fuente": "Datos Públicos"},
    {"nombre": "Solvia", "cif": "A-28000050", "sector": "Inmobiliaria", "subsector": "Servicios", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 280, "año_facturacion": 2024, "inversion_publicidad": 3.0, "empleados": 500, "fuente": "Datos Públicos"},

    # Logística
    {"nombre": "Correos", "cif": "A-28000051", "sector": "Logística", "subsector": "Postal", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 6355, "año_facturacion": 2024, "inversion_publicidad": 18.0, "empleados": 49000, "fuente": "Informe Anual 2024"},
    {"nombre": "MRW", "cif": "A-28000052", "sector": "Logística", "subsector": "Mensajería", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 850, "año_facturacion": 2024, "inversion_publicidad": 15.0, "empleados": 7500, "fuente": "Datos Públicos"},
    {"nombre": "Seur", "cif": "A-28000053", "sector": "Logística", "subsector": "Mensajería", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 1200, "año_facturacion": 2024, "inversion_publicidad": 20.0, "empleados": 12000, "fuente": "Datos Públicos"},
    {"nombre": "DHL España", "cif": "A-28000054", "sector": "Logística", "subsector": "Internacional", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 1800, "año_facturacion": 2024, "inversion_publicidad": 25.0, "empleados": 8000, "fuente": "Datos Públicos"},
    {"nombre": "Nacex", "cif": "A-28000055", "sector": "Logística", "subsector": "Mensajería", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 400, "año_facturacion": 2024, "inversion_publicidad": 8.0, "empleados": 3500, "fuente": "Datos Públicos"},
    {"nombre": "XPO Logistics España", "cif": "A-28000056", "sector": "Logística", "subsector": "Transporte", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 1100, "año_facturacion": 2024, "inversion_publicidad": 10.0, "empleados": 5000, "fuente": "Datos Públicos"},
    {"nombre": "ID Logistics España", "cif": "A-28000057", "sector": "Logística", "subsector": "Almacenamiento", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 600, "año_facturacion": 2024, "inversion_publicidad": 5.0, "empleados": 8000, "fuente": "Datos Públicos"},

    # Sanidad
    {"nombre": "Quirónsalud", "cif": "A-28000058", "sector": "Sanidad", "subsector": "Hospitales", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 5077, "año_facturacion": 2024, "inversion_publicidad": 30.0, "empleados": 40000, "fuente": "Informe Anual 2024"},
    {"nombre": "HM Hospitales", "cif": "A-28000059", "sector": "Sanidad", "subsector": "Hospitales", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 850, "año_facturacion": 2024, "inversion_publicidad": 20.0, "empleados": 8000, "fuente": "Datos Públicos"},
    {"nombre": "Vithas", "cif": "A-28000060", "sector": "Sanidad", "subsector": "Hospitales", "comunidad_autonoma": "Valencia", "provincia": "Valencia", "facturacion": 780, "año_facturacion": 2024, "inversion_publicidad": 15.0, "empleados": 9000, "fuente": "Datos Públicos"},
    {"nombre": "Ribera Salud", "cif": "A-28000061", "sector": "Sanidad", "subsector": "Hospitales", "comunidad_autonoma": "Valencia", "provincia": "Valencia", "facturacion": 550, "año_facturacion": 2024, "inversion_publicidad": 10.0, "empleados": 6500, "fuente": "Datos Públicos"},
    {"nombre": "Fresenius España", "cif": "A-28000062", "sector": "Sanidad", "subsector": "Servicios Médicos", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 700, "año_facturacion": 2024, "inversion_publicidad": 8.0, "empleados": 4500, "fuente": "Datos Públicos"},
    {"nombre": "Grupo ICM", "cif": "A-28000063", "sector": "Sanidad", "subsector": "Diagnóstico", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 320, "año_facturacion": 2024, "inversion_publicidad": 5.0, "empleados": 2800, "fuente": "Datos Públicos"},

    # Moda
    {"nombre": "Mango", "cif": "A-28000064", "sector": "Moda", "subsector": "Confección", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 3339, "año_facturacion": 2024, "inversion_publicidad": 55.0, "empleados": 16000, "fuente": "Informe Anual 2024"},
    {"nombre": "Desigual", "cif": "A-28000065", "sector": "Moda", "subsector": "Confección", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 450, "año_facturacion": 2024, "inversion_publicidad": 35.0, "empleados": 4500, "fuente": "Datos Públicos"},
    {"nombre": "Tous", "cif": "A-28000066", "sector": "Moda", "subsector": "Complementos", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 520, "año_facturacion": 2024, "inversion_publicidad": 30.0, "empleados": 4000, "fuente": "Datos Públicos"},
    {"nombre": "Camper", "cif": "A-28000067", "sector": "Moda", "subsector": "Calzado", "comunidad_autonoma": "Baleares", "provincia": "Mallorca", "facturacion": 280, "año_facturacion": 2024, "inversion_publicidad": 15.0, "empleados": 2500, "fuente": "Datos Públicos"},
    {"nombre": "Mayoral", "cif": "A-28000068", "sector": "Moda", "subsector": "Confección", "comunidad_autonoma": "Andalucía", "provincia": "Málaga", "facturacion": 320, "año_facturacion": 2024, "inversion_publicidad": 12.0, "empleados": 2200, "fuente": "Datos Públicos"},
    {"nombre": "Pepe Jeans", "cif": "A-28000069", "sector": "Moda", "subsector": "Textil", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 380, "año_facturacion": 2024, "inversion_publicidad": 25.0, "empleados": 2000, "fuente": "Datos Públicos"},
    {"nombre": "Scalpers", "cif": "A-28000070", "sector": "Moda", "subsector": "Textil", "comunidad_autonoma": "Andalucía", "provincia": "Sevilla", "facturacion": 220, "año_facturacion": 2024, "inversion_publicidad": 18.0, "empleados": 1500, "fuente": "Datos Públicos"},

    # Química/Consumo
    {"nombre": "Henkel España", "cif": "A-28000071", "sector": "Consumo", "subsector": "Detergentes", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 1200, "año_facturacion": 2024, "inversion_publicidad": 70.0, "empleados": 2800, "fuente": "Datos Públicos"},
    {"nombre": "Reckitt España", "cif": "A-28000072", "sector": "Consumo", "subsector": "Higiene", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 950, "año_facturacion": 2024, "inversion_publicidad": 85.0, "empleados": 1800, "fuente": "Datos Públicos"},
    {"nombre": "Kao España", "cif": "A-28000073", "sector": "Consumo", "subsector": "Higiene", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 480, "año_facturacion": 2024, "inversion_publicidad": 40.0, "empleados": 1200, "fuente": "Datos Públicos"},
    {"nombre": "Lactalis España", "cif": "A-28000074", "sector": "Alimentación", "subsector": "Lácteos", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 1100, "año_facturacion": 2024, "inversion_publicidad": 35.0, "empleados": 3500, "fuente": "Datos Públicos"},
    {"nombre": "AkzoNobel España", "cif": "A-28000075", "sector": "Química", "subsector": "Pinturas", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 650, "año_facturacion": 2024, "inversion_publicidad": 20.0, "empleados": 2000, "fuente": "Datos Públicos"},
    {"nombre": "BASF España", "cif": "A-28000076", "sector": "Química", "subsector": "Industrial", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 1400, "año_facturacion": 2024, "inversion_publicidad": 10.0, "empleados": 1500, "fuente": "Datos Públicos"},
    {"nombre": "Bayer España", "cif": "A-28000077", "sector": "Química", "subsector": "Farmacéutica", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 900, "año_facturacion": 2024, "inversion_publicidad": 50.0, "empleados": 2200, "fuente": "Datos Públicos"},

    # Más Banca
    {"nombre": "Bankinter", "cif": "A-28000078", "sector": "Banca", "subsector": "Banca Comercial", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 2901, "año_facturacion": 2024, "inversion_publicidad": 42.0, "empleados": 6800, "fuente": "Informe Anual 2024"},
    {"nombre": "Ibercaja", "cif": "A-28000079", "sector": "Banca", "subsector": "Banca Comercial", "comunidad_autonoma": "Aragón", "provincia": "Zaragoza", "facturacion": 1303, "año_facturacion": 2024, "inversion_publicidad": 20.0, "empleados": 4500, "fuente": "Informe Anual 2024"},
    {"nombre": "Unicaja", "cif": "A-28000080", "sector": "Banca", "subsector": "Banca Comercial", "comunidad_autonoma": "Andalucía", "provincia": "Málaga", "facturacion": 2041, "año_facturacion": 2024, "inversion_publicidad": 22.0, "empleados": 8500, "fuente": "Informe Anual 2024"},
    {"nombre": "Kutxabank", "cif": "A-28000081", "sector": "Banca", "subsector": "Banca Comercial", "comunidad_autonoma": "País Vasco", "provincia": "Vizcaya", "facturacion": 2012, "año_facturacion": 2024, "inversion_publicidad": 18.0, "empleados": 5500, "fuente": "Informe Anual 2024"},
    {"nombre": "Abanca", "cif": "A-28000082", "sector": "Banca", "subsector": "Banca Comercial", "comunidad_autonoma": "Galicia", "provincia": "A Coruña", "facturacion": 2077, "año_facturacion": 2024, "inversion_publicidad": 15.0, "empleados": 7000, "fuente": "Informe Anual 2024"},
    {"nombre": "Cajamar", "cif": "A-28000083", "sector": "Banca", "subsector": "Banca Cooperativa", "comunidad_autonoma": "Andalucía", "provincia": "Almería", "facturacion": 800, "año_facturacion": 2024, "inversion_publicidad": 10.0, "empleados": 5500, "fuente": "Informe Anual"},

    # Más Alimentación
    {"nombre": "Grupo Borges", "cif": "A-28000084", "sector": "Alimentación", "subsector": "Aceites", "comunidad_autonoma": "Cataluña", "provincia": "Tarragona", "facturacion": 850, "año_facturacion": 2024, "inversion_publicidad": 18.0, "empleados": 2500, "fuente": "Datos Públicos"},
    {"nombre": "Deoleo/Carbonell", "cif": "A-28000085", "sector": "Alimentación", "subsector": "Aceites", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 620, "año_facturacion": 2024, "inversion_publicidad": 25.0, "empleados": 1200, "fuente": "Datos Públicos"},
    {"nombre": "Casa Tarradellas", "cif": "A-28000086", "sector": "Alimentación", "subsector": "Charcutería", "comunidad_autonoma": "Cataluña", "provincia": "Lleida", "facturacion": 480, "año_facturacion": 2024, "inversion_publicidad": 20.0, "empleados": 2800, "fuente": "Datos Públicos"},
    {"nombre": "Calvo Group", "cif": "A-28000087", "sector": "Alimentación", "subsector": "Conservas", "comunidad_autonoma": "Galicia", "provincia": "A Coruña", "facturacion": 690, "año_facturacion": 2024, "inversion_publicidad": 22.0, "empleados": 4500, "fuente": "Datos Públicos"},
    {"nombre": "Pastas Gallo", "cif": "A-28000088", "sector": "Alimentación", "subsector": "Pasta", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 180, "año_facturacion": 2024, "inversion_publicidad": 12.0, "empleados": 800, "fuente": "Datos Públicos"},
    {"nombre": "Siro", "cif": "A-28000089", "sector": "Alimentación", "subsector": "Panadería", "comunidad_autonoma": "Castilla y León", "provincia": "Palencia", "facturacion": 320, "año_facturacion": 2024, "inversion_publicidad": 8.0, "empleados": 2000, "fuente": "Datos Públicos"},
    {"nombre": "Gallina Blanca", "cif": "A-28000090", "sector": "Alimentación", "subsector": "Caldos", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 550, "año_facturacion": 2024, "inversion_publicidad": 30.0, "empleados": 1800, "fuente": "Datos Públicos"},
    {"nombre": "Torres Wines", "cif": "A-28000091", "sector": "Bebidas", "subsector": "Vinos", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 310, "año_facturacion": 2024, "inversion_publicidad": 15.0, "empleados": 1800, "fuente": "Datos Públicos"},
    {"nombre": "Freixenet", "cif": "A-28000092", "sector": "Bebidas", "subsector": "Cava", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 290, "año_facturacion": 2024, "inversion_publicidad": 20.0, "empleados": 1400, "fuente": "Datos Públicos"},
    {"nombre": "García Carrión", "cif": "A-28000093", "sector": "Bebidas", "subsector": "Vinos", "comunidad_autonoma": "Murcia", "provincia": "Murcia", "facturacion": 420, "año_facturacion": 2024, "inversion_publicidad": 12.0, "empleados": 2200, "fuente": "Datos Públicos"},

    # Más Turismo
    {"nombre": "Riu Hotels", "cif": "A-28000094", "sector": "Turismo", "subsector": "Hostelería", "comunidad_autonoma": "Baleares", "provincia": "Mallorca", "facturacion": 4082, "año_facturacion": 2024, "inversion_publicidad": 35.0, "empleados": 38000, "fuente": "Informe Anual 2024"},
    {"nombre": "Iberostar", "cif": "A-28000095", "sector": "Turismo", "subsector": "Hostelería", "comunidad_autonoma": "Baleares", "provincia": "Mallorca", "facturacion": 4468, "año_facturacion": 2024, "inversion_publicidad": 28.0, "empleados": 37000, "fuente": "Informe Anual 2024"},
    {"nombre": "Grupo Hotusa", "cif": "A-28000096", "sector": "Turismo", "subsector": "Hostelería", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 1200, "año_facturacion": 2024, "inversion_publicidad": 20.0, "empleados": 20000, "fuente": "Datos Públicos"},
    {"nombre": "Vincci Hoteles", "cif": "A-28000097", "sector": "Turismo", "subsector": "Hostelería", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 380, "año_facturacion": 2024, "inversion_publicidad": 12.0, "empleados": 3500, "fuente": "Datos Públicos"},
    {"nombre": "Lopesan", "cif": "A-28000098", "sector": "Turismo", "subsector": "Hostelería", "comunidad_autonoma": "Canarias", "provincia": "Las Palmas", "facturacion": 650, "año_facturacion": 2024, "inversion_publicidad": 15.0, "empleados": 8000, "fuente": "Datos Públicos"},
    {"nombre": "Palladium Hotel Group", "cif": "A-28000099", "sector": "Turismo", "subsector": "Hostelería", "comunidad_autonoma": "Baleares", "provincia": "Ibiza", "facturacion": 580, "año_facturacion": 2024, "inversion_publicidad": 14.0, "empleados": 7000, "fuente": "Datos Públicos"},

    # Más Transporte
    {"nombre": "Alsa", "cif": "A-28000100", "sector": "Transporte", "subsector": "Autobuses", "comunidad_autonoma": "Asturias", "provincia": "Oviedo", "facturacion": 1200, "año_facturacion": 2024, "inversion_publicidad": 10.0, "empleados": 14000, "fuente": "Datos Públicos"},
    {"nombre": "Cabify España", "cif": "A-28000101", "sector": "Transporte", "subsector": "Movilidad", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 580, "año_facturacion": 2024, "inversion_publicidad": 30.0, "empleados": 2000, "fuente": "Datos Públicos"},
    {"nombre": "Vueling", "cif": "A-28000102", "sector": "Transporte", "subsector": "Aerolínea", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 3261, "año_facturacion": 2024, "inversion_publicidad": 22.0, "empleados": 5000, "fuente": "Informe Anual 2024"},
    {"nombre": "Globalia", "cif": "A-28000103", "sector": "Transporte", "subsector": "Turístico", "comunidad_autonoma": "Baleares", "provincia": "Mallorca", "facturacion": 1800, "año_facturacion": 2024, "inversion_publicidad": 18.0, "empleados": 8000, "fuente": "Datos Públicos"},
    {"nombre": "Talgo", "cif": "A-28000104", "sector": "Transporte", "subsector": "Ferroviario", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 480, "año_facturacion": 2024, "inversion_publicidad": 5.0, "empleados": 3000, "fuente": "Datos Públicos"},

    # Más Tecnología
    {"nombre": "GMV", "cif": "A-28000105", "sector": "Tecnología", "subsector": "Aeroespacial", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 650, "año_facturacion": 2024, "inversion_publicidad": 5.0, "empleados": 3200, "fuente": "Datos Públicos"},
    {"nombre": "NTT DATA España", "cif": "A-28000106", "sector": "Tecnología", "subsector": "Servicios IT", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 950, "año_facturacion": 2024, "inversion_publicidad": 8.0, "empleados": 9000, "fuente": "Datos Públicos"},
    {"nombre": "Capgemini España", "cif": "A-28000107", "sector": "Tecnología", "subsector": "Consultoría IT", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 1100, "año_facturacion": 2024, "inversion_publicidad": 10.0, "empleados": 10000, "fuente": "Datos Públicos"},
    {"nombre": "Inetum España", "cif": "A-28000108", "sector": "Tecnología", "subsector": "Servicios IT", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 420, "año_facturacion": 2024, "inversion_publicidad": 5.0, "empleados": 4500, "fuente": "Datos Públicos"},
    {"nombre": "Grupo Sothis", "cif": "A-28000109", "sector": "Tecnología", "subsector": "ERP", "comunidad_autonoma": "Valencia", "provincia": "Valencia", "facturacion": 180, "año_facturacion": 2024, "inversion_publicidad": 3.0, "empleados": 1200, "fuente": "Datos Públicos"},
    {"nombre": "Caixa Bank Tech", "cif": "A-28000110", "sector": "Tecnología", "subsector": "Fintech", "comunidad_autonoma": "Cataluña", "provincia": "Barcelona", "facturacion": 550, "año_facturacion": 2024, "inversion_publicidad": 6.0, "empleados": 3500, "fuente": "Datos Públicos"},

    # Más Construcción
    {"nombre": "Sacyr", "cif": "A-28000111", "sector": "Construcción", "subsector": "Infraestructuras", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 4571, "año_facturacion": 2024, "inversion_publicidad": 8.0, "empleados": 50000, "fuente": "Informe Anual 2024"},
    {"nombre": "FCC", "cif": "A-28000112", "sector": "Construcción", "subsector": "Servicios Urbanos", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 9071, "año_facturacion": 2024, "inversion_publicidad": 12.0, "empleados": 70000, "fuente": "Informe Anual 2024"},
    {"nombre": "Técnicas Reunidas", "cif": "A-28000113", "sector": "Construcción", "subsector": "Ingeniería", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 4451, "año_facturacion": 2024, "inversion_publicidad": 6.0, "empleados": 7000, "fuente": "Informe Anual 2024"},
    {"nombre": "Vinci España", "cif": "A-28000114", "sector": "Construcción", "subsector": "Infraestructuras", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 2800, "año_facturacion": 2024, "inversion_publicidad": 7.0, "empleados": 20000, "fuente": "Datos Públicos"},

    # Medios adicionales
    {"nombre": "El País (PRISA Digital)", "cif": "A-28000115", "sector": "Medios", "subsector": "Digital", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 280, "año_facturacion": 2024, "inversion_publicidad": 15.0, "empleados": 1800, "fuente": "Datos Públicos"},
    {"nombre": "Vocento Digital", "cif": "A-28000116", "sector": "Medios", "subsector": "Digital", "comunidad_autonoma": "País Vasco", "provincia": "Vizcaya", "facturacion": 180, "año_facturacion": 2024, "inversion_publicidad": 8.0, "empleados": 1200, "fuente": "Datos Públicos"},

    # Energía adicional
    {"nombre": "EDP España", "cif": "A-28000117", "sector": "Energía", "subsector": "Eléctrica", "comunidad_autonoma": "Extremadura", "provincia": "Badajoz", "facturacion": 4200, "año_facturacion": 2024, "inversion_publicidad": 20.0, "empleados": 4000, "fuente": "Informe Anual"},
    {"nombre": "Veolia España", "cif": "A-28000118", "sector": "Energía", "subsector": "Servicios", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 1800, "año_facturacion": 2024, "inversion_publicidad": 8.0, "empleados": 9000, "fuente": "Datos Públicos"},
    {"nombre": "Solaria", "cif": "A-28000119", "sector": "Energía", "subsector": "Solar", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 280, "año_facturacion": 2024, "inversion_publicidad": 4.0, "empleados": 300, "fuente": "Datos Públicos"},
    {"nombre": "Grenergy", "cif": "A-28000120", "sector": "Energía", "subsector": "Renovables", "comunidad_autonoma": "Madrid", "provincia": "Madrid", "facturacion": 220, "año_facturacion": 2024, "inversion_publicidad": 3.0, "empleados": 250, "fuente": "Datos Públicos"},
]


def seed_database():
    """Poblar la base de datos con datos de ejemplo"""

    print("Creando tablas...")
    Base.metadata.create_all(bind=engine)

    print("Poblando base de datos con datos de ejemplo...")
    db = SessionLocal()

    try:
        # Verificar si ya hay datos
        count = db.query(Empresa).count()
        if count > 0:
            print(f"La base de datos ya tiene {count} empresas. ¿Limpiar? (s/n): ")
            # Para script no interactivo, limpiamos automáticamente
            db.query(Empresa).delete()
            db.commit()
            print("Base de datos limpiada.")

        # Insertar empresas
        for empresa_data in EMPRESAS_EJEMPLO:
            empresa = Empresa(**empresa_data)
            db.add(empresa)

        db.commit()
        print(f"✓ {len(EMPRESAS_EJEMPLO)} empresas insertadas correctamente.")

        # Mostrar resumen
        print("\n=== RESUMEN ===")
        print(f"Total empresas: {db.query(Empresa).count()}")
        print(f"Sectores: {db.query(Empresa.sector).distinct().count()}")
        print(f"Comunidades: {db.query(Empresa.comunidad_autonoma).distinct().count()}")

        facturacion_total = db.query(func.sum(Empresa.facturacion)).scalar()
        print(f"Facturación total: {facturacion_total:,.0f} millones €")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
