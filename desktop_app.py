import os
import socket
import subprocess
import sys
import time
import webview


def wait_for_port(host: str, port: int, timeout: int = 30) -> None:
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.2)
    raise RuntimeError(f"Streamlit no respondió en {timeout}s (puerto {port}).")


def start_streamlit() -> subprocess.Popen:
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "ElectroGalindez.py",
        "--server.headless=true",
        "--server.port=8501",
        "--server.address=127.0.0.1",
    ]
    env = os.environ.copy()
    env.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    return subprocess.Popen(cmd, cwd=os.path.dirname(__file__), env=env)


def main() -> None:
    process = start_streamlit()
    try:
        wait_for_port("127.0.0.1", 8501)
        window = webview.create_window(
            "ElectroGalíndez - Contabilidad",
            "http://127.0.0.1:8501",
            width=1200,
            height=800,
        )

        def on_closed() -> None:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

        window.events.closed += on_closed
        webview.start()
    finally:
        if process.poll() is None:
            process.terminate()


if __name__ == "__main__":
    main()
