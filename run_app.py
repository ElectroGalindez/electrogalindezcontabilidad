from __future__ import annotations

import os
import socket
import sys
import threading
import time
from pathlib import Path

import webview


def _get_base_path() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def _prepare_runtime(base_path: Path) -> None:
    if str(base_path) not in sys.path:
        sys.path.insert(0, str(base_path))
    os.chdir(base_path)
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")


def _wait_for_port(host: str, port: int, timeout: int = 30) -> None:
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.2)
    raise RuntimeError(f"Streamlit no respondió en {timeout}s (puerto {port}).")


def _start_streamlit(script_path: Path, host: str, port: int) -> None:
    from streamlit.web import bootstrap

    def _run() -> None:
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

    thread = threading.Thread(target=_run, name="streamlit", daemon=True)
    thread.start()


def main() -> None:
    base_path = _get_base_path()
    _prepare_runtime(base_path)

    script_path = base_path / "ElectroGalindez.py"
    if not script_path.exists():
        raise FileNotFoundError(f"No se encontró la app Streamlit en {script_path}.")

    host = "127.0.0.1"
    port = 8501

    _start_streamlit(script_path, host, port)
    _wait_for_port(host, port)

    window = webview.create_window(
        "ElectroGalíndez - Contabilidad",
        f"http://{host}:{port}",
        width=1200,
        height=800,
    )

    def on_closed() -> None:
        os._exit(0)

    window.events.closed += on_closed
    webview.start()


if __name__ == "__main__":
    main()
