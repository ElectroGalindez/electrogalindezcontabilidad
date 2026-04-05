import webview
import threading
import subprocess
import time
import sys
import os

PORT = 8501

def resource_path(relative_path):
    """Obtener ruta compatible con PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def start_streamlit():
    app_path = resource_path("ElectroGalindez.py")

    subprocess.Popen([
        sys.executable, "-m", "streamlit", "run",
        app_path,
        "--server.port", str(PORT),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ])

def main():
    t = threading.Thread(target=start_streamlit)
    t.daemon = True
    t.start()

    time.sleep(5)

    webview.create_window(
        "Sistema ElectroGalíndez",
        f"http://localhost:{PORT}",
        width=1200,
        height=800
    )

    webview.start()

if __name__ == "__main__":
    main()