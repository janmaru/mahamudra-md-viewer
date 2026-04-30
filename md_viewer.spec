# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Friedrich - Document Reader."""

import os

block_cipher = None
project_dir = os.path.abspath(".")

a = Analysis(
    ["md_reader.py"],
    pathex=[project_dir],
    binaries=[],
    datas=[
        ("scripts/mermaid.min.js", "scripts"),
        ("scripts/plantuml.jar", "scripts"),
        ("styles/*.css", "styles"),
        ("VERSION", "."),
    ],
    hiddenimports=[
        "services",
        "services.css_loader",
        "services.diagram_cache",
        "services.file_renderer",
        "services.file_scanner",
        "services.mermaid_processor",
        "services.pdf_exporter",
        "services.plantuml_processor",
        "services.log_renderer",
        "widgets",
        "widgets.custom_menu",
        "widgets.diagram_viewer",
        "widgets.listbox_tooltip",
        "widgets.search_bar",
        "widgets.sidebar",
        "widgets.toolbar",
        "constants",
        "app_context",
        "settings_manager",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Friedrich",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon="app_icon.ico",
)
