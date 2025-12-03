"""
visualizer.py - Streamlit-based visualizer for UATP capsule chains.
Displays capsule chains, forks, and merges interactively using Graphviz.
Implements a progressive disclosure UI with tabs for different views.
"""

import datetime
import json

import graphviz
import pandas as pd
import streamlit as st
from capsule_schema import Capsule

# ---- Global Design Helpers ----


def apply_global_design(dark_mode: bool = False):
    """Inject Google Font, CSS variables, and JS dark-mode toggle."""
    # Google Font
    st.markdown(
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&display=swap" rel="stylesheet">',
        unsafe_allow_html=True,
    )

    # CSS Variables & component styles
    css = """
    <style>
    :root {
        /* Base colors */
        --bg: #ffffff;
        --bg-subtle: #f9f9f9;
        --bg-card: #ffffff;
        --text: #222222;
        --text-muted: #6e6e6e;
        --border: rgba(0,0,0,0.05);
        --shadow: rgba(0,0,0,0.04);

        /* Accent color - subtle blue */
        --accent: #4a6eb3;
        --accent-subtle: rgba(74,110,179,0.08);

        /* Functional Capsule Type Colors */
        --introspective: #dbeafe; /* Light Blue */
        --joint: #dcfce7;       /* Light Green */
        --refusal: #fee2e2;       /* Light Red */
        --merge: #fef3c7;         /* Light Amber */
        --perspective: #ede9fe;   /* Light Purple */
        --default-capsule: #f3f4f6; /* Light Gray */
    }

    html[data-theme='dark'] {
        /* Dark Mode Colors */
        --bg: #111827;
        --bg-subtle: #1f2937;
        --bg-card: #374151;
        --text: #d1d5db;
        --text-muted: #9ca3af;
        --border: #4b5563;
        --shadow: rgba(0,0,0,0.3);

        /* Accent Color */
        --accent: #60a5fa;
        --accent-subtle: rgba(96, 165, 250, 0.1);

        /* Functional Capsule Type Colors (Dark) */
        --introspective: #1e3a8a; /* Dark Blue */
        --joint: #166534;       /* Dark Green */
        --refusal: #991b1b;       /* Dark Red */
        --merge: #92400e;         /* Dark Amber */
        --perspective: #5b21b6;   /* Dark Purple */
        --default-capsule: #4b5563; /* Dark Gray */
    }

    /* Global styles */
    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: var(--bg);
        color: var(--text);
        font-size: 15px;
        line-height: 1.6;
        letter-spacing: 0.01em;
        transition: background-color 0.3s ease;
    }

    /* Page fade-in animation */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    .main .block-container {
        animation: fadeIn 0.5s ease-in-out;
        max-width: 1200px;
        padding-top: 1rem;
        padding-bottom: 5rem;
    }

    /* Typography */
    h1 {
        font-weight: 300;
        letter-spacing: 0.02em;
        margin-bottom: 1.5rem;
        color: var(--text);
    }

    h2, h3, h4, h5 {
        font-weight: 400;
        letter-spacing: 0.01em;
        color: var(--text);
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }

    p {
        color: var(--text-muted);
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }

    /* Sidebar */
    section[data-testid='stSidebar'] > div:first-child {
        background: var(--bg-subtle);
        border-right: 1px solid var(--border);
    }

    /* Cards and containers */
    div.stExpander {
        border: none !important;
        background: var(--bg-card) !important;
        box-shadow: 0 1px 3px var(--shadow) !important;
        border-radius: 4px !important;
        transition: box-shadow 0.15s ease-in-out !important;
    }

    div.stExpander:hover {
        box-shadow: 0 2px 6px var(--shadow) !important;
    }

    /* Buttons */
    button[kind] {
        border-radius: 4px;
        font-size: 0.9rem;
        font-weight: 400;
        letter-spacing: 0.02em;
        padding: 0.4rem 1rem;
        transition: all 0.15s ease-in-out;
    }

    button[kind='primary'] {
        background: var(--accent);
        color: white;
        border: none;
    }

    button:not([kind='primary']) {
        border: 1px solid var(--border);
        background: var(--bg-card);
        color: var(--text);
    }

    button[kind]:hover {
        box-shadow: 0 2px 6px var(--shadow);
        transform: translateY(-1px);
    }

    /* Tabs */
    .stTabs {
        margin-top: 1rem;
    }

    .stTabs [data-baseweb='tab-list'] {
        gap: 2rem;
        border-bottom: 1px solid var(--border);
    }

    .stTabs [data-baseweb='tab'] {
        padding: 0.5rem 0.25rem;
        font-size: 0.95rem;
        font-weight: 400;
        color: var(--text-muted);
        transition: all 0.15s ease;
    }

    .stTabs [aria-selected='true'] {
        border-bottom: 2px solid var(--accent);
        color: var(--text);
        font-weight: 500;
    }

    /* Toggle switch */
    .stToggle > div[role='switch'][aria-checked='true'] {
        background-color: var(--accent) !important;
    }

    /* Tables */
    .dataframe {
        font-size: 0.9rem;
        border-collapse: separate;
        border-spacing: 0;
    }

    .dataframe th {
        background: var(--bg-subtle);
        color: var(--text);
        font-weight: 500;
        padding: 0.5rem 0.75rem;
        border-bottom: 1px solid var(--border);
    }

    .dataframe td {
        padding: 0.5rem 0.75rem;
        border-bottom: 1px solid var(--border);
        color: var(--text-muted);
    }

    /* Timeline items */
    .timeline-item {
        transition: transform 0.15s ease-out, box-shadow 0.15s ease-out;
    }

    .timeline-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 3px 10px var(--shadow);
    }

    /* Graph elements */
    svg g.node:hover {
        opacity: 0.9;
        cursor: pointer;
    }

    /* Dark mode toggle */
    [data-testid="stToggleButton"] {
        display: flex;
        justify-content: flex-end;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

    # JS to set theme attribute and add animations
    theme = "dark" if dark_mode else "light"
    js = f"""
    <script>
    // Set theme attribute
    const root = document.documentElement;
    root.setAttribute('data-theme', '{theme}');

    // Add fade-in animation to graph elements when they appear
    const observer = new MutationObserver((mutations) => {{
      mutations.forEach((mutation) => {{
        if (mutation.addedNodes && mutation.addedNodes.length > 0) {{
          mutation.addedNodes.forEach((node) => {{
            if (node.tagName === 'SVG') {{
              // Add animation to graph nodes
              const nodes = node.querySelectorAll('.node');
              nodes.forEach((node, index) => {{
                node.style.opacity = '0';
                node.style.transition = 'opacity 0.3s ease-in-out';
                setTimeout(() => {{
                  node.style.opacity = '1';
                }}, 100 + (index * 50));
              }});

              // Add animation to graph edges
              const edges = node.querySelectorAll('.edge');
              edges.forEach((edge, index) => {{
                edge.style.opacity = '0';
                edge.style.transition = 'opacity 0.3s ease-in-out';
                setTimeout(() => {{
                  edge.style.opacity = '1';
                }}, 300 + (index * 30));
              }});
            }}
          }});
        }}
      }});
    }});

    // Start observing the document
    observer.observe(document.body, {{
      childList: true,
      subtree: true
    }});
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)


