#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Point d'entrée principal pour Gestio V4
Lance l'interface web
"""

import sys
from pathlib import Path

# Ajouter app au path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

if __name__ == "__main__":
    from web_launcher import app
    import webbrowser
    
    # Ouvrir le navigateur
    webbrowser.open('http://localhost:5555')
    
    # Lancer le serveur
    print("🚀 Gestio V4 Web Launcher")
    print("📍 Ouverture dans votre navigateur...")
    print("⚠️  Appuyez sur Ctrl+C pour arrêter\n")
    
    app.run(host='localhost', port=5555, debug=False)