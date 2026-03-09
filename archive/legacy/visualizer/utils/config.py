"""
Centralized configuration for the UATP Visualizer.

This file holds shared configuration variables to prevent circular imports.
"""

# Single source of truth for navigation structure
nav_options = [
    {"label": "Overview", "view": "overview", "icon": ""},
    {"label": "Timeline", "view": "timeline", "icon": ""},
    {"label": "Sankey", "view": "sankey", "icon": ""},
    {"label": "Heatmap", "view": "heatmap", "icon": "️"},
    {"label": "Analysis", "view": "analysis", "icon": ""},
    {"label": "Settings", "view": "settings", "icon": ""},
]
