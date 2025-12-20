#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Point d'entrée principal pour Gestio V4
Lance l'interface web
"""

import sys
from pathlib import Path

# Ajouter app au path
if getattr(sys, 'frozen', False):
    # Mode PyInstaller : modules dans MEIPASS
    current_dir = Path(sys._MEIPASS)
else:
    # Mode développement
    current_dir = Path(__file__).parent
    
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

if __name__ == "__main__":
    from gui_launcher import main
    
    # Lancer le Centre de Contrôle
    print("🚀 Gestio V4 - Centre de Contrôle")
    print("📍 Ouverture de l'interface...\n")
    
    main()
    print("📍 Ouverture dans votre navigateur...")
    print("⚠️  Appuyez sur Ctrl+C pour arrêter\n")
    
    app.run(host='localhost', port=5555, debug=False)