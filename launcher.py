#!/usr/bin/env python3
"""Launch Streamlit in a background thread and open a PyWebview window."""

from __future__ import annotations

import atexit
import socket
import subprocess
import sys
import threading
import time
from typing import Optional

HOST = "127.0.0.1"
PORT = 8501
STREAMLIT_SCRIPT = "ElectroGalindez.py"


class StreamlitLauncherError(RuntimeError):
    """Raised when the Streamlit launcher cannot start."""


def is_port_open(host: str, port: int) -> bool:
    """Return True if the given host/port is accepting TCP connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def wait_for_port(host: str, port: int, timeout_s: float = 30.0) -> bool:
    """Wait until a TCP port is open or timeout expires."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if is_port_open(host, port):
            return True
        time.sleep(0.3)
    return False


def start_streamlit() -> subprocess.Popen:
    """Start Streamlit as a subprocess."""
    command = [
        sys.executable,
        "-m",
        "streamlit.web.cli",
        "run",
        STREAMLIT_SCRIPT,
    ]
    return subprocess.Popen(command)


def main() -> None:
    if is_port_open(HOST, PORT):
        raise StreamlitLauncherError(
            f"El puerto {PORT} ya está en uso. Cierra la app que lo ocupa o cambia el puerto."
        )

    try:
        import webview  # noqa: WPS433 (runtime import for optional dependency)
    except ImportError as exc:
        raise StreamlitLauncherError(
            "No se encontró pywebview. Instala dependencias con: pip install pywebview"
        ) from exc

    process: Optional[subprocess.Popen] = None

    def start_server() -> None:
        nonlocal process
        process = start_streamlit()

    thread = threading.Thread(target=start_server, daemon=True)
    thread.start()

    if not wait_for_port(HOST, PORT, timeout_s=45.0):
        raise StreamlitLauncherError(
            "Streamlit no inició a tiempo. Revisa el script y la salida de la consola."
        )

    def cleanup() -> None:
        if process and process.poll() is None:
            process.terminate()

    atexit.register(cleanup)

    webview.create_window(
        "ElectroGalindez",
        f"http://{HOST}:{PORT}",
        width=1280,
        height=800,
    )
    webview.start()


if __name__ == "__main__":
    try:
        main()
    except StreamlitLauncherError as exc:
        print(f"[launcher] Error: {exc}", file=sys.stderr)
        sys.exit(1)
