# Empaquetado de escritorio (PyInstaller + Streamlit + PyWebview)

## Estructura sugerida del proyecto

```
/electrogalindezcontabilidad
├─ ElectroGalindez.py
├─ launcher.py
├─ assets/
├─ pages/
├─ core/
├─ ui/
├─ data/                # SQLite y archivos locales
├─ docs/
│  └─ desktop_packaging.md
├─ requirements.txt
└─ launcher_desktop.spec
```

## Ejemplo de `launcher_desktop.spec`

```python
# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

project_root = Path(__file__).resolve().parent

block_cipher = None

streamlit_datas = [
    (str(project_root / "assets"), "assets"),
    (str(project_root / "pages"), "pages"),
    (str(project_root / "core"), "core"),
    (str(project_root / "ui"), "ui"),
    (str(project_root / "data"), "data"),
    (str(project_root / "ElectroGalindez.py"), "."),
]

hiddenimports = [
    "streamlit.web.cli",
    "streamlit.runtime.scriptrunner",
    "pywebview",
]

analysis = Analysis(
    ["launcher.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=streamlit_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(analysis.pure, analysis.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    [],
    name="ElectroGalindez",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Evita consola en Windows/macOS
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

## Construcción del ejecutable

```bash
# Windows
pyinstaller launcher_desktop.spec

# macOS
pyinstaller launcher_desktop.spec

# Linux
pyinstaller launcher_desktop.spec
```

## Notas importantes

- El `launcher.py` detecta si está empaquetado (`sys.frozen`) y usa rutas con `_MEIPASS`.
- Los recursos se incluyen como `datas` en el `.spec`.
- `console=False` evita la consola en Windows/macOS.
- Si cambia el nombre del script principal, actualiza `STREAMLIT_SCRIPT` en `launcher.py`.
