#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestio V4 - Launcher Simplifié
Point d'entrée unique pour toutes les versions
"""

import sys
import os
from pathlib import Path

# Ajouter app au path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

def main():
    """Lance le Control Center GUI ou directement l'app selon l'environnement"""
    
    # Détecter le mode
    if getattr(sys, 'frozen', False):
        # Mode compilé : lancer le Control Center
        print("🚀 Gestio V4 - Control Center")
        from gui_launcher import main as gui_main
        gui_main()
    else:
        # Mode développement : lancer directement Streamlit
        print("🚀 Gestio V4 - Mode Développement")
        print("📍 Lancement de Streamlit...")
        os.system(f"{sys.executable} -m streamlit run {current_dir / 'main.py'}")

if __name__ == "__main__":
    main()
