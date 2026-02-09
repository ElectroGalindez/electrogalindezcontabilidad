#!/usr/bin/env python3
"""Launch Streamlit in a background thread and open a PyWebview window."""

from __future__ import annotations

import atexit
import logging
import os
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Optional
from urllib.error import URLError
from urllib.request import urlopen

HOST = "127.0.0.1"
PORT = 8501
STREAMLIT_SCRIPT = "ElectroGalindez.py"
HEALTH_ENDPOINT = "/_stcore/health"


class StreamlitLauncherError(RuntimeError):
    """Raised when the Streamlit launcher cannot start."""


def is_port_open(host: str, port: int) -> bool:
    """Return True if the given host/port is accepting TCP connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def get_base_path() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def configure_runtime(base_path: Path) -> None:
    if str(base_path) not in sys.path:
        sys.path.insert(0, str(base_path))
    os.chdir(base_path)
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")


def setup_logging(base_path: Path) -> Path:
    log_dir = Path.home() / ".electrogalindez" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "launcher.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ],
    )
    logging.info("Base path: %s", base_path)
    logging.info("Log file: %s", log_file)
    return log_file


def start_streamlit(script_path: Path, host: str, port: int) -> tuple[threading.Thread, dict]:
    """Start Streamlit in a background thread."""
    from streamlit.web import bootstrap

    state: dict[str, Optional[BaseException]] = {"error": None}

    def _run() -> None:
        try:
            bootstrap.run(
                str(script_path),
                False,
                [],
                {
                    "server.headless": True,
                    "server.port": port,
                    "server.address": host,
                },
            )
        except BaseException as exc:  # pragma: no cover - defensive logging
            state["error"] = exc
            logging.exception("Streamlit failed to start.")

    thread = threading.Thread(target=_run, name="streamlit", daemon=True)
    thread.start()
    return thread, state


def wait_for_streamlit(host: str, port: int, state: dict, timeout_s: float = 45.0) -> None:
    deadline = time.time() + timeout_s
    health_url = f"http://{host}:{port}{HEALTH_ENDPOINT}"
    while time.time() < deadline:
        if state.get("error") is not None:
            raise StreamlitLauncherError("Streamlit falló al iniciar. Revisa launcher.log.")
        try:
            with urlopen(health_url, timeout=1) as response:
                if response.status == 200:
                    return
        except URLError:
            pass
        time.sleep(0.3)
    if is_port_open(host, port):
        return
    raise StreamlitLauncherError(
        "Streamlit no inició a tiempo. Revisa launcher.log para más detalles."
    )


def main() -> None:
    base_path = get_base_path()
    configure_runtime(base_path)
    setup_logging(base_path)

    script_path = base_path / STREAMLIT_SCRIPT
    if not script_path.exists():
        raise StreamlitLauncherError(f"No se encontró {script_path}.")

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

    process: Optional[threading.Thread] = None
    thread, state = start_streamlit(script_path, HOST, PORT)
    process = thread
    wait_for_streamlit(HOST, PORT, state, timeout_s=60.0)

    def cleanup() -> None:
        if process and process.is_alive():
            logging.info("Cerrando Streamlit.")

    atexit.register(cleanup)

    webview.create_window(
        "ElectroGalindez",
        f"http://{HOST}:{PORT}",
        width=1280,
        height=800,
    )
    logging.info("Abriendo PyWebview.")
    webview.start()


if __name__ == "__main__":
    try:
        main()
    except StreamlitLauncherError as exc:
        print(f"[launcher] Error: {exc}", file=sys.stderr)
        sys.exit(1)
