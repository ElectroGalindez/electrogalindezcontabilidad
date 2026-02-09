# -*- mode: python ; coding: utf-8 -*-

import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

streamlit_datas = collect_data_files("streamlit")
streamlit_metadata = copy_metadata("streamlit")
webview_metadata = copy_metadata("pywebview")

hiddenimports = (
    collect_submodules("streamlit")
    + [
        "webview.platforms.cocoa",
        "webview.platforms.winforms",
    ]
)

excludes = [
    "PyQt5",
    "PyQt6",
    "PySide2",
    "PySide6",
    "tkinter",
]

a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("ElectroGalindez.py", "."),
        ("assets", "assets"),
        ("backend", "backend"),
        ("pages", "pages"),
        ("ui", "ui"),
        ("data", "data"),
    ]
    + streamlit_datas
    + streamlit_metadata
    + webview_metadata,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ElectroGalindez",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ElectroGalindez",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="ElectroGalindez.app",
        icon=None,
        bundle_identifier=None,
    )
