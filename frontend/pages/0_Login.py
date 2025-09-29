import streamlit as st
from backend.usuarios import autenticar_usuario

st.set_page_config(page_title="Login | ElectroGalíndez", layout="centered")
st.markdown("""
<style>
.titulo-login {font-size:2em; font-weight:bold; color:#2c3e50; margin-bottom:0.5em;}
.stButton>button {background-color:#2980b9; color:white; font-weight:bold; border-radius:6px;}
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="titulo-login">🔒 Iniciar sesión</div>', unsafe_allow_html=True)

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario:
    st.success(f"Bienvenido, {st.session_state.usuario['username']} ({st.session_state.usuario['rol']})")
    st.button("Cerrar sesión", on_click=lambda: st.session_state.update({"usuario": None}))
else:
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        user = autenticar_usuario(username, password)
        if user:
            st.session_state.usuario = user
            st.success(f"Bienvenido, {user['username']} ({user['rol']})")
            st.experimental_rerun()
        else:
            st.error("Usuario o contraseña incorrectos")
