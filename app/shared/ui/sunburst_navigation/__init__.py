"""
Sunburst Navigation Component - Streamlit Custom Component with Plotly

Bidirectional communication: Python → JS → Python
"""

import streamlit as st
import streamlit.components.v1 as components
import os
from typing import Dict, Any, Optional


# Declare the custom component pointing to frontend folder
_component_func = components.declare_component(
    "sunburst_navigation",
    path=os.path.join(os.path.dirname(__file__), "frontend")
)


def sunburst_navigation(
    hierarchy: Dict[str, Any],
    key: Optional[str] = None,
    height: int = 600
) -> Optional[Dict[str, Any]]:
    """
    Render interactive Plotly Sunburst with click detection.
    
    Args:
        hierarchy: Financial hierarchy data from fractal_service
        key: Unique component key
        height: Chart height in pixels
    
    Returns:
        Dictionary with clicked category info or None
        Format: {'code': 'DEPENSES', 'label': 'Dépenses', 'action': 'select'}
    """
    
    if not hierarchy:
        return None
    
    # Get reset counter from session state if button was clicked
    reset_counter = st.session_state.get(f'{key}_reset', 0) if key else 0
    
    # Call the custom component
    # It will return the value sent by Streamlit.setComponentValue() in JS
    component_value = _component_func(
        hierarchy=hierarchy,
        height=height,
        reset_counter=reset_counter,
        key=key,
        default=None
    )
    
    # Returns None initially, or the clicked category data
    return component_value
