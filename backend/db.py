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
# Normalizar y validar la URL
# ---------------------------
import re
from sqlalchemy.engine import make_url


def _normalizar_url(url):
    """Limpia variantes de pegado: espacios, comillas, prefijo psql, esquema postgres://."""
    url = url.strip()
    # "postgresql://..." pegado con comillas dentro del valor
    if len(url) > 1 and url[0] == url[-1] and url[0] in "\"'":
        url = url[1:-1].strip()
    # Comandos pegados: psql 'postgresql://...' o PGPASSWORD=... psql postgresql://...
    url = re.sub(r"^psql\s+", "", url)
    url = re.sub(r"^.*?(postgresql(?:s)?(?:\+[a-z0-9]+)?://)", r"\1", url)
    # Comillas que envolvian al comando completo
    url = url.strip().strip("'\"")
    # Esquemas alternativos
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


def _diagnostico(url):
    """Describe la estructura del secreto SIN revelar usuario ni contraseña."""
    partes = []
    if not re.match(r"^postgresql(\+[a-z0-9]+)?://", url):
        partes.append("no empieza por postgresql://")
    if "@" not in url:
        partes.append("falta el '@' entre contraseña y host")
    else:
        credenciales = url.split("://", 1)[-1].split("@", 1)[0]
        if ":" not in credenciales:
            partes.append("falta ':' entre usuario y contraseña")
        elif not credenciales.split(":", 1)[1]:
            partes.append("la contraseña está vacía")
    if url.count("@") > 1:
        partes.append("hay varios '@' (cifra la contraseña con %40)")
    if any(c.isspace() for c in url):
        partes.append("tiene espacios o saltos de línea")
    if "'" in url or '"' in url:
        partes.append("tiene comillas dentro del valor")
    if "#" in url:
        partes.append("tiene '#', que en TOML inicia comentario (cifra con %23)")
    if not partes:
        partes.append("el formato parece correcto; revisa que el secreto no tenga otro formato")
    return partes


if DATABASE_URL:
    DATABASE_URL = _normalizar_url(DATABASE_URL)
    try:
        make_url(DATABASE_URL)
    except Exception:
        raise ValueError(
            "NEON_DATABASE_URL está presente pero no es una URL válida.\n"
            "Problemas detectados: " + "; ".join(_diagnostico(DATABASE_URL)) + "\n"
            "Valor esperado: postgresql://USUARIO:CONTRASENA@HOST/neondb?sslmode=require\n"
            "En Streamlit Cloud va en Settings -> Secrets, así:\n"
            '  NEON_DATABASE_URL = "postgresql://USUARIO:CONTRASENA@HOST/neondb?sslmode=require"'
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
