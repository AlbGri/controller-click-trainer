# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file per Controller Click Trainer

import os

block_cipher = None

# DLL conda che PyInstaller non trova automaticamente
CONDA_BIN = os.path.join(os.environ.get('CONDA_PREFIX', r'C:\Users\Alberto\.conda\envs\click-trainer'), 'Library', 'bin')

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[
        (os.path.join(CONDA_BIN, 'tcl86t.dll'), '.'),
        (os.path.join(CONDA_BIN, 'tk86t.dll'), '.'),
        (os.path.join(CONDA_BIN, 'ffi.dll'), '.'),
        (os.path.join(CONDA_BIN, 'liblzma.dll'), '.'),
        (os.path.join(CONDA_BIN, 'libbz2.dll'), '.'),
        (os.path.join(CONDA_BIN, 'libexpat.dll'), '.'),
    ],
    datas=[
        ('config/settings.json', 'config'),
    ],
    hiddenimports=[
        'src',
        'src.gui',
        'src.controller_monitor',
        'src.data_manager',
        'src.diagnostics',
        'src.visualizer',
        'src.translations',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ControllerClickTrainer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No finestra console, solo GUI tkinter
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ControllerClickTrainer',
)
