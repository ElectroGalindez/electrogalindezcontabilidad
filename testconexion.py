import os

import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")
if NEON_DATABASE_URL:
    NEON_DATABASE_URL = NEON_DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")

def test_connection():
    if not NEON_DATABASE_URL:
        print("❌ No se encontro NEON_DATABASE_URL en el archivo .env")
        return
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(NEON_DATABASE_URL)
        cursor = conn.cursor()
        
        # Ejecutar un SELECT simple
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()
        print("✅ Conexión exitosa a Neon PostgreSQL")
        print("⏰ Hora actual en la base de datos:", result[0])
        
        # Cerrar cursor y conexión
        cursor.close()
        conn.close()
        
    except OperationalError as e:
        print("❌ Error al conectar a Neon:", e)
    except Exception as e:
        print("❌ Error inesperado:", e)

if __name__ == "__main__":
    test_connection()
