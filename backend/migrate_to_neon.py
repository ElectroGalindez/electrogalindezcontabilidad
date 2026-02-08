"""Utility script to migrate the schema to a Neon/PostgreSQL database."""

from __future__ import annotations

import os

import psycopg2
from dotenv import load_dotenv

SCHEMA_SQL = """
-- Tabla de clientes
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    telefono VARCHAR(50),
    ci VARCHAR(50),
    chapa VARCHAR(50)
);

-- Tabla de productos
CREATE TABLE IF NOT EXISTS productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    precio NUMERIC(10,2) NOT NULL,
    cantidad INT NOT NULL
);

-- Tabla de ventas
CREATE TABLE IF NOT EXISTS ventas (
    id SERIAL PRIMARY KEY,
    cliente_id INT REFERENCES clientes(id),
    total NUMERIC(10,2) NOT NULL,
    pagado NUMERIC(10,2) NOT NULL,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tipo_pago VARCHAR(50)
);

-- Tabla de productos vendidos en cada venta
CREATE TABLE IF NOT EXISTS productos_vendidos (
    id SERIAL PRIMARY KEY,
    venta_id INT REFERENCES ventas(id) ON DELETE CASCADE,
    producto_id INT REFERENCES productos(id),
    cantidad INT NOT NULL,
    precio_unitario NUMERIC(10,2) NOT NULL,
    subtotal NUMERIC(10,2) NOT NULL,
    saldo NUMERIC(10,2) DEFAULT 0
);

-- Tabla de deudas
CREATE TABLE IF NOT EXISTS deudas (
    id SERIAL PRIMARY KEY,
    cliente_id INT REFERENCES clientes(id),
    venta_id INT REFERENCES ventas(id),
    monto_total NUMERIC(10,2) NOT NULL,
    estado VARCHAR(50) DEFAULT 'pendiente'
);
"""


def migrate_schema(database_url: str) -> None:
    """Apply the schema to a PostgreSQL database."""
    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
            conn.commit()


def main() -> None:
    """Load env vars and run the schema migration."""
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL no está configurada en el entorno.")

    try:
        migrate_schema(database_url)
        print("✅ Esquema migrado correctamente a Neon")
    except Exception as exc:
        print("❌ Error al migrar:", exc)
        raise


if __name__ == "__main__":
    main()
