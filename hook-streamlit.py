# -*- coding: utf-8 -*-
"""
Created on Mon Oct 20 22:58:21 2025

@author: djabi
"""
from PyInstaller.utils.hooks import (
    copy_metadata,
    collect_data_files,
    collect_submodules,
)

# 1️⃣ Inclure les métadonnées (streamlit-x.y.z.dist-info)
datas = copy_metadata("streamlit")

# 2️⃣ Inclure les fichiers internes (html, css, config, etc.)
datas += collect_data_files("streamlit")

# 3️⃣ Forcer l’inclusion de tous les sous-modules
hiddenimports = collect_submodules("streamlit")

