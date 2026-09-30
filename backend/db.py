import os
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from contextlib import contextmanager

# ---------------------------
# Cargar credenciales
# ---------------------------
# 1) Archivo .env en la raíz del proyecto (uso local)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path)

# 2) Secrets de Streamlit (Streamlit Community Cloud / Codespaces).
#    Se define NEON_DATABASE_URL en Settings -> Secrets del proyecto.
def _from_streamlit_secrets():
    try:
        import streamlit as st
        return st.secrets.get("NEON_DATABASE_URL")
    except Exception:
        return None


DATABASE_URL = os.getenv("NEON_DATABASE_URL") or _from_streamlit_secrets()

if not DATABASE_URL:
    raise ValueError(
        "No se encontró NEON_DATABASE_URL.\n"
        "Para uso local: copia .env.example a .env y pon tus credenciales ->  cp .env.example .env\n"
        "Para Streamlit Cloud: define el secreto NEON_DATABASE_URL en Settings -> Secrets."
    )

# ---------------------------
# Motor y sesión
# ---------------------------
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Objeto MetaData global
metadata = MetaData()

# ---------------------------
# Context manager para conexión
# ---------------------------
@contextmanager
def get_connection():
    """
    Devuelve una sesión de SQLAlchemy (context manager).
    Uso:
       with get_connection() as session:  
           session.execute(...)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# ---------------------------
# Función de prueba
# ---------------------------
def test_connection():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT NOW()"))
        print("Conexión exitosa ✅", result.scalar())

if __name__ == "__main__":
    test_connection()
