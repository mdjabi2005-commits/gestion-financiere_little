"""CSS style loading utilities.

This module provides functions to load and apply CSS styles from the
resources/styles/ directory to Streamlit applications.
"""

import os
import logging
from typing import Optional, List
import streamlit as st

logger = logging.getLogger(__name__)

# Base directory for CSS files
STYLES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "resources",
    "styles"
)


def load_css(filename: str) -> Optional[str]:
    """
    Load a CSS file from the resources/styles/ directory.

    Args:
        filename: Name of the CSS file (e.g., 'main.css')

    Returns:
        CSS content as string, or None if file not found

    Example:
        >>> css = load_css('main.css')
        >>> css is not None
        True
        >>> 'background' in css
        True
    """
    css_path = os.path.join(STYLES_DIR, filename)

    try:
        if not os.path.exists(css_path):
            logger.warning(f"CSS file not found: {css_path}")
            return None

        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
            logger.info(f"Loaded CSS file: {filename}")
            return css_content

    except Exception as e:
        logger.error(f"Error loading CSS file {filename}: {e}")
        return None


def apply_css(filename: str) -> None:
    """
    Load and apply a CSS file to the current Streamlit page.

    Wraps the CSS in <style> tags and injects it using st.markdown().

    Args:
        filename: Name of the CSS file (e.g., 'main.css')

    Side effects:
        - Injects CSS into the page using st.markdown()
        - Logs warning if file not found

    Example:
        >>> apply_css('main.css')  # Applies main.css to current page
        >>> apply_css('dark_mode.css')  # Applies dark mode styles
    """
    css_content = load_css(filename)

    if css_content:
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    else:
        logger.warning(f"Could not apply CSS: {filename}")


def apply_multiple_css(filenames: List[str]) -> None:
    """
    Load and apply multiple CSS files to the current Streamlit page.

    Args:
        filenames: List of CSS file names to apply

    Side effects:
        - Injects all CSS files into the page
        - Logs warnings for any files not found

    Example:
        >>> apply_multiple_css(['main.css', 'responsive.css', 'dark_mode.css'])
    """
    for filename in filenames:
        apply_css(filename)


def get_available_styles() -> List[str]:
    """
    Get list of available CSS files in the styles directory.

    Returns:
        List of CSS filenames found in resources/styles/

    Example:
        >>> styles = get_available_styles()
        >>> 'main.css' in styles
        True
    """
    try:
        if not os.path.exists(STYLES_DIR):
            logger.warning(f"Styles directory not found: {STYLES_DIR}")
            return []

        css_files = [
            f for f in os.listdir(STYLES_DIR)
            if f.endswith('.css')
        ]

        return sorted(css_files)

    except Exception as e:
        logger.error(f"Error listing style files: {e}")
        return []


def inject_custom_css(css_content: str) -> None:
    """
    Inject custom CSS directly without loading from file.

    Args:
        css_content: CSS content as string

    Side effects:
        - Injects CSS into the page using st.markdown()

    Example:
        >>> custom_css = '''
        ... .my-custom-class {
        ...     background-color: #f0f0f0;
        ...     padding: 10px;
        ... }
        ... '''
        >>> inject_custom_css(custom_css)
    """
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def load_all_styles() -> None:
    """
    Load and apply all standard application styles.

    Applies the following CSS files in order:
    1. main.css - Main application styles
    2. responsive.css - Responsive design styles
    3. dark_mode.css - Dark mode styles (if available)

    Side effects:
        - Applies all available standard CSS files
        - Skips files that don't exist

    Example:
        >>> load_all_styles()  # Loads all standard styles
    """
    standard_styles = ['main.css', 'responsive.css', 'dark_mode.css']

    for style_file in standard_styles:
        apply_css(style_file)