from cqss.scorer import CQSSScorer


# Helper functions for data handling
def convert_to_serializable(obj):
    """Convert objects to JSON-serializable format, handling datetime objects."""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(i) for i in obj]
    elif hasattr(obj, "model_dump"):
        return convert_to_serializable(obj.model_dump())
    else:
        return obj


# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        return convert_to_serializable(obj)


# Path to the capsule chain file
CHAIN_PATH = "capsule_chain.jsonl"

# --- Color Palette for Graphviz (cannot use CSS vars) ---
# These are carefully chosen to be distinct but not jarring.
PALETTE = {
    "light": {
        "introspective": "#a5b4fc",  # Lighter Purple-Blue
        "joint": "#86efac",  # Lighter Green
        "refusal": "#fca5a5",  # Lighter Red
        "merge": "#fcd34d",  # Lighter Amber
        "perspective": "#c4b5fd",  # Lighter Purple
        "default": "#e5e7eb",  # Lighter Gray
    },
    "dark": {
        "introspective": "#818cf8",  # Desaturated Purple-Blue
        "joint": "#4ade80",  # Desaturated Green
        "refusal": "#f87171",  # Desaturated Red
        "merge": "#fbbf24",  # Desaturated Amber
        "perspective": "#a78bfa",  # Desaturated Purple
        "default": "#6b7280",  # Desaturated Gray
    },
}


