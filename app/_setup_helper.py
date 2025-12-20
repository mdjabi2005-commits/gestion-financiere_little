# -*- coding: utf-8 -*-
"""
Simple wrapper to add setup.done check before dependency verification
"""
import os
from pathlib import Path

def should_check_dependencies():
    """Check if we need to verify dependencies (only on first run)"""
    base_path = Path(__file__).parent
    setup_marker = base_path / "setup.done"
    
    if setup_marker.exists():
        print("✅ Configuration déjà effectuée - lancement rapide...")
        return False
    else:
        print("📦 Première exécution - vérification des dépendances...")
        return True

def mark_setup_complete():
    """Create setup.done marker"""
    base_path = Path(__file__).parent
    setup_marker = base_path / "setup.done"
    setup_marker.touch()
    print("✅ Configuration initiale terminée!")
