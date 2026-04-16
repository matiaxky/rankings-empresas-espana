#!/usr/bin/env python3
"""
Script principal para iniciar el servidor de Rankings de Empresas España
"""

import subprocess
import sys
import os


def main():
    print("=" * 50)
    print("📊 Rankings Empresas España")
    print("=" * 50)

    # Inicializar BD si no existe (la BD está en la raíz del proyecto)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    db_path = "empresas.db"
    if not os.path.exists(db_path):
        print("\n📦 Inicializando base de datos...")
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app.seed import seed_database
        seed_database()
    else:
        print("\n✓ Base de datos encontrada")

    print("\n🚀 Iniciando servidor...")
    print("\n🌐 Accede a: http://localhost:8000")
    print("\n📡 API Docs: http://localhost:8000/docs")
    print("\nPresiona Ctrl+C para detener\n")

    # Iniciar uvicorn
    subprocess.run([sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"])


if __name__ == "__main__":
    main()