@st.cache_data
def load_capsules_from_jsonl(path):
    """Load capsules from a JSONL file, caching the result."""
    capsules = []
    try:
        with open(path) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    capsules.append(Capsule.model_validate(data))
    except FileNotFoundError:
        st.error(f"Error: The file '{path}' was not found.")
    except Exception as e:
        st.error(f"Error parsing file: {e}")
    return capsules


def create_chain_graph(capsules, detailed_view=False, focus_id=None, dark_mode=False):
    """Build a Graphviz Digraph, optionally focusing on a specific capsule."""
    dot = graphviz.Digraph("UATP-Capsule-Chain", comment="UATP Capsule Chain")

    theme = "dark" if dark_mode else "light"
    graph_palette = PALETTE[theme]

    # Set graph attributes based on theme
    dot.attr(
        "graph",
        rankdir="LR",
        splines="spline",
        nodesep="0.6" if detailed_view else "0.4",
        ranksep="1.0" if detailed_view else "0.7",
        bgcolor="transparent",
        margin="0.2",
    )

    dot.attr(
        "node",
        style="filled",
        fontname="Inter",
        fontsize="10",
        fontcolor=graph_palette["default"] if theme == "light" else "#e5e5e5",
        penwidth="0.5",
    )

    dot.attr("edge", penwidth="0.8", color=graph_palette["default"], arrowsize="0.7")

    for capsule in capsules:
        # Use the Graphviz palette
        color = graph_palette.get(
            capsule.capsule_type.lower(), graph_palette["default"]
        )

        # More elegant shapes
        shape = "circle" if capsule.capsule_type == "Merge" else "box"

        # Adjust label and tooltip based on detail level
        if detailed_view:
            score = CQSSScorer.calculate_score(capsule)["total_score"]
            label = (
                f"{capsule.capsule_type}\nID: {capsule.capsule_id[:8]}\nCQSS: {score}"
            )
            # Enhanced tooltip with more info and full ID for selection
            timestamp_str = capsule.timestamp
            if hasattr(capsule.timestamp, "strftime"):
                timestamp_str = capsule.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            tooltip = f"ID: {capsule.capsule_id}\nType: {capsule.capsule_type}\nTime: {timestamp_str}"
        else:
            label = capsule.capsule_type
            # Always show full ID in tooltip for selection
            tooltip = f"ID: {capsule.capsule_id}"

        # Determine if the node should be faded
        is_faded = False
        if focus_id:
            focus_capsule = next(
                (c for c in capsules if c.capsule_id == focus_id), None
            )
            if focus_capsule:
                connections = {focus_id, focus_capsule.previous_capsule_id}
                connections.update(focus_capsule.merged_from_ids or [])
                # Get direct children
                children_ids = {
                    c.capsule_id for c in capsules if c.previous_capsule_id == focus_id
                }
                connections.update(children_ids)
                if capsule.capsule_id not in connections:
                    is_faded = True

        fill_color = color
        font_color = "#FFFFFF" if theme == "dark" else "#222222"

        if is_faded:
            fill_color = f"{color}40"  # Add alpha for faded effect
            font_color = "#9ca3af" if theme == "dark" else "#d1d5db"

        dot.node(
            capsule.capsule_id,
            label=label,
            fillcolor=fill_color,
            shape=shape,
            tooltip=tooltip,
            fontcolor=font_color,
            color=f"{color}80",
        )

    for capsule in capsules:
        is_faded = False
        if focus_id:
            focus_capsule = next(
                (c for c in capsules if c.capsule_id == focus_id), None
            )
            if focus_capsule:
                # Fade edges not connected to the focused node
                if (
                    capsule.capsule_id != focus_id
                    and capsule.previous_capsule_id != focus_id
                ):
                    is_faded = True

        edge_color = graph_palette["default"]
        if is_faded:
            edge_color = f"{edge_color}40"

        if capsule.previous_capsule_id:
            dot.edge(capsule.previous_capsule_id, capsule.capsule_id, color=edge_color)
        if capsule.capsule_type == "Merge" and capsule.merged_from_ids:
            for merged_id in capsule.merged_from_ids:
                dot.edge(
                    merged_id, capsule.capsule_id, style="dashed", color=edge_color
                )

    return dot


