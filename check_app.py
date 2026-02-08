import sys
import time
from pathlib import Path
from subprocess import DEVNULL, Popen
from urllib.error import URLError
from urllib.request import urlopen


def find_executable() -> Path:
    executable_name = "ElectroGalindez.exe" if sys.platform == "win32" else "ElectroGalindez"
    candidates = [
        Path("dist") / executable_name,
        Path(executable_name),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"No se encontró el ejecutable '{executable_name}' en {', '.join(str(c) for c in candidates)}"
    )


def wait_for_streamlit(url: str, timeout_s: int = 60, interval_s: float = 1.0) -> int:
    start_time = time.time()
    while time.time() - start_time < timeout_s:
        try:
            with urlopen(url, timeout=5) as response:
                return response.getcode()
        except URLError:
            time.sleep(interval_s)
    raise TimeoutError(f"No se pudo conectar a {url} después de {timeout_s} segundos.")


def terminate_process(process: Popen) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except Exception:
        process.kill()


def main() -> int:
    url = "http://localhost:8501"
    process = None
    try:
        executable_path = find_executable()
        process = Popen([str(executable_path)], stdout=DEVNULL, stderr=DEVNULL)
        status_code = wait_for_streamlit(url)
        if status_code == 200:
            print("✅ App funciona")
            return 0
        print("❌ Error")
        return 1
    except Exception as exc:
        print(f"❌ Error: {exc}")
        return 1
    finally:
        if process is not None:
            terminate_process(process)


if __name__ == "__main__":
    raise SystemExit(main())
