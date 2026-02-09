import subprocess
import webview
import threading
import time
import sys
import socket

STREAMLIT_APP = "ElectroGalindez.py"
PORT = 8501

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0

def start_streamlit():
    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            STREAMLIT_APP,
            "--server.port",
            str(PORT),
            "--server.headless",
            "true",
        ]
    )

threading.Thread(target=start_streamlit, daemon=True).start()

while not is_port_open(PORT):
    time.sleep(0.2)

webview.create_window(
    "ElectroGalindez Contabilidad",
    f"http://localhost:{PORT}",
    width=1200,
    height=800,
)

webview.start()
