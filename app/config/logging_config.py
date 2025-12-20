"""
Configuration du système de logging pour Gestion Financière V4

Ce module configure le logging avec:
- Rotation automatique des fichiers (5MB max)
- Logs dans fichier + console
- Niveaux de log configurables
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logging(log_dir: Optional[Path] = None, level: str = "INFO") -> None:
    """
    Configure le système de logging pour l'application.
    
    Args:
        log_dir: Répertoire où stocker les logs (défaut: répertoire courant)
        level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Exemple:
        >>> from config.logging_config import setup_logging
        >>> from pathlib import Path
        >>> setup_logging(Path("logs"), "INFO")
    """
    # Créer le répertoire de logs s'il n'existe pas
    if log_dir is None:
        log_dir = Path.cwd()
    
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "gestio_app.log"
    
    # Format détaillé pour les logs
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler fichier avec rotation (5MB max, 3 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, 
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Handler console (WARNING+ seulement)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)
    
    # Configuration du root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Nettoyer les handlers existants (évite les duplications)
    root_logger.handlers.clear()
    
    # Ajouter les nouveaux handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log de démarrage
    root_logger.info("=" * 50)
    root_logger.info("Logging system initialized")
    root_logger.info(f"Log file: {log_file}")
    root_logger.info(f"Log level: {level}")
    root_logger.info("=" * 50)


def get_logger(name: str) -> logging.Logger:
    """
    Obtenir un logger pour un module spécifique.
    
    Args:
        name: Nom du logger (généralement __name__)
    
    Returns:
        Logger configuré
    
    Exemple:
        >>> logger = get_logger(__name__)
        >>> logger.info("Message d'information")
    """
    return logging.getLogger(name)
