# backend/db.py
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Reemplaza esta URL con la tuya de Neon
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://usuario:contraseña@host:puerto/dbname")

def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
