"""
Enhanced Console and Error Display Module

Provides colorful console output and user-friendly error messages
for better debugging and user experience.
"""

import sys
from typing import Optional
from enum import Enum


class ConsoleColor(Enum):
    """ANSI color codes for console output."""
    # Basic colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    
    # Formatting
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


def colored_print(message: str, color: ConsoleColor = ConsoleColor.WHITE, bold: bool = False):
    """
    Print colored message to console.
    
    Args:
        message: Message to print
        color: Color to use
        bold: Whether to make text bold
    """
    prefix = color.value
    if bold:
        prefix += ConsoleColor.BOLD.value
    
    print(f"{prefix}{message}{ConsoleColor.RESET.value}")


def success(message: str):
    """Print success message in green."""
    colored_print(f"✅ {message}", ConsoleColor.BRIGHT_GREEN, bold=True)


def error(message: str):
    """Print error message in red."""
    colored_print(f"❌ {message}", ConsoleColor.BRIGHT_RED, bold=True)


def warning(message: str):
    """Print warning message in yellow."""
    colored_print(f"⚠️  {message}", ConsoleColor.BRIGHT_YELLOW, bold=True)


def info(message: str):
    """Print info message in cyan."""
    colored_print(f"ℹ️  {message}", ConsoleColor.BRIGHT_CYAN)


def debug(message: str):
    """Print debug message in magenta."""
    colored_print(f"🔍 {message}", ConsoleColor.MAGENTA)


def section(title: str):
    """Print section header."""
    colored_print(f"\n{'='*60}", ConsoleColor.BLUE)
    colored_print(f"  {title}", ConsoleColor.BRIGHT_BLUE, bold=True)
    colored_print(f"{'='*60}\n", ConsoleColor.BLUE)


def progress(message: str, percentage: Optional[int] = None):
    """Print progress message."""
    if percentage is not None:
        colored_print(f"🔄 {message} ({percentage}%)", ConsoleColor.CYAN)
    else:
        colored_print(f"🔄 {message}", ConsoleColor.CYAN)


# Examples for testing
if __name__ == "__main__":
    section("Enhanced Console Demo")
    
    success("Operation completed successfully!")
    error("Failed to connect to database")
    warning("Configuration file not found, using defaults")
    info("Processing 150 transactions...")
    debug("Variable x = 42")
    progress("Installing dependencies", 75)
    
    print("\n")
    colored_print("Custom colored text", ConsoleColor.MAGENTA, bold=True)
