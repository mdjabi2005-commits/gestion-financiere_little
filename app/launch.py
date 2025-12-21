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

def check_first_run():
    """Vérifie si c'est le premier lancement"""
    flag_file = Path.home() / ".gestio_v4_initialized"
    return not flag_file.exists(), flag_file

def verify_dependencies():
    """Vérifie que Python et les dépendances sont installées"""
    print("🔍 Vérification des dépendances...")
    
    # Vérifier Python
    print(f"✅ Python {sys.version.split()[0]} détecté")
    
    # Vérifier modules critiques
    required_modules = ['tkinter', 'requests']
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} installé")
        except ImportError:
            print(f"❌ {module} manquant")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️ Modules manquants : {', '.join(missing)}")
        print("💡 Installez avec : pip install " + " ".join(missing))
        input("\nAppuyez sur Entrée pour continuer...")
        return False
    
    print("\n✅ Toutes les dépendances sont installées !")
    return True

def main():
    """Lance le Control Center GUI ou directement l'app selon l'environnement"""
    
    # Détecter le mode
    if getattr(sys, 'frozen', False):
        # Mode compilé
        is_first_run, flag_file = check_first_run()
        
        if is_first_run:
            # Premier lancement : vérifier dépendances
            print("🚀 Gestio V4 - Premier lancement")
            print("━" * 50)
            
            if verify_dependencies():
                # Créer le flag
                flag_file.touch()
                print("✅ Configuration terminée !")
                print("\nLancement du Control Center...")
                import time
                time.sleep(2)
        
        # Lancer le Control Center
        from gui_launcher import main as gui_main
        gui_main()
    else:
        # Mode développement : lancer directement Streamlit
        print("🚀 Gestio V4 - Mode Développement")
        print("📍 Lancement de Streamlit...")
        os.system(f"{sys.executable} -m streamlit run {current_dir / 'main.py'}")

if __name__ == "__main__":
    main()
