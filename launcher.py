#!/usr/bin/env python3
"""Launch Streamlit in a background process and open a PyWebview window."""

from __future__ import annotations

import atexit
import logging
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

HOST = "127.0.0.1"
PORT = 8501
LOCK_PORT = 8502
STREAMLIT_SCRIPT = "ElectroGalindez.py"
APP_TITLE = "ElectroGalindez"


class StreamlitLauncherError(RuntimeError):
    """Raised when the Streamlit launcher cannot start."""


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def base_path() -> Path:
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


def resource_path(relative: str) -> Path:
    return base_path() / relative


def init_logging() -> Path:
    log_dir = Path.home() / f".{APP_TITLE.lower()}"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "launcher.log"
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    return log_path


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


def acquire_single_instance_lock() -> socket.socket:
    """Prevent multiple instances by binding to a local lock port."""
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        lock_socket.bind((HOST, LOCK_PORT))
        lock_socket.listen(1)
    except OSError as exc:
        lock_socket.close()
        raise StreamlitLauncherError(
            "La aplicación ya está en ejecución. Cierra la ventana abierta antes de iniciar otra."
        ) from exc
    return lock_socket


def build_streamlit_command(script_path: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "streamlit.web.cli",
        "run",
        str(script_path),
        "--server.headless",
        "true",
        "--server.address",
        HOST,
        "--server.port",
        str(PORT),
        "--server.fileWatcherType",
        "none",
        "--server.runOnSave",
        "false",
        "--browser.gatherUsageStats",
        "false",
    ]


def start_streamlit(log_path: Path) -> subprocess.Popen:
    """Start Streamlit as a subprocess."""
    script_path = resource_path(STREAMLIT_SCRIPT)
    if not script_path.exists():
        raise StreamlitLauncherError(
            f"No se encontró el archivo principal de Streamlit: {script_path}"
        )

    env = os.environ.copy()
    env["APP_BASE_DIR"] = str(base_path())
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    log_file = open(log_path, "a", encoding="utf-8")
    return subprocess.Popen(
        build_streamlit_command(script_path),
        stdout=log_file,
        stderr=log_file,
        env=env,
    )


def show_error(message: str) -> None:
    try:
        import tkinter  # noqa: WPS433
        from tkinter import messagebox  # noqa: WPS433

        root = tkinter.Tk()
        root.withdraw()
        messagebox.showerror(APP_TITLE, message)
        root.destroy()
    except Exception:  # pragma: no cover - fallback when tkinter is missing
        print(f"[{APP_TITLE}] Error: {message}", file=sys.stderr)


def main() -> None:
    log_path = init_logging()
    logging.info("Iniciando launcher")

    lock_socket = acquire_single_instance_lock()

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
        process = start_streamlit(log_path)

    thread = threading.Thread(target=start_server, daemon=True)
    thread.start()

    if not wait_for_port(HOST, PORT, timeout_s=45.0):
        raise StreamlitLauncherError(
            "Streamlit no inició a tiempo. Revisa el archivo launcher.log para más detalles."
        )

    def cleanup() -> None:
        if process and process.poll() is None:
            process.terminate()
        lock_socket.close()

    atexit.register(cleanup)

    webview.create_window(
        APP_TITLE,
        f"http://{HOST}:{PORT}",
        width=1280,
        height=800,
        resizable=True,
    )
    webview.start()


if __name__ == "__main__":
    try:
        main()
    except StreamlitLauncherError as exc:
        show_error(str(exc))
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - unexpected failure
        show_error(f"Error inesperado al iniciar la aplicación: {exc}")
        sys.exit(1)
