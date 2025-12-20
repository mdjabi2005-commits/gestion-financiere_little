#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Point d'entrée principal pour Gestio V4
Lance la console interactive
"""

import sys
from pathlib import Path

# Ajouter app au path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

if __name__ == "__main__":
    from launcher import main
    main()