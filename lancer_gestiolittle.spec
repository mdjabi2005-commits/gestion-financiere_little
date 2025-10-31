# -*- mode: python ; coding: utf-8 -*-


# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# 🔥 CORRECTION : Collecter TOUS les fichiers Python nécessaires
datas_list = []

# Ajouter gestiolittle.py (application principale)
if os.path.exists('app/gestiolittle.py'):
    datas_list.append(('app/gestiolittle.py', '.'))

# 🔥 CRITIQUE : Ajouter configlittle.py
if os.path.exists('app/configlittle.py'):
    datas_list.append(('app/configlittle.py', '.'))

# Ajouter auto_updater.py
if os.path.exists('app/auto_updater.py'):
    datas_list.append(('app/auto_updater.py', '.'))

# Ajouter changelog_viewer.py
if os.path.exists('app/changelog_viewer.py'):
    datas_list.append(('app/changelog_viewer.py', '.'))

# Ajouter le dossier tesseract s'il existe (Windows)
if os.path.exists('tesseract'):
    datas_list.append(('tesseract', 'tesseract'))

a = Analysis(
    ['app/lancer_gestiolittle.py'],
    pathex=['app'],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        'streamlit',
        'configlittle',
        'auto_updater', 
        'changelog_viewer',
        'pandas',
        'pytesseract',
        'PIL',
        'cv2',
        'numpy',
        'dateutil',
        'requests'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'unittest', 'test', '_pytest', 'setuptools', 'pip', 'wheel'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GestionFinanciereLittle',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Désactiver UPX pour éviter faux positifs antivirus
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
