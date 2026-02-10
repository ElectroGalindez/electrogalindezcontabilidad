import streamlit as st
from sqlalchemy.exc import OperationalError
from backend.errors import (
    AppError,
    DatabaseConnectionError
)


def handle_app_error(e: Exception):
    # Error de conexión BD
    if isinstance(e, (OperationalError, DatabaseConnectionError)):
        st.error("❌ Error 404 – Sin conexión con la base de datos")
        st.info("📡 No se pudo conectar al servidor de datos. Intenta más tarde.")
        st.stop()

    # Errores controlados
    if isinstance(e, AppError):
        st.warning(f"⚠️ {str(e)}")
        st.stop()

    # Error inesperado
    st.error("💥 Error inesperado")
    st.exception(e)
    st.stop()
