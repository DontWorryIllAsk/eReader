# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

project_root = Path(SPECPATH)

a = Analysis(
    [str(project_root / 'src' / 'main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[(str(project_root / 'resources'), 'resources')],
    hiddenimports=[
        'src',
        'src.main',
        'src.app',
        'src.utils',
        'src.icons',
        'src.models',
        'src.models.database',
        'src.models.book',
        'src.models.annotation',
        'src.readers',
        'src.readers.epub_reader',
        'src.readers.reader_widget',
        'src.library',
        'src.library.main_window',
        'src.library.library_widget',
        'src.library.import_handler',
        'src.settings',
        'src.settings.settings',
        'src.settings.settings_widget',
        'src.settings.settings_repository',
        'src.settings.theme_manager',
        'src.settings.themes',
        'src.annotations',
        'src.annotations.annotation_widget',
        'src.annotations.bookmark_manager',
        'PySide6.QtSvg',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
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
    name='eReader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'resources' / 'icons' / 'app_icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='eReader',
)
