"""
Standalone script to view the complete UATP system network graph
Run with: streamlit run view_system_graph.py --server.port 8504
"""

import os
import sys

# Add project paths
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from visualizer.components.system_network_graph import render_system_graph

if __name__ == "__main__":
    render_system_graph()
