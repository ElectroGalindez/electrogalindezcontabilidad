#!/usr/bin/env python3
"""Launcher de ElectroGalindez: Streamlit en background + ventana PyWebview."""

import atexit
import socket
import subprocess
import sys
import threading
import time
from typing import Optional

# ===================== CONFIGURACIÓN =====================
HOST = "127.0.0.1"
PORT = 8501
STREAMLIT_SCRIPT = "ElectroGalindez.py"
WINDOW_TITLE = "ElectroGalindez Contabilidad"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
# ==========================================================


class StreamlitLauncherError(RuntimeError):
    """Error al lanzar Streamlit."""


def is_port_open(host: str, port: int) -> bool:
    """Retorna True si el host/puerto está disponible."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def wait_for_port(host: str, port: int, timeout_s: float = 30.0) -> bool:
    """Espera hasta que el puerto TCP esté abierto o expire el timeout."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if is_port_open(host, port):
            return True
        time.sleep(0.3)
    return False


def start_streamlit() -> subprocess.Popen:
    """Arranca Streamlit como subprocess."""
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        STREAMLIT_SCRIPT,
        "--server.headless",
        "true",           # evita abrir navegador
        "--server.enableCORS",
        "false",
    ]
    return subprocess.Popen(command)


def main() -> None:
    if is_port_open(HOST, PORT):
        raise StreamlitLauncherError(
            f"El puerto {PORT} ya está en uso. Cierra la app que lo ocupe o cambia el puerto en la configuración."
        )

    try:
        import webview  # noqa: WPS433 (runtime import)
    except ImportError as exc:
        raise StreamlitLauncherError(
            "No se encontró pywebview. Instala dependencias con: pip install pywebview"
        ) from exc

    process: Optional[subprocess.Popen] = None

    # Arranca Streamlit en un hilo de fondo
    def start_server() -> None:
        nonlocal process
        process = start_streamlit()

    thread = threading.Thread(target=start_server, daemon=True)
    thread.start()

    # Espera a que Streamlit abra el puerto
    if not wait_for_port(HOST, PORT, timeout_s=45.0):
        raise StreamlitLauncherError(
            f"Streamlit no inició en {PORT}. Revisa ElectroGalindez.py o el entorno."
        )

    # Asegura que Streamlit se cierre al salir
    def cleanup() -> None:
        if process and process.poll() is None:
            process.terminate()

    atexit.register(cleanup)

    # Crea la ventana PyWebview
    webview.create_window(
        WINDOW_TITLE,
        f"http://{HOST}:{PORT}",
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
    )
    webview.start()


if __name__ == "__main__":
    try:
        main()
    except StreamlitLauncherError as exc:
        print(f"[launcher] Error: {exc}", file=sys.stderr)
        sys.exit(1)
