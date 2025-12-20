"""
Financial Tree Component - Streamlit Custom Component with D3.js

Interactive Sankey flow visualization with drag-and-drop for transaction management.
"""

import streamlit as st
import streamlit.components.v1 as components
import os
from typing import Dict, Any, Optional, List


# Declare the custom component pointing to frontend folder
_component_func = components.declare_component(
    "financial_tree",
    path=os.path.join(os.path.dirname(__file__), "frontend")
)


def financial_tree(
    nodes: List[Dict[str, Any]],
    transactions: List[Dict[str, Any]],
    key: Optional[str] = None,
    height: int = 900
) -> Optional[Dict[str, Any]]:
    """
    Render interactive D3 Sankey flow with drag-and-drop transactions.
    
    Args:
        nodes: List of category nodes with levels
        transactions: List of transaction flows between nodes
        key: Unique component key
        height: Chart height in pixels
    
    Returns:
        Dictionary with action info from user interactions
        Format: {'action': 'update_transaction', 'transaction_id': 1, 'new_category': '...'}
    """
    
    if not nodes or not transactions:
        return None
    
    # Debug: Print what we're sending to the component
    print(f"[FINANCIAL_TREE] Calling component with {len(nodes)} nodes and {len(transactions)} transactions")
    print(f"[FINANCIAL_TREE] Key: {key}")
    
    # Call the custom component
    component_value = _component_func(
        nodes=nodes,
        transactions=transactions,
        height=height,
        key=key,
        default=None
    )
    
    return component_value

