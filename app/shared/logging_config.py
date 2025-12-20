"""
Logging Configuration - Centralized Logging Setup

Provides structured logging with:
- File rotation (5MB max, 3 backups)
- Dual output (file + console)
- Timestamp + module + level formatting
- UTF-8 encoding for French characters
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logging(log_dir: Optional[Path] = None, log_level: int = logging.INFO) -> None:
    """
    Configure centralized logging system for the application.
    
    Features:
    - File handler with 5MB rotation, 3 backups
    - Console handler for warnings and above
    - UTF-8 encoding for French characters
    - Detailed timestamp formatting
    
    Args:
        log_dir: Directory for log files (default: data/logs/)
        log_level: Minimum logging level (default: INFO)
    
    Example:
        >>> from shared.logging_config import setup_logging
        >>> setup_logging()
        >>> import logging
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Application started")
    """
    # Default log directory
    if log_dir is None:
        log_dir = Path("data/logs")
    
    # Create log directory if doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Log file path
    log_file = log_dir / "gestio_app.log"
    
    # Formatter with timestamp, module name, level, and message
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # === FILE HANDLER ===
    # Rotating file handler: 5MB max, 3 backups
    # gestio_app.log → gestio_app.log.1 → gestio_app.log.2 → gestio_app.log.3
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding='utf-8'  # Support French characters (é, è, à, etc.)
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)  # File gets INFO and above
    
    # === CONSOLE HANDLER ===
    # Console only shows warnings and errors (less verbose)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)  # Console gets WARNING and above
    
    # === ROOT LOGGER CONFIGURATION ===
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)  # Root level (catch everything)
    
    # Clear existing handlers (avoid duplicates on reload)
    root_logger.handlers.clear()
    
    # Add our handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log initialization
    logging.info("=" * 70)
    logging.info("Logging system initialized")
    logging.info(f"Log file: {log_file.absolute()}")
    logging.info(f"Log level: {logging.getLevelName(log_level)}")
    logging.info("=" * 70)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Usage in modules:
        >>> from shared.logging_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Module loaded")
    
    Args:
        name: Module name (use __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Logging best practices:
# 
# DEBUG   - Detailed diagnostic info (variable values, function calls)
# INFO    - General informational messages (operation started/completed)
# WARNING - Something unexpected but not critical (fallback used, retry)
# ERROR   - Error occurred but app continues (failed to save, parse error)
# CRITICAL - Serious error, app may crash (database corrupted, config missing)
#
# Example usage across domains:
#
# ```python
# from shared.logging_config import get_logger
# 
# logger = get_logger(__name__)
# 
# def add_transaction(data):
#     logger.info(f"Adding transaction: {data.get('description')}")
#     
#     try:
#         # ... operation ...
#         logger.debug(f"Transaction saved with ID: {result.id}")
#         return result
#     except Exception as e:
#         logger.error(f"Failed to add transaction: {e}", exc_info=True)
#         raise
# ```
