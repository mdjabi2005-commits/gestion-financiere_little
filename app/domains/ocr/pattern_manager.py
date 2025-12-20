"""
Pattern Manager for OCR Configuration

This module manages OCR patterns loaded from YAML configuration,
allowing easy addition and modification of patterns without code changes.
"""

import yaml
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from shared.logging_config import get_logger

logger = get_logger(__name__)


class PatternManager:
    """Manages OCR patterns from YAML configuration."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize Pattern Manager.
        
        Args:
            config_path: Path to YAML configuration file (defaults to project config/ocr_patterns.yml)
        """
        if config_path is None:
            # Get absolute path relative to this file
            current_dir = Path(__file__).parent.parent.parent  # domains/ocr -> v4/
            config_path = str(current_dir / 'config' / 'ocr_patterns.yml')
        
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Config file not found: {self.config_path}")
                return self._get_default_config()
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded OCR patterns from {self.config_path}")
                return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if file doesn't exist."""
        return {
            'amount_patterns': [],
            'payment_patterns': [],
            'date_patterns': [],
            'known_merchants': [],
            'config': {}
        }
    
    def get_amount_patterns(self) -> List[str]:
        """
        Get active amount detection patterns sorted by priority.
        
        Returns:
            List of regex patterns for amount detection
        """
        patterns = self.config.get('amount_patterns', [])
        
        # Filter enabled patterns
        active = [p for p in patterns if p.get('enabled', True)]
        
        # Sort by priority (lower number = higher priority)
        sorted_patterns = sorted(active, key=lambda x: x.get('priority', 999))
        
        # Extract just the pattern strings
        return [p['pattern'] for p in sorted_patterns]
    
    def get_payment_patterns(self) -> List[str]:
        """
        Get payment method patterns.
        
        Returns:
            List of payment method keywords
        """
        return self.config.get('payment_patterns', [])
    
    def get_date_patterns(self) -> List[Dict[str, str]]:
        """
        Get date detection patterns with formats.
        
        Returns:
            List of dicts with 'pattern' and 'format' keys
        """
        return self.config.get('date_patterns', [])
    
    def get_known_merchants(self) -> List[str]:
        """
        Get list of known merchant names.
        
        Returns:
            List of merchant keywords
        """
        return self.config.get('known_merchants', [])
    
    def add_amount_pattern(
        self, 
        pattern: str, 
        description: str = "", 
        priority: int = 99,
        enabled: bool = True
    ) -> bool:
        """
        Add a new amount detection pattern.
        
        Args:
            pattern: Regex pattern string
            description: Human-readable description
            priority: Priority (lower = tested first)
            enabled: Whether pattern is active
        
        Returns:
            True if added successfully
        """
        try:
            new_pattern = {
                'pattern': pattern,
                'priority': priority,
                'enabled': enabled,
                'description': description
            }
            
            self.config['amount_patterns'].append(new_pattern)
            self._save_config()
            logger.info(f"Added new pattern: {pattern}")
            return True
        except Exception as e:
            logger.error(f"Error adding pattern: {e}")
            return False
    
    def disable_pattern(self, pattern: str) -> bool:
        """
        Disable a pattern without removing it.
        
        Args:
            pattern: Pattern string to disable
        
        Returns:
            True if disabled successfully
        """
        try:
            for p in self.config.get('amount_patterns', []):
                if p['pattern'] == pattern:
                    p['enabled'] = False
                    self._save_config()
                    logger.info(f"Disabled pattern: {pattern}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error disabling pattern: {e}")
            return False
    
    def enable_pattern(self, pattern: str) -> bool:
        """
        Enable a previously disabled pattern.
        
        Args:
            pattern: Pattern string to enable
        
        Returns:
            True if enabled successfully
        """
        try:
            for p in self.config.get('amount_patterns', []):
                if p['pattern'] == pattern:
                    p['enabled'] = True
                    self._save_config()
                    logger.info(f"Enabled pattern: {pattern}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error enabling pattern: {e}")
            return False
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found
        
        Returns:
            Configuration value
        """
        return self.config.get('config', {}).get(key, default)
    
    def _save_config(self) -> None:
        """Save current configuration to YAML file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
            logger.info(f"Saved config to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            raise
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self.config = self._load_config()
        logger.info("Configuration reloaded")
    
    def get_pattern_stats(self) -> Dict[str, int]:
        """
        Get statistics about loaded patterns.
        
        Returns:
            Dict with pattern counts
        """
        return {
            'total_amount_patterns': len(self.config.get('amount_patterns', [])),
            'active_amount_patterns': len(self.get_amount_patterns()),
            'payment_patterns': len(self.get_payment_patterns()),
            'date_patterns': len(self.get_date_patterns()),
            'known_merchants': len(self.get_known_merchants())
        }


# Singleton instance for global access
_pattern_manager_instance: Optional[PatternManager] = None


def get_pattern_manager() -> PatternManager:
    """
    Get the global PatternManager instance (singleton).
    
    Returns:
        PatternManager instance
    """
    global _pattern_manager_instance
    
    if _pattern_manager_instance is None:
        _pattern_manager_instance = PatternManager()
    
    return _pattern_manager_instance
