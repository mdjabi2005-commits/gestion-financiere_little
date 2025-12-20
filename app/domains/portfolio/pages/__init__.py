"""
Portfolio Package

This package contains the refactored portfolio interface modules (V2):
- helpers.py: Utility functions for period calculations and budget analysis
- overview.py: Dashboard tab (read-only)
- manage.py: Management hub tab (4 quadrants)
- analyze.py: Analysis and forecasts tab
"""

from .overview import render_overview_tab
from .manage import render_manage_tab
from .analyze import render_analyze_tab
from .helpers import (
    normalize_recurrence_column,
    get_period_start_date,
    calculate_months_in_period,
    analyze_exceptional_expenses
)


__all__ = [
    # V2 main tabs
    'render_overview_tab',
    'render_manage_tab',
    'render_analyze_tab',
    # Helpers
    'normalize_recurrence_column',
    'get_period_start_date',
    'calculate_months_in_period',
    'analyze_exceptional_expenses',
]
