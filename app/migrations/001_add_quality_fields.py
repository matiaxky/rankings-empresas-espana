"""
Migración 001: Añadir campos de calidad de datos a la tabla empresas.

Campos nuevos:
  - data_quality_score     (FLOAT,    default 0.0)
  - fuente_publicidad      (VARCHAR,  nullable)
  - fecha_ultima_actualizacion (DATETIME, nullable)

Es idempotente: si las columnas ya existen en SQLite, no falla; simplemente
las omite. No borra datos existentes.

Uso:
    python3 app/migrations/001_add_quality_fields.py
"""

import os
import sqlite3
import sys


def _db_path() -> str:
    """Devuelve la ruta al fichero SQLite (relativa al cwd del proyecto)."""
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(here, "..", ".."))
    return os.path.join(project_root, "empresas.db")


def _existing_columns(conn: sqlite3.Connection, table: str) -> set:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}


def run(db_path: str | None = None) -> dict:
    db_path = db_path or _db_path()

    if not os.path.exists(db_path):
        print(f"[migrations/001] ⚠️  La BD no existe en {db_path}. "
              f"Se creará al arrancar la app; esta migración se omite.")
        return {"skipped": True, "added": []}

    conn = sqlite3.connect(db_path)
    try:
        cols = _existing_columns(conn, "empresas")
        if not cols:
            print("[migrations/001] ⚠️  La tabla 'empresas' no existe aún; se omite.")
            return {"skipped": True, "added": []}

        planned = [
            ("data_quality_score",          "FLOAT DEFAULT 0.0"),
            ("fuente_publicidad",           "VARCHAR"),
            ("fecha_ultima_actualizacion",  "DATETIME"),
        ]

        added = []
        for name, decl in planned:
            if name in cols:
                print(f"[migrations/001] ✓ Columna '{name}' ya existe — skip")
                continue
            sql = f"ALTER TABLE empresas ADD COLUMN {name} {decl}"
            try:
                conn.execute(sql)
                added.append(name)
                print(f"[migrations/001] + Añadida columna '{name}'")
            except sqlite3.OperationalError as e:
                # "duplicate column name" => carrera / re-ejecución: ignorar
                if "duplicate column" in str(e).lower():
                    print(f"[migrations/001] ✓ Columna '{name}' ya existía (race) — skip")
                else:
                    raise
        conn.commit()
        print(f"[migrations/001] ✅ Migración completada. Columnas añadidas: {added or 'ninguna'}")
        return {"skipped": False, "added": added}
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        result = run()
        sys.exit(0 if not result.get("error") else 1)
    except Exception as e:
        print(f"[migrations/001] ❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