def display_sidebar(capsules, capsule_map):
    """Manages the sidebar for capsule selection and inspection."""
    # Minimal sidebar header
    st.sidebar.markdown(
        "<h2 style='font-weight:300;margin-bottom:1.5rem;'>Capsule Inspector</h2>",
        unsafe_allow_html=True,
    )

    if not capsules:
        st.sidebar.info("No capsules to inspect.")
        return None

    # Create a minimal dropdown to select capsules
    st.sidebar.markdown(
        "<span style='color:#9e9e9e;font-size:0.8rem;'>SELECT CAPSULE</span>",
        unsafe_allow_html=True,
    )
    capsule_options = [f"{c.capsule_type}: {c.capsule_id[:8]}" for c in capsules]
    selected_index = st.sidebar.selectbox(
        "",  # Empty label for minimalism
        range(len(capsule_options)),
        format_func=lambda i: capsule_options[i],
    )

    selected_capsule = capsules[selected_index]
    selected_id = selected_capsule.capsule_id

    # Display capsule details in the sidebar with minimal styling
    with st.sidebar:
        # Subtle divider
        st.markdown(
            "<hr style='margin:1.5rem 0;border:none;border-top:1px solid #f0f0f0;'>",
            unsafe_allow_html=True,
        )

        # Capsule type header with color indicator using CSS variables
        capsule_type_css_var = (
            f"var(--{selected_capsule.capsule_type.lower()}, var(--default-capsule))"
        )
        st.markdown(
            f"<h3 style='font-weight:300;margin-bottom:1rem;'><span style='display:inline-block;width:10px;height:10px;background-color:{capsule_type_css_var};border-radius:50%;margin-right:8px;'></span>{selected_capsule.capsule_type} Capsule</h3>",
            unsafe_allow_html=True,
        )

        # --- Overview Section ---
        with st.sidebar.expander("Overview", expanded=True):
            # More elegant metadata display
            st.markdown(
                f"<span style='color:#9e9e9e;font-size:0.8rem;'>CAPSULE ID</span><br/><span style='font-family:monospace;font-size:0.9rem;'>{selected_capsule.capsule_id}</span>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<span style='color:#9e9e9e;font-size:0.8rem;'>AGENT ID</span><br/><span style='font-size:0.9rem;'>{selected_capsule.agent_id}</span>",
                unsafe_allow_html=True,
            )

            # Handle timestamp whether it's a string or datetime object
            timestamp_display = selected_capsule.timestamp
            if hasattr(selected_capsule.timestamp, "strftime"):
                timestamp_display = selected_capsule.timestamp.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            st.markdown(
                f"<span style='color:#9e9e9e;font-size:0.8rem;'>TIMESTAMP</span><br/><span style='font-size:0.9rem;'>{timestamp_display}</span>",
                unsafe_allow_html=True,
            )

        # --- CQSS Score Section ---
        with st.sidebar.expander("CQSS Score"):
            cqss_result = CQSSScorer.calculate_score(selected_capsule)
            score = cqss_result["total_score"]

            # Create a minimal score display
            st.markdown(
                f"""
            <div style="margin-bottom:1rem;">
                <span style="color:#9e9e9e;font-size:0.8rem;">TOTAL SCORE</span>
                <div style="display:flex;align-items:center;margin-top:0.3rem;">
                    <span style="font-size:1.8rem;font-weight:300;margin-right:0.8rem;">{score}</span>
                    <div style="flex-grow:1;background-color:#f5f5f5;height:6px;border-radius:3px;">
                        <div style="width:{score}%;height:100%;background-color:#424242;border-radius:3px;"></div>
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Display individual scores with minimal styling
            st.markdown(
                "<span style='color:#9e9e9e;font-size:0.8rem;'>COMPONENT SCORES</span>",
                unsafe_allow_html=True,
            )

            # Create a clean component scores display
            for component, score in cqss_result.items():
                if component != "total_score":
                    component_name = component.replace("_", " ").title()
                    st.markdown(
                        f"""
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:0.5rem;">
                        <span style="font-size:0.9rem;">{component_name}</span>
                        <div style="display:flex;align-items:center;">
                            <span style="font-size:0.9rem;margin-right:0.5rem;">{score}</span>
                            <div style="width:50px;background-color:#f5f5f5;height:4px;border-radius:2px;">
                                <div style="width:{score}%;height:100%;background-color:#9e9e9e;border-radius:2px;"></div>
                            </div>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        # --- Reasoning Trace Section ---
        with st.sidebar.expander("Reasoning Trace"):
            if (
                hasattr(selected_capsule, "reasoning_trace")
                and selected_capsule.reasoning_trace
            ):
                if hasattr(selected_capsule.reasoning_trace, "content"):
                    st.markdown(
                        "<span style='color:#9e9e9e;font-size:0.8rem;'>TRACE CONTENT</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<div style='font-size:0.9rem;background-color:#fafafa;padding:0.8rem;border-radius:4px;margin-top:0.3rem;'>{selected_capsule.reasoning_trace.content}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        "<div style='color:#9e9e9e;font-style:italic;font-size:0.9rem;'>No content in reasoning trace.</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    "<div style='color:#9e9e9e;font-style:italic;font-size:0.9rem;'>No reasoning trace available.</div>",
                    unsafe_allow_html=True,
                )

        # --- Raw Data Section ---
        with st.sidebar.expander("Raw Data"):
            st.markdown(
                "<span style='color:#9e9e9e;font-size:0.8rem;'>CAPSULE JSON</span>",
                unsafe_allow_html=True,
            )
            # Use Pydantic's built-in JSON serialization to handle complex objects
            json_data = selected_capsule.model_dump_json(indent=2)
            st.markdown(
                f"<div style='font-family:monospace;font-size:0.85rem;background-color:#fafafa;padding:0.8rem;border-radius:4px;margin-top:0.3rem;overflow-x:auto;'>{json_data}</div>",
                unsafe_allow_html=True,
            )

        # --- Focus Mode Button ---
        if st.sidebar.button("✨ Focus on this Capsule"):
            st.session_state["focus_id"] = selected_id

        return selected_id
    return None


def display_timeline_view(capsules, capsule_map):
    """Display capsules in a chronological timeline view."""
    # Minimal header
    st.markdown(
        "<h2 style='font-weight:300;margin-bottom:1.5rem;'>Capsule Timeline</h2>",
        unsafe_allow_html=True,
    )

    if not capsules:
        st.info("No capsules to display.")
        return

    # Sort capsules by timestamp, handling both datetime objects and strings
    def get_timestamp_for_sorting(capsule):
        if hasattr(capsule.timestamp, "strftime"):  # It's a datetime object
            return capsule.timestamp
        elif isinstance(capsule.timestamp, str):  # It's a string
            # Try to parse it as ISO format
            try:
                return datetime.datetime.fromisoformat(
                    capsule.timestamp.replace("Z", "+00:00")
                )
            except ValueError:
                # If parsing fails, return the string (will be sorted lexicographically)
                return capsule.timestamp
        return capsule.timestamp  # Fallback

    sorted_capsules = sorted(capsules, key=get_timestamp_for_sorting)

    # Get focus ID from session state if available
    focus_id = st.session_state.get("focus_id")

    # Add a vertical timeline line
    st.markdown(
        """
    <style>
    .timeline-line {
        position: absolute;
        left: 10px;
        top: 0;
        bottom: 0;
        width: 1px;
        background-color: #e0e0e0;
    }
    </style>
    <div class="timeline-line"></div>
    """,
        unsafe_allow_html=True,
    )

    # Display timeline
    for capsule in sorted_capsules:
        # Determine if this capsule should be highlighted
        is_highlighted = focus_id == capsule.capsule_id

        # Format timestamp for display
        if hasattr(capsule.timestamp, "strftime"):  # It's a datetime object
            timestamp_str = capsule.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(capsule.timestamp, str):  # It's a string
            # Try to format it nicely if it's ISO format
            if "T" in capsule.timestamp:
                try:
                    parts = capsule.timestamp.split("T")
                    date_part = parts[0]
                    time_part = (
                        parts[1].split(".")[0]
                        if "." in parts[1]
                        else parts[1].split("Z")[0]
                    )
                    timestamp_str = f"{date_part} {time_part}"
                except:
                    timestamp_str = capsule.timestamp
            else:
                timestamp_str = capsule.timestamp
        else:
            timestamp_str = str(capsule.timestamp)

        # Use CSS variables for the background color hint, with a fallback
        bg_color = f"var(--{capsule.capsule_type.lower()}, var(--default-capsule))"

        # Determine if this capsule should be highlighted
        is_highlighted = focus_id == capsule.capsule_id

        # Create a dot marker for the timeline
        dot_color = "#424242" if is_highlighted else "#9e9e9e"
        st.markdown(
            f"""
        <div style="position:absolute; left:5px; width:10px; height:10px; background-color:{dot_color}; border-radius:50%; margin-top:10px;"></div>
        """,
            unsafe_allow_html=True,
        )

        # Create elegant, minimalist expandable card for each capsule
        with st.expander(
            f"{timestamp_str} · {capsule.capsule_type}", expanded=is_highlighted
        ):
            # Add a subtle top border in the capsule type color
            st.markdown(
                f"""
            <div style="border-top:2px solid {bg_color}; margin-bottom:1rem;"></div>
            """,
                unsafe_allow_html=True,
            )

            # Two columns: left for metadata, right for content
            col1, col2 = st.columns([1, 2])

            with col1:
                # More elegant metadata display
                st.markdown(
                    f"<span style='color:#9e9e9e;font-size:0.8rem;'>ID</span><br/><span style='font-family:monospace;font-size:0.9rem;'>{capsule.capsule_id[:8]}...</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<span style='color:#9e9e9e;font-size:0.8rem;'>TYPE</span><br/><span style='font-size:0.9rem;'>{capsule.capsule_type}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<span style='color:#9e9e9e;font-size:0.8rem;'>AGENT</span><br/><span style='font-size:0.9rem;'>{capsule.agent_id}</span>",
                    unsafe_allow_html=True,
                )

                # Show connections with minimal styling
                if capsule.previous_capsule_id:
                    prev_capsule = capsule_map.get(capsule.previous_capsule_id)
                    prev_type = prev_capsule.capsule_type if prev_capsule else "Unknown"
                    st.markdown(
                        f"<span style='color:#9e9e9e;font-size:0.8rem;'>PREVIOUS</span><br/><span style='font-size:0.9rem;'>{prev_type} <span style='font-family:monospace;color:#9e9e9e;'>{capsule.previous_capsule_id[:6]}...</span></span>",
                        unsafe_allow_html=True,
                    )

                if capsule.capsule_type == "Merge" and capsule.merged_from_ids:
                    st.markdown(
                        "<span style='color:#9e9e9e;font-size:0.8rem;'>MERGED FROM</span>",
                        unsafe_allow_html=True,
                    )
                    for merged_id in capsule.merged_from_ids:
                        merged_capsule = capsule_map.get(merged_id)
                        merged_type = (
                            merged_capsule.capsule_type if merged_capsule else "Unknown"
                        )
                        st.markdown(
                            f"<span style='font-size:0.9rem;'>{merged_type} <span style='font-family:monospace;color:#9e9e9e;'>{merged_id[:6]}...</span></span>",
                            unsafe_allow_html=True,
                        )

            with col2:
                # Show CQSS score with minimal styling
                cqss_result = CQSSScorer.calculate_score(capsule)
                score = cqss_result["total_score"]

                # Create a minimal score display
                st.markdown(
                    f"""
                <div style="margin-bottom:1rem;">
                    <span style="color:#9e9e9e;font-size:0.8rem;">CQSS SCORE</span><br/>
                    <div style="display:flex;align-items:center;margin-top:0.3rem;">
                        <span style="font-size:1.5rem;font-weight:300;margin-right:0.5rem;">{score}</span>
                        <div style="flex-grow:1;background-color:#f5f5f5;height:4px;border-radius:2px;">
                            <div style="width:{score}%;height:100%;background-color:#424242;border-radius:2px;"></div>
                        </div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                # Show content preview with minimal styling
                if hasattr(capsule, "content") and capsule.content:
                    st.markdown(
                        "<span style='color:#9e9e9e;font-size:0.8rem;'>CONTENT</span>",
                        unsafe_allow_html=True,
                    )
                    content_preview = (
                        capsule.content[:200] + "..."
                        if len(capsule.content) > 200
                        else capsule.content
                    )
                    st.markdown(
                        f"<div style='font-size:0.9rem;background-color:#fafafa;padding:0.8rem;border-radius:4px;'>{content_preview}</div>",
                        unsafe_allow_html=True,
                    )

                # Minimal button to select this capsule
                if st.button(
                    "Focus",
                    key=f"select_{capsule.capsule_id}",
                    use_container_width=False,
                ):
                    st.session_state["focus_id"] = capsule.capsule_id
                    st.rerun()


def display_data_inspector(capsules):
    """Displays a searchable, sortable table of all capsules."""
    st.header("Data Inspector")

    if not capsules:
        st.info("No capsules to display.")
        return

    # Convert capsules to DataFrame for display
    capsule_data = []
    for capsule in capsules:
        # Extract basic data and ensure it's serializable
        data = {
            "capsule_id": capsule.capsule_id[:8] + "...",
            "capsule_type": capsule.capsule_type,
            "agent_id": capsule.agent_id,
            "timestamp": convert_to_serializable(capsule.timestamp),
        }

        # Add CQSS score
        data["cqss_score"] = CQSSScorer.calculate_score(capsule)["total_score"]

        # Add reasoning trace summary if available
        if hasattr(capsule, "reasoning_trace") and capsule.reasoning_trace:
            if hasattr(capsule.reasoning_trace, "content"):
                content = convert_to_serializable(capsule.reasoning_trace.content)
                data["reasoning"] = (
                    content[:50] + "..." if len(content) > 50 else content
                )
            else:
                data["reasoning"] = "No content"
        else:
            data["reasoning"] = "N/A"

        capsule_data.append(data)

    # Create DataFrame with serializable data
    df = pd.DataFrame(capsule_data)

    # Reorder columns for better readability
    cols_order = [
        "capsule_id",
        "capsule_type",
        "timestamp",
        "agent_id",
        "cqss_score",
        "reasoning",
    ]
    cols_order = [col for col in cols_order if col in df.columns] + [
        col for col in df.columns if col not in cols_order
    ]
    df = df[cols_order]

    # Display as interactive table with minimal styling
    st.markdown(
        "<span style='color:#9e9e9e;font-size:0.8rem;'>CAPSULE DATA</span>",
        unsafe_allow_html=True,
    )
    st.dataframe(df, use_container_width=True)


def apply_filters(capsules):
    """Apply filters to the capsule list based on sidebar filter settings."""
    # Initialize session state for filters if not present
    if "filter_types" not in st.session_state:
        st.session_state["filter_types"] = []
    if "filter_start_date" not in st.session_state:
        st.session_state["filter_start_date"] = None
    if "filter_end_date" not in st.session_state:
        st.session_state["filter_end_date"] = None

    # Get unique capsule types
    all_types = sorted({c.capsule_type for c in capsules})

    # Display filter controls in sidebar
    with st.sidebar:
        st.subheader("📊 Filter Capsules")

        # Filter by capsule type
        st.write("**Filter by Type:**")
        selected_types = []
        for capsule_type in all_types:
            if st.checkbox(capsule_type, value=True, key=f"filter_{capsule_type}"):
                selected_types.append(capsule_type)

        # Filter by date range
        st.write("**Filter by Date Range:**")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start", value=None, key="start_date")
        with col2:
            end_date = st.date_input("End", value=None, key="end_date")

        # Apply filters button
        if st.button("Apply Filters"):
            st.session_state["filter_types"] = selected_types
            st.session_state["filter_start_date"] = (
                start_date if start_date != None else None
            )
            st.session_state["filter_end_date"] = end_date if end_date != None else None

        # Reset filters button
        if st.button("Reset Filters"):
            st.session_state["filter_types"] = []
            st.session_state["filter_start_date"] = None
            st.session_state["filter_end_date"] = None
            # Reset checkboxes
            for capsule_type in all_types:
                st.session_state[f"filter_{capsule_type}"] = True

    # Apply filters to capsules
    filtered_capsules = capsules

    # Filter by type if types are selected
    if st.session_state["filter_types"]:
        filtered_capsules = [
            c
            for c in filtered_capsules
            if c.capsule_type in st.session_state["filter_types"]
        ]

    # Filter by date range
    if st.session_state["filter_start_date"] or st.session_state["filter_end_date"]:
        filtered_capsules = [
            c
            for c in filtered_capsules
            if _is_in_date_range(
                c,
                st.session_state["filter_start_date"],
                st.session_state["filter_end_date"],
            )
        ]

    return filtered_capsules


def _is_in_date_range(capsule, start_date, end_date):
    """Check if a capsule's timestamp is within the given date range."""
    # Convert timestamp to datetime if it's a string
    timestamp = capsule.timestamp
    if isinstance(timestamp, str):
        try:
            from datetime import datetime

            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return True  # If we can't parse the date, include it

    # Extract date from datetime
    from datetime import date

    capsule_date = timestamp.date() if hasattr(timestamp, "date") else date.today()

    # Check if within range
    if start_date and capsule_date < start_date:
        return False
    if end_date and capsule_date > end_date:
        return False
    return True


def main():
    """Main function to run the Streamlit app."""
    # Initialize session state for dark mode. This must be the first Streamlit command.
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False

    st.set_page_config(layout="wide", page_title="UATP Visualizer")

    # Apply the global design. This MUST be called right after set_page_config.
    apply_global_design(st.session_state.dark_mode)

    # --- Header --- #
    col_logo, col_toggle = st.columns([3, 1])
    with col_logo:
        st.markdown(
            "<h1 style='font-weight:300; margin:0; padding:0;'>UATP Capsule Visualizer</h1>",
            unsafe_allow_html=True,
        )
    with col_toggle:
        # This simple toggle assignment is the correct way to manage state in Streamlit.
        st.session_state.dark_mode = st.toggle(
            "Dark Mode", value=st.session_state.dark_mode, key="dark_mode_toggle"
        )

    capsules = load_capsules_from_jsonl(CHAIN_PATH)
    if not capsules:
        st.warning(f"No capsules found in '{CHAIN_PATH}'. Create a chain first.")
        return

    # Apply filters
    filtered_capsules = apply_filters(capsules)

    capsule_map = {c.capsule_id: c for c in filtered_capsules}

    # Initialize focus_id in session state if not present
    if "focus_id" not in st.session_state:
        st.session_state["focus_id"] = None

    selected_id = display_sidebar(filtered_capsules, capsule_map)

    # --- Main Panel with Tabs ---
    graph_tab, timeline_tab, data_tab = st.tabs(["Graph", "Timeline", "Data"])

    with graph_tab:
        st.header("Capsule Chain Graph")
        col1, col2 = st.columns([3, 1])
        with col1:
            detailed_view = st.toggle(
                "Show Detailed View", value=False, key="detail_toggle"
            )
        with col2:
            if st.button("Clear Focus"):
                st.session_state["focus_id"] = None

        try:
            graph = create_chain_graph(
                filtered_capsules,
                detailed_view=detailed_view,
                focus_id=st.session_state.get("focus_id"),
                dark_mode=st.session_state.dark_mode,
            )
            st.graphviz_chart(graph, use_container_width=True)

            # Add interactive selection form below the graph
            st.write(
                "**Tip**: Hover over any node to see its full ID, then use the form below to select it."
            )
            with st.form("capsule_selector_form"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    selected_capsule_id = st.text_input(
                        "Enter Capsule ID to select:",
                        value=st.session_state.get("focus_id", ""),
                        placeholder="Hover over a node to see its ID",
                    )
                with col2:
                    submitted = st.form_submit_button("Select Capsule")

                if submitted and selected_capsule_id in capsule_map:
                    st.session_state["focus_id"] = selected_capsule_id
                    st.rerun()
                elif submitted and selected_capsule_id:
                    st.error(f"Capsule ID '{selected_capsule_id}' not found.")
        except Exception as e:
            st.error(f"Failed to render graph: {e}")
            st.exception(e)

    with timeline_tab:
        display_timeline_view(filtered_capsules, capsule_map)

    with data_tab:
        display_data_inspector(filtered_capsules)


if __name__ == "__main__":
    main()
