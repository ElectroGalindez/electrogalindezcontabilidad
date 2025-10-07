# 0_Login.py
import streamlit as st
from backend.usuarios import autenticar_usuario
from datetime import datetime

st.set_page_config(page_title="Login | ElectroGalíndez", layout="centered")

# Inicializar sesión
if "usuario" not in st.session_state:
    st.session_state.usuario = None

# Usuario ya logueado
if st.session_state.usuario:
    usuario = st.session_state.usuario
    st.sidebar.write(f"👤 Usuario: {usuario['username']}")
    st.sidebar.write(f"Rol: {usuario['rol']}")

    st.success(f"Bienvenido, {usuario['username']} ({usuario['rol']})")
    if st.button("Cerrar sesión"):
        st.session_state.usuario = None
        st.status()

# Usuario no logueado
else:
    st.title("🔒 Iniciar sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar"):
        user = autenticar_usuario(username, password)
        if isinstance(user, dict) and user.get("bloqueado"):
            try:
                bloqueado_hasta = datetime.fromisoformat(user['bloqueado_hasta'])
                st.error(f"Usuario bloqueado hasta {bloqueado_hasta.strftime('%Y-%m-%d %H:%M')}")
            except:
                st.error("Usuario bloqueado. Intenta más tarde.")
        elif user:
            st.session_state.usuario = user
            st.success(f"Bienvenido, {user['username']} ({user['rol']})")
            st.status()
        else:
            st.error("Usuario o contraseña incorrectos")
