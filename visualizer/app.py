import os
import sys

import streamlit as st

# Add project root and src directory to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from engine.legacy_capsule_engine import LegacyCapsuleEngine
from utils.database_loader import (
    load_capsules_cached,
    get_capsule_stats_cached,
    search_capsules_cached,
)

# Try to import specialized components, fallback if not available
try:
    from engine.specialized_engine import SpecializedCapsuleEngine

    SPECIALIZED_ENGINE_AVAILABLE = True
except ImportError:
    SPECIALIZED_ENGINE_AVAILABLE = False
    SpecializedCapsuleEngine = None

try:
    # Try to import specialized capsules, but handle gracefully if they fail
    from capsules.specialized_capsules import (
        AncestralKnowledgeCapsule,
        EmbodiedCapsule,
        InfluenceCapsule,
        IntrospectiveCapsule,
        JointCapsule,
        LifecycleCapsule,
        MetaCapsule,
        PerspectiveCapsule,
        RefusalCapsule,
        SpecializedCapsule,
    )

    SPECIALIZED_CAPSULES_AVAILABLE = True
except ImportError:
    SPECIALIZED_CAPSULES_AVAILABLE = False
# Try to import optional components
try:
    from cqss.simulator import simulate_cqss_for_capsule

    CQSS_AVAILABLE = True
except ImportError:
    CQSS_AVAILABLE = False

try:
    from visualizer.components.inspector import render_inspector

    INSPECTOR_AVAILABLE = True
except ImportError:
    INSPECTOR_AVAILABLE = False

try:
    from visualizer.components.specialized_inspector import render_specialized_inspector

    SPECIALIZED_INSPECTOR_AVAILABLE = True
except ImportError:
    SPECIALIZED_INSPECTOR_AVAILABLE = False

try:
    from visualizer.components.specialized_creator import render_specialized_creator

    SPECIALIZED_CREATOR_AVAILABLE = True
except ImportError:
    SPECIALIZED_CREATOR_AVAILABLE = False
import tempfile
import time
import urllib.parse
from functools import wraps

import networkx as nx
import requests
from engine.cqss import compute_cqss
from pyvis.network import Network

from visualizer.components.capsule_network import render_capsule_network
from visualizer.components.capsule_timeline import render_capsule_timeline
from visualizer.components.protocol_guidelines import render_protocol_guidelines
from visualizer.components.reference_capsules_viewer import (
    render_reference_capsules_viewer,
)
from visualizer.utils.colors import CAPSULE_TYPE_COLORS
from visualizer.utils.capsule_compat import (
    get_capsule_id,
    get_capsule_type,
    get_parent_capsule_id,
    get_confidence_score,
    get_reasoning_steps,
    is_valid_capsule,
)

# Settings
AGENT_ID = os.getenv("UATP_AGENT_ID", "demo-agent-007")
# Set up the correct path for the chain file
DEFAULT_CHAIN_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "capsule_chain.jsonl"
)
CHAIN_PATH = os.getenv("UATP_CHAIN_PATH", DEFAULT_CHAIN_PATH)

# Reasoning API configuration
API_HOST = os.getenv("UATP_API_HOST", "localhost")
API_PORT = os.getenv("UATP_API_PORT", "5006")
API_KEY = os.getenv("UATP_DEMO_API_KEY", "test-key")
API_BASE_URL = f"http://{API_HOST}:{API_PORT}/reasoning"


# --- API Client Helpers ---


def normalize_reasoning_steps(reasoning_trace):
    """
    Normalizes reasoning steps into a standard format expected by the API.
    Works with both dict objects and class instances.
    """
    if not reasoning_trace:
        return []

    steps_data = []
    for step in reasoning_trace:
        # If step is a dict, use as is; if object, extract fields
        if isinstance(step, dict):
            content = step.get("content")
            step_type = step.get("step_type")
            confidence = step.get("confidence")
            metadata = step.get("metadata", {})
        else:
            content = getattr(step, "content", str(step))
            step_type = getattr(step, "step_type", "OBSERVATION")
            if hasattr(step_type, "name"):
                step_type = step_type.name.upper()
            else:
                step_type = str(step_type).upper()
            confidence = getattr(step, "confidence", 1.0)
            metadata = getattr(step, "metadata", {})
        steps_data.append(
            {
                "content": content,
                "step_type": step_type
                if isinstance(step_type, str)
                else str(step_type).upper(),
                "confidence": confidence,
                "metadata": metadata,
            }
        )
    return steps_data


def with_retry(max_retries=3, backoff_factor=0.5):
    """
    Decorator that adds retry logic to API calls with exponential backoff.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except (
                    requests.exceptions.RequestException,
                    requests.exceptions.Timeout,
                ) as e:
                    wait_time = backoff_factor * (2**retries)
                    retries += 1
                    if retries > max_retries:
                        return {
                            "error": f"API call failed after {max_retries} retries: {str(e)}"
                        }
                    time.sleep(wait_time)

        return wrapper

    return decorator


@with_retry()
def call_api_endpoint(endpoint, data, timeout=10):
    """
    Generic function to call any reasoning API endpoint with proper error handling and retry logic.
    """
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    url = urllib.parse.urljoin(API_BASE_URL + "/", endpoint)
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=timeout)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": f"API Error {resp.status_code}: {resp.text}"}
    except Exception as ex:
        return {"error": str(ex)}


def call_reasoning_batch_analyze_api(reasoning_traces):
    """
    Calls the /reasoning/analyze-batch endpoint with multiple reasoning traces.
    Returns the batch analysis result dict or error message.
    """
    # Input validation
    if not reasoning_traces or len(reasoning_traces) == 0:
        return {"error": "No reasoning traces provided"}

    batch_data = []
    for i, trace in enumerate(reasoning_traces):
        if not trace:
            continue
        steps_data = normalize_reasoning_steps(trace)
        batch_data.append(
            {"id": f"trace_{i}", "reasoning_trace": {"steps": steps_data}}
        )

    if not batch_data:
        return {"error": "All provided reasoning traces were empty"}

    data = {"batch": batch_data}
    return call_api_endpoint("analyze-batch", data)


def call_reasoning_compare_api(reasoning_trace1, reasoning_trace2):
    """
    Calls the /reasoning/compare endpoint with two reasoning traces.
    Returns the comparison result dict or error message.
    """
    # Input validation
    if not reasoning_trace1 or not reasoning_trace2:
        return {"error": "One or both reasoning traces are empty"}

    steps_data1 = normalize_reasoning_steps(reasoning_trace1)
    steps_data2 = normalize_reasoning_steps(reasoning_trace2)

    data = {
        "reasoning_trace1": {"steps": steps_data1},
        "reasoning_trace2": {"steps": steps_data2},
    }
    return call_api_endpoint("compare", data)


def call_reasoning_analyze_api(reasoning_trace):
    """
    Calls the /reasoning/analyze endpoint with a reasoning trace.
    Returns the analysis result dict or error message.
    """
    # Input validation
    if not reasoning_trace:
        return {"error": "Empty reasoning trace provided"}

    steps_data = normalize_reasoning_steps(reasoning_trace)
    data = {"reasoning_trace": {"steps": steps_data}}
    return call_api_endpoint("analyze", data)


def call_reasoning_validate_api(reasoning_trace):
    """
    Calls the /reasoning/validate endpoint with a reasoning trace.
    Returns the validation result dict or error message.
    """
    # Input validation
    if not reasoning_trace:
        return {"error": "Empty reasoning trace provided"}

    steps_data = normalize_reasoning_steps(reasoning_trace)
    data = {"reasoning_trace": {"steps": steps_data}}
    return call_api_endpoint("validate", data)


# --- UI Helper Functions ---

# Using centralized color palette
# Extend with additional types if necessary
for capsule_type in [
    "Meta",
    "Influence",
    "Lifecycle",
    "Embodied",
    "AncestralKnowledge",
]:
    if capsule_type not in CAPSULE_TYPE_COLORS:
        CAPSULE_TYPE_COLORS[capsule_type] = "#bdbdbd"  # Default gray for unknown types


def display_capsule_details(capsule, index):
    """Renders a single capsule's details in a formatted block."""
    color = CAPSULE_TYPE_COLORS.get(
        capsule.capsule_type, CAPSULE_TYPE_COLORS["DEFAULT"]
    )
    st.markdown(
        f"<div style='background:{color};padding:10px;border-radius:8px;border: 2px solid #444;'>",
        unsafe_allow_html=True,
    )
    st.markdown(f"**Capsule #{index+1}: {capsule.capsule_type}**")
    st.markdown(f"<small>ID: {capsule.capsule_id}</small>", unsafe_allow_html=True)
    st.markdown(f"- **Agent:** `{capsule.agent_id}`")
    st.markdown(f"- **Timestamp:** `{capsule.timestamp}`")
    st.markdown(f"- **Confidence:** `{capsule.confidence}`")
    st.markdown(f"- **Previous Capsule:** `{capsule.previous_capsule_id}`")
    st.markdown(f"- **Signature:** `{capsule.signature[:40]}...`")
    with st.expander("Reasoning Trace"):
        for i, step in enumerate(capsule.reasoning_trace):
            st.text(f"{i+1}. {step}")
    with st.expander("Metadata"):
        st.json(capsule.metadata)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Main Application UI ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "Chain Explorer",
            "Inspector",
            "Creator",
            "Analyzer",
            "Relationships",
            "Reference Models",
        ]
    )
    st.title("UATP Capsule Chain Visualizer")

    # Reference Models Tab
    with tab6:
        # Render the reference capsules viewer component
        render_reference_capsules_viewer()

        # Add option to add reference capsules to chain
        st.divider()
        st.markdown("### Add Reference Capsule to Chain")
        st.markdown(
            "Use these options to add selected reference capsules directly to your chain for testing."
        )

        capsule_type = st.selectbox(
            "Select reference capsule type to add",
            ["ideal", "economic", "remix"],
            key="ref_capsule_type",
        )

        if st.button("Add Reference Capsule to Chain"):
            from visualizer.components.reference_capsules_viewer import (
                add_reference_capsule_to_chain,
            )

            with st.spinner(f"Adding {capsule_type} reference capsule to chain..."):
                capsule_id = add_reference_capsule_to_chain(engine, capsule_type)
                if capsule_id:
                    st.success(
                        f"Successfully added reference capsule to chain: {capsule_id}"
                    )
                    st.info(
                        "Please navigate to the Chain Explorer tab to see your new capsule."
                    )
                else:
                    st.error(
                        "Failed to add reference capsule to chain. Check console for errors."
                    )


# Load chain using Specialized Capsule Engine if available
if SPECIALIZED_ENGINE_AVAILABLE and SpecializedCapsuleEngine:
    try:
        engine = SpecializedCapsuleEngine(agent_id=AGENT_ID, storage_path=CHAIN_PATH)
        st.sidebar.success("✅ Using specialized UATP 7.0 capsule engine")
    except Exception as e:
        st.sidebar.warning(f"⚠️ Falling back to basic capsule engine: {str(e)}")
        engine = LegacyCapsuleEngine(agent_id=AGENT_ID, storage_path=CHAIN_PATH)
else:
    st.sidebar.info("ℹ️ Using basic capsule engine (specialized engine not available)")
    engine = LegacyCapsuleEngine(agent_id=AGENT_ID, storage_path=CHAIN_PATH)
chain = list(engine.load_chain())

# Create capsule map for lookup and store in session state
capsule_map = {capsule.capsule_id: capsule for capsule in chain}
st.session_state["capsule_map"] = capsule_map

if not chain:
    st.warning("No capsules found in the chain file.")
    st.info(f"Chain file path: {CHAIN_PATH}")
    st.info(f"File exists: {os.path.exists(CHAIN_PATH)}")
    if os.path.exists(CHAIN_PATH):
        st.info(f"File size: {os.path.getsize(CHAIN_PATH)} bytes")
else:
    # Show successful load info in sidebar
    st.sidebar.success(f"✅ Loaded {len(chain)} capsules from chain")
    # --- Sidebar Controls ---
    st.sidebar.header("Chain Controls & Info")

    # CQSS Dashboard
    try:
        import asyncio

        cqss = asyncio.run(compute_cqss(chain, engine.verify_capsule))
        cqss_dict = cqss.as_dict()

        # Calculate overall score manually if method not available
        try:
            # First try to use the method if it exists
            if hasattr(cqss, "get_overall_score"):
                overall_score = cqss.get_overall_score()
                # Scale the score to 0-100 range from the 0-1 range
                if overall_score is not None:
                    overall_score = overall_score * 100
            else:
                # Calculate manually using the same formula as in CQSSResult.get_overall_score
                weights = {
                    "integrity_score": 0.3,
                    "verification_ratio": 0.2,
                    "trust_score": 0.2,
                    "complexity_score": 0.15,
                    "diversity_score": 0.15,
                }

                weighted_sum = 0
                weight_total = 0

                for key, weight in weights.items():
                    if key in cqss_dict and cqss_dict[key] is not None:
                        # Scale down score metrics that are in 0-100 range to 0-1
                        value = cqss_dict[key]
                        if key != "verification_ratio":  # already in 0-1 range
                            value = value / 100.0
                        weighted_sum += value * weight
                        weight_total += weight

                if weight_total > 0:
                    overall_score = (weighted_sum / weight_total) * 100
                else:
                    overall_score = None
        except Exception as e:
            st.sidebar.warning(f"Error calculating overall score: {e}")
            overall_score = None

        # Dedicated CQSS tab
        st.sidebar.subheader("CQSS Summary")
        if overall_score is not None:
            st.sidebar.metric(
                "Overall CQSS Score",
                f"{overall_score:.1f}/100",
                help="Weighted score of all quality and security factors",
            )

        # Core security metrics
        col1, col2 = st.sidebar.columns(2)

        # Safely display metrics with error handling
        try:
            if (
                "integrity_score" in cqss_dict
                and cqss_dict["integrity_score"] is not None
            ):
                col1.metric(
                    "Integrity",
                    f"{cqss_dict['integrity_score']:.1f}",
                    help="Based on valid signatures",
                )
            else:
                col1.warning("Integrity score not available")

            if "trust_score" in cqss_dict and cqss_dict["trust_score"] is not None:
                col2.metric(
                    "Trust",
                    f"{cqss_dict['trust_score']:.1f}",
                    help="Based on joint capsules and verification",
                )
            else:
                col2.warning("Trust score not available")
        except Exception as e:
            st.warning(f"Error displaying metrics: {e}")

        # Toggle for full CQSS dashboard
        if st.sidebar.checkbox("Show Full CQSS Dashboard"):
            st.header("Chain Quality & Security Score Dashboard")

            # Top metrics
            st.subheader("Primary Quality & Security Metrics")
            cols = st.columns(5)
            metrics = [
                (
                    "Integrity Score",
                    f"{cqss_dict['integrity_score']:.1f}",
                    "Based on signature verification",
                ),
                (
                    "Trust Score",
                    f"{cqss_dict['trust_score']:.1f}",
                    "Based on joint capsules and verification",
                ),
                (
                    "Complexity Score",
                    f"{cqss_dict['complexity_score']:.1f}",
                    "Based on fork/join structure",
                ),
                (
                    "Diversity Score",
                    f"{cqss_dict['diversity_score']:.1f}",
                    "Based on agent diversity",
                ),
                (
                    "Overall Score",
                    f"{overall_score:.1f}" if overall_score is not None else "N/A",
                    "Weighted average",
                ),
            ]

            for i, (label, value, help_text) in enumerate(metrics):
                cols[i].metric(label, value, help=help_text)

            # Structure metrics
            st.subheader("Chain Structure Analysis")
            cols = st.columns(4)
            cols[0].metric(
                "Roots", cqss_dict["root_count"], help="Number of starting capsules"
            )
            cols[1].metric(
                "Leaves", cqss_dict["leaf_count"], help="Number of ending capsules"
            )
            cols[2].metric(
                "Fork Points",
                cqss_dict["fork_count"],
                help="Capsules with multiple children",
            )
            cols[3].metric(
                "Join Points",
                cqss_dict["join_points"],
                help="Capsules with multiple parents",
            )

            # Path metrics
            cols = st.columns(3)
            cols[0].metric(
                "Longest Path",
                cqss_dict["longest_path"],
                help="Longest chain from root to leaf",
            )
            cols[1].metric(
                "Avg Path Length",
                cqss_dict["avg_path_length"],
                help="Average chain length",
            )
            cols[2].metric("Total Capsules", cqss_dict["chain_length"])

            # Capsule type metrics
            st.subheader("Capsule Type Analysis")
            cols = st.columns(3)
            cols[0].metric(
                "Joint Capsule %",
                f"{cqss_dict['joint_capsule_ratio']*100:.1f}%",
                help="Percentage of joint capsules (human-signed)",
            )
            cols[1].metric(
                "Introspective %",
                f"{cqss_dict['introspective_ratio']*100:.1f}%",
                help="Percentage of introspective capsules",
            )
            cols[2].metric("Avg. Confidence", f"{cqss_dict['avg_confidence']:.2f}")

            # Verification metrics
            st.subheader("Verification Status")
            cols = st.columns(2)
            cols[0].metric(
                "Valid Signatures",
                f"{cqss_dict['valid_signatures']}/{cqss_dict['chain_length']}",
            )
            cols[1].metric(
                "Verification Rate", f"{cqss_dict['verification_ratio']*100:.1f}%"
            )
    except Exception as e:
        st.error(f"Could not compute CQSS: {e}")
        import traceback

        st.error(f"Detailed error: {traceback.format_exc()}")
        st.error(f"CQSS calculation error: {e}")

    # Confidence Metrics
    st.sidebar.subheader("Confidence Metrics")

    # Calculate confidence statistics from metadata
    confidence_scores = []
    for capsule in chain:
        try:
            confidence = get_confidence_score(capsule)
            if confidence is not None:
                confidence_scores.append(confidence)
        except Exception:
            pass  # Skip invalid capsules

    if confidence_scores:
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        min_confidence = min(confidence_scores)
        max_confidence = max(confidence_scores)

        col1, col2 = st.sidebar.columns(2)
        col1.metric("Avg Confidence", f"{avg_confidence:.1%}")
        col2.metric("Min Confidence", f"{min_confidence:.1%}")

        # Confidence distribution
        high_confidence = sum(1 for c in confidence_scores if c >= 0.8)
        medium_confidence = sum(1 for c in confidence_scores if 0.5 <= c < 0.8)
        low_confidence = sum(1 for c in confidence_scores if c < 0.5)

        st.sidebar.write(f"High confidence (≥80%): {high_confidence}")
        st.sidebar.write(f"Medium confidence (50-80%): {medium_confidence}")
        st.sidebar.write(f"Low confidence (<50%): {low_confidence}")
    else:
        st.sidebar.info("No confidence data available")

    # Chain Analysis Metrics
    st.sidebar.subheader("Chain Analysis")
    G_full = nx.DiGraph()
    for c in chain:
        try:
            if not is_valid_capsule(c):
                continue

            capsule_id = get_capsule_id(c)
            if capsule_id:
                G_full.add_node(capsule_id)

                parent_id = get_parent_capsule_id(c)
                if parent_id:
                    G_full.add_edge(parent_id, capsule_id)
        except Exception:
            continue  # Skip invalid capsules

    num_capsules = len(chain)
    num_chains = len([node for node, in_degree in G_full.in_degree() if in_degree == 0])
    num_forks = len(
        [node for node, out_degree in G_full.out_degree() if out_degree > 1]
    )
    longest_chain = 0
    if num_chains > 0:
        all_paths = list(
            nx.all_simple_paths(
                G_full,
                source=[n for n, d in G_full.in_degree() if d == 0][0],
                target=[n for n, d in G_full.out_degree() if d == 0],
            )
        )
        if all_paths:
            longest_chain = len(max(all_paths, key=len))
        else:
            longest_chain = 0

    st.sidebar.metric("Total Capsules", num_capsules)
    st.sidebar.metric("Number of Chains", num_chains)
    st.sidebar.metric("Number of Forks", num_forks)
    st.sidebar.metric("Longest Chain", longest_chain)

    # Capsule Type Distribution
    st.sidebar.subheader("Capsule Types")
    type_counts = {}
    for c in chain:
        try:
            if not is_valid_capsule(c):
                continue

            capsule_type = get_capsule_type(c)
            # Clean up type display
            display_type = capsule_type.replace("_", " ").title()
            type_counts[display_type] = type_counts.get(display_type, 0) + 1
        except Exception:
            continue  # Skip invalid capsules

    for capsule_type, count in sorted(type_counts.items()):
        st.sidebar.write(f"{capsule_type}: {count}")

    # Reasoning Trace Summary
    st.sidebar.subheader("Reasoning Traces")
    traces_with_steps = 0
    total_reasoning_steps = 0

    for capsule in chain:
        try:
            if not is_valid_capsule(capsule):
                continue

            reasoning_steps = get_reasoning_steps(capsule)
            if reasoning_steps:
                traces_with_steps += 1
                total_reasoning_steps += len(reasoning_steps)
        except Exception:
            continue  # Skip invalid capsules

    col1, col2 = st.sidebar.columns(2)
    col1.metric("With Traces", traces_with_steps)
    col2.metric("Total Steps", total_reasoning_steps)

    # Filtering
    # Fork Simulation
    st.sidebar.subheader("Fork Simulation")
    parent_capsule_id = st.sidebar.selectbox(
        "Select Parent Capsule for Fork", [c.capsule_id for c in chain]
    )
    new_capsule_type = st.sidebar.selectbox(
        "New Capsule Type", ["Introspective", "Refusal", "Joint"]
    )
    reasoning_trace = st.sidebar.text_area(
        "Reasoning Trace (one step per line)", "Step 1\nStep 2"
    )

    if st.sidebar.button("Create Fork"):
        new_capsule = engine.create_capsule(
            capsule_type=new_capsule_type,
            previous_capsule_id=parent_capsule_id,
            reasoning_trace=reasoning_trace.splitlines(),
            confidence=0.95,
            metadata={"simulation": True, "forked_from": parent_capsule_id},
        )
        engine.log_capsule(new_capsule)
        st.sidebar.success(
            f"Created and logged new forked capsule: {new_capsule.capsule_id}"
        )
        st.experimental_rerun()

    st.sidebar.subheader("Filters")
    all_types = sorted(list({c.capsule_type for c in chain}))
    all_agents = sorted(list({c.agent_id for c in chain}))
    filter_type = st.sidebar.multiselect(
        "Filter by Capsule Type", all_types, default=all_types
    )
    filter_agent = st.sidebar.multiselect(
        "Filter by Agent", all_agents, default=all_agents
    )

    filtered_chain = [
        c for c in chain if c.capsule_type in filter_type and c.agent_id in filter_agent
    ]

    # --- Main View ---
    if not filtered_chain:
        st.info("No capsules match the current filter.")
    else:
        st.header("Capsule Chain Graph")
        st.info(
            "Displaying the capsule chain as a directed graph. Click and drag nodes to rearrange."
        )

        G = nx.DiGraph()
        for c in filtered_chain:
            color = CAPSULE_TYPE_COLORS.get(
                c.capsule_type, CAPSULE_TYPE_COLORS["DEFAULT"]
            )
            label = f"{c.capsule_type}\n{c.capsule_id[:8]}..."
            title = f"Capsule ID: {c.capsule_id}\nAgent: {c.agent_id}\nConfidence: {c.confidence}"
            G.add_node(c.capsule_id, label=label, color=color, title=title)
            if c.previous_capsule_id and c.previous_capsule_id in [
                p.capsule_id for p in filtered_chain
            ]:
                G.add_edge(c.previous_capsule_id, c.capsule_id)

        net = Network(
            height="700px",
            width="100%",
            directed=True,
            notebook=False,
            bgcolor="#0f0f0f",
            font_color="white",
        )
        net.from_nx(G)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
            net.save_graph(tmp_file.name)
            html_path = tmp_file.name

        with open(html_path, encoding="utf-8") as f:
            html_content = f.read()
        try:
            import streamlit.components.v1 as components

            components.html(html_content, height=720)
        except Exception as e:
            st.error(f"Error rendering network graph: {e}")
            st.text(f"HTML content length: {len(html_content)}")
            # Show a fallback message
            st.info(
                "Network visualization temporarily unavailable. Showing capsule data below."
            )

        # Capsule details on selection
        st.header("Capsule Details")
        capsule_ids = [c.capsule_id for c in filtered_chain]
        selected_id = st.selectbox(
            "Select a Capsule ID to view its details", capsule_ids
        )
        selected_capsule = (
            next((c for c in filtered_chain if c.capsule_id == selected_id), None)
            if selected_id
            else None
        )

        # --- UATP 7.0 Specialized Capsule Creator ---
        st.header("UATP 7.0 Specialized Capsule Creator")
        st.markdown(
            "Create specialized capsules with type-specific fields as defined in the UATP 7.0 white paper."
        )

        # Render the specialized creator component
        if SPECIALIZED_CREATOR_AVAILABLE:
            render_specialized_creator(engine)
        else:
            st.warning("Specialized capsule creator component is not available.")

        # --- Economic Analysis Tab ---
        st.header("Economic Analysis")
        st.markdown("Visualize economic metrics and trends in the UATP capsule chain.")

        # Import economic visualization components
        from visualizer.components.economic_visualization import (
            analyze_economic_transactions,
            render_dividend_calculator,
        )

        # Render the economic dashboard
        analyze_economic_transactions(chain)

        # --- Reasoning Validation Section ---
        st.subheader("Reasoning Validation (API)")
        st.markdown(
            "Validate the reasoning trace of the selected capsule using the Reasoning API."
        )

        # Use a container to track the button's disabled state
        validation_container = st.container()
        with validation_container:
            validate_button_clicked = st.button(
                "Validate Reasoning via API",
                key="validate_reasoning_api",
                disabled=False,
            )

        # Handle the API call if button was clicked
        if validate_button_clicked:
            # Disable the button while processing
            with validation_container:
                st.button(
                    "Validate Reasoning via API",
                    key="validate_reasoning_api_disabled",
                    disabled=True,
                )

            with st.spinner("Validating reasoning trace via API..."):
                if not selected_capsule or not selected_capsule.reasoning_trace:
                    st.error("No reasoning trace available in the selected capsule.")
                else:
                    result = call_reasoning_validate_api(
                        selected_capsule.reasoning_trace
                    )
                    if "error" in result:
                        st.error(f"API Error: {result['error']}")
                    elif "validation_result" in result:
                        val = result["validation_result"]
                        st.success(
                            f"Score: {val['score']:.1f}/100 | Valid: {val['is_valid']}"
                        )
                        if val.get("issues"):
                            st.warning("Issues found:")
                            for issue in val["issues"]:
                                st.markdown(
                                    f"- **{issue['severity'].capitalize()}**: {issue['message']}"
                                )
                        if val.get("suggestions"):
                            st.info("Suggestions:")
                            for suggestion in val["suggestions"]:
                                st.markdown(f"- {suggestion}")
                    else:
                        st.error(
                            "Unexpected API response. Please check the API server."
                        )

        # --- Reasoning Analysis Section ---
        st.subheader("Reasoning Analysis (API)")
        st.markdown(
            "Analyze the reasoning trace of the selected capsule using the Reasoning API."
        )

        # Use a container to track the button's disabled state
        analysis_container = st.container()
        with analysis_container:
            analyze_button_clicked = st.button(
                "Analyze Reasoning via API", key="analyze_reasoning_api", disabled=False
            )

        # Handle the API call if button was clicked
        if analyze_button_clicked:
            # Disable the button while processing
            with analysis_container:
                st.button(
                    "Analyze Reasoning via API",
                    key="analyze_reasoning_api_disabled",
                    disabled=True,
                )

            with st.spinner("Analyzing reasoning trace via API..."):
                if not selected_capsule or not selected_capsule.reasoning_trace:
                    st.error("No reasoning trace available in the selected capsule.")
                else:
                    analysis_result = call_reasoning_analyze_api(
                        selected_capsule.reasoning_trace
                    )
                    if "error" in analysis_result:
                        st.error(f"API Error: {analysis_result['error']}")
                    elif "analysis" in analysis_result:
                        analysis = analysis_result["analysis"]
                        st.success(
                            f"Step Count: {analysis['step_count']} | Avg Confidence: {analysis['average_confidence']:.2f}"
                        )
                        # Step type distribution chart
                        if analysis.get("type_distribution"):
                            st.markdown("**Step Type Distribution:**")
                            st.bar_chart(analysis["type_distribution"])
                        # Patterns
                        if analysis.get("patterns"):
                            st.markdown("**Detected Patterns:**")
                            for pattern in analysis["patterns"]:
                                st.markdown(f"- {pattern}")
                        # Flow assessment
                        if analysis.get("flow"):
                            st.markdown("**Flow Quality Assessment:**")
                            for aspect, rating in analysis["flow"].items():
                                st.markdown(
                                    f"- **{aspect.replace('_', ' ').capitalize()}:** {rating}"
                                )
                    else:
                        st.error(
                            "Unexpected API response. Please check the API server."
                        )

        # --- Relationships Visualization Section ---
        st.subheader("UATP 7.0 Capsule Relationships")
        st.markdown(
            "Visualize relationships between capsules as defined in the UATP 7.0 white paper."
        )

        # Import shared filter component
        from visualizer.components.visualization_filters import render_filter_controls

        # Apply filters to chain
        filtered_chain = render_filter_controls(chain)

        if filtered_chain:
            # Create tabs for different visualizations
            viz_tab1, viz_tab2, viz_tab3, viz_tab4 = st.tabs(
                [
                    "Network View",
                    "Timeline View",
                    "Economic Analysis",
                    "Protocol Guidelines",
                ]
            )

            # Import shared state management
            from visualizer.components.visualization_shared_state import (
                get_highlighted_capsule_id,
                initialize_visualization_state,
                render_highlight_controls,
            )

            # Initialize the shared state
            initialize_visualization_state()

            # Render the highlight controls
            render_highlight_controls()

            # Get the currently highlighted capsule ID from shared state
            highlighted_id = get_highlighted_capsule_id()

            # Network View Tab
            with viz_tab1:
                st.markdown("### Network Visualization")
                st.caption(
                    "Interactive network showing all relationship types between capsules"
                )

                # Option for interactive network visualization
                interactive_network = st.checkbox("Use interactive network", value=True)

                # Render the network visualization
                try:
                    render_capsule_network(
                        filtered_chain,
                        interactive=interactive_network,
                        highlighted_capsule_id=highlighted_id,
                    )
                except Exception as e:
                    st.error(f"Error rendering network visualization: {str(e)}")

            # Timeline View Tab
            with viz_tab2:
                st.markdown("### Timeline Visualization")
                st.caption("Chronological view of capsule creation and relationships")

                # Option for interactive timeline visualization
                interactive_timeline = st.checkbox(
                    "Use interactive timeline", value=True
                )

                # Render the timeline visualization
                try:
                    render_capsule_timeline(
                        filtered_chain,
                        interactive=interactive_timeline,
                        highlighted_capsule_id=highlighted_id,
                    )
                except Exception as e:
                    st.error(f"Error rendering timeline visualization: {str(e)}")

            # Economic Analysis Tab
            with viz_tab3:
                st.markdown("### Economic Analysis")
                st.caption(
                    "Economic metrics and value distribution analysis of the capsule chain"
                )

                try:
                    # Import economic visualization components
                    from visualizer.components.economic_visualization import (
                        analyze_economic_transactions,
                        render_dividend_calculator,
                    )

                    # Create subtabs for different economic analysis views
                    econ_tab1, econ_tab2 = st.tabs(
                        ["Value Transactions", "Dividend Simulator"]
                    )

                    with econ_tab1:
                        analyze_economic_transactions(filtered_chain)

                    with econ_tab2:
                        render_dividend_calculator()

                except ImportError as e:
                    st.error(
                        f"Could not import economic visualization components: {str(e)}"
                    )
                    st.info(
                        "Make sure economic visualization modules are properly installed."
                    )
                except Exception as e:
                    st.error(f"Error rendering economic visualizations: {str(e)}")
                    st.info(
                        "There was an issue with the economic visualization components."
                    )

            # Protocol Guidelines Tab
            with viz_tab4:
                try:
                    # Render the protocol guidelines component
                    render_protocol_guidelines()
                except Exception as e:
                    st.error(f"Error rendering protocol guidelines: {str(e)}")
                    st.info(
                        "There was an issue with the protocol guidelines component."
                    )
        else:
            st.info("No capsules match the current filter to display relationships.")

        # --- Reasoning Comparison Section ---
        st.subheader("Reasoning Comparison (API)")
        st.markdown(
            "Compare the reasoning traces of two capsules using the Reasoning API."
        )

        # Selection for two capsules to compare
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**First Capsule**")
            first_capsule_id = st.selectbox(
                "Select first capsule",
                [c.capsule_id for c in filtered_chain],
                key="first_capsule",
            )
            first_capsule = next(
                (c for c in filtered_chain if c.capsule_id == first_capsule_id), None
            )
            if first_capsule:
                st.success(f"Type: {first_capsule.capsule_type}")

        with col2:
            st.markdown("**Second Capsule**")
            second_capsule_id = st.selectbox(
                "Select second capsule",
                [
                    c.capsule_id
                    for c in filtered_chain
                    if c.capsule_id != first_capsule_id
                ],
                key="second_capsule",
            )
            second_capsule = next(
                (c for c in filtered_chain if c.capsule_id == second_capsule_id), None
            )
            if second_capsule:
                st.success(f"Type: {second_capsule.capsule_type}")

        # Container for the compare button
        comparison_container = st.container()
        with comparison_container:
            compare_button_clicked = st.button(
                "Compare Reasoning Traces", key="compare_reasoning_api", disabled=False
            )

        # Handle API call when compare button is clicked
        if compare_button_clicked and first_capsule and second_capsule:
            # Disable button during processing
            with comparison_container:
                st.button(
                    "Compare Reasoning Traces",
                    key="compare_reasoning_api_disabled",
                    disabled=True,
                )

            with st.spinner("Comparing reasoning traces via API..."):
                # Validate both capsules have reasoning traces
                if (
                    not first_capsule.reasoning_trace
                    or not second_capsule.reasoning_trace
                ):
                    st.error(
                        "One or both selected capsules do not have reasoning traces."
                    )
                else:
                    comparison_result = call_reasoning_compare_api(
                        first_capsule.reasoning_trace, second_capsule.reasoning_trace
                    )

                    if "error" in comparison_result:
                        st.error(f"API Error: {comparison_result['error']}")
                    elif "comparison" in comparison_result:
                        comp = comparison_result["comparison"]

                        # Display similarity score
                        st.success(
                            f"Similarity Score: {comp.get('similarity_score', 0):.2f}/100"
                        )

                        # Display key differences in a tabular format
                        if comp.get("differences"):
                            st.markdown("**Key Differences:**")
                            differences_data = []
                            for diff in comp["differences"]:
                                differences_data.append(
                                    {
                                        "Aspect": diff.get("aspect", ""),
                                        "First Capsule": diff.get("value1", ""),
                                        "Second Capsule": diff.get("value2", ""),
                                    }
                                )
                            st.table(differences_data)

                        # Display strengths of each trace
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(
                                f"**Strengths of First Capsule ({first_capsule.capsule_type}):**"
                            )
                            strengths1 = comp.get("strengths_trace1", [])
                            for strength in strengths1:
                                st.markdown(f"- {strength}")

                        with col2:
                            st.markdown(
                                f"**Strengths of Second Capsule ({second_capsule.capsule_type}):**"
                            )
                            strengths2 = comp.get("strengths_trace2", [])
                            for strength in strengths2:
                                st.markdown(f"- {strength}")

                        # Display improvement suggestions
                        if comp.get("suggestions"):
                            st.markdown("**Improvement Suggestions:**")
                            for suggestion in comp["suggestions"]:
                                st.markdown(f"- {suggestion}")
                    else:
                        st.error(
                            "Unexpected API response. Please check the API server."
                        )

        # --- Reasoning Batch Analysis Section ---
        st.subheader("Reasoning Batch Analysis (API)")
        st.markdown(
            "Analyze multiple reasoning traces at once and compare their metrics."
        )

        # Multi-select for capsules
        st.markdown("**Select multiple capsules for batch analysis:**")
        batch_capsule_ids = st.multiselect(
            "Select capsules for batch analysis",
            [c.capsule_id for c in filtered_chain],
            [],
            key="batch_capsules",
        )

        # Get selected capsules
        batch_capsules = [
            c for c in filtered_chain if c.capsule_id in batch_capsule_ids
        ]

        # Show selected capsule types
        if batch_capsules:
            st.markdown("**Selected capsules:**")
            for capsule in batch_capsules:
                st.markdown(f"- {capsule.capsule_type} ({capsule.capsule_id[:8]}...)")

        # Container for the batch analyze button
        batch_container = st.container()
        with batch_container:
            batch_button_clicked = st.button(
                "Analyze Batch",
                key="batch_analyze_api",
                disabled=len(batch_capsules) < 2,
            )

        # Handle API call when batch analyze button is clicked
        if batch_button_clicked and len(batch_capsules) >= 2:
            # Disable button during processing
            with batch_container:
                st.button(
                    "Analyze Batch", key="batch_analyze_api_disabled", disabled=True
                )

            with st.spinner("Performing batch analysis via API..."):
                # Extract reasoning traces from selected capsules
                reasoning_traces = [
                    c.reasoning_trace for c in batch_capsules if c.reasoning_trace
                ]

                if not reasoning_traces:
                    st.error("None of the selected capsules have reasoning traces.")
                else:
                    batch_result = call_reasoning_batch_analyze_api(reasoning_traces)

                    if "error" in batch_result:
                        st.error(f"API Error: {batch_result['error']}")
                    elif "batch_results" in batch_result:
                        results = batch_result["batch_results"]

                        # Create comparison table
                        st.markdown("### Batch Analysis Results")

                        # Prepare data for table
                        table_data = []
                        for i, (capsule, result) in enumerate(
                            zip(batch_capsules, results)
                        ):
                            if "analysis" in result:
                                analysis = result["analysis"]
                                table_data.append(
                                    {
                                        "Capsule Type": capsule.capsule_type,
                                        "ID": capsule.capsule_id[:8] + "...",
                                        "Step Count": analysis.get("step_count", 0),
                                        "Avg Confidence": f"{analysis.get('average_confidence', 0):.2f}",
                                        "Pattern Count": len(
                                            analysis.get("patterns", [])
                                        ),
                                        "Top Step Type": max(
                                            analysis.get(
                                                "type_distribution", {}
                                            ).items(),
                                            key=lambda x: x[1],
                                        )[0]
                                        if analysis.get("type_distribution")
                                        else "N/A",
                                    }
                                )

                        # Display table
                        if table_data:
                            st.table(table_data)

                            # Create visualizations
                            st.markdown("### Comparative Visualizations")

                            # Step count comparison chart
                            step_counts = [
                                result["analysis"].get("step_count", 0)
                                for result in results
                                if "analysis" in result
                            ]
                            capsule_types = [
                                c.capsule_type
                                for c in batch_capsules[: len(step_counts)]
                            ]

                            step_count_chart = {
                                "Capsule": capsule_types,
                                "Step Count": step_counts,
                            }
                            st.markdown("**Step Count Comparison:**")
                            st.bar_chart(step_count_chart, x="Capsule")

                            # Confidence comparison
                            avg_confidences = [
                                result["analysis"].get("average_confidence", 0)
                                for result in results
                                if "analysis" in result
                            ]

                            confidence_chart = {
                                "Capsule": capsule_types,
                                "Avg Confidence": avg_confidences,
                            }
                            st.markdown("**Average Confidence Comparison:**")
                            st.bar_chart(confidence_chart, x="Capsule")

                            # Common patterns across all traces
                            st.markdown("**Common Patterns Across All Traces:**")
                            all_patterns = [
                                set(result["analysis"].get("patterns", []))
                                for result in results
                                if "analysis" in result
                            ]

                            if all_patterns:
                                common_patterns = (
                                    set.intersection(*all_patterns)
                                    if all_patterns
                                    else set()
                                )
                                if common_patterns:
                                    for pattern in common_patterns:
                                        st.markdown(f"- {pattern}")
                                else:
                                    st.info(
                                        "No common patterns found across all traces."
                                    )

                            # Overall insights
                            st.markdown("### Overall Insights")
                            st.markdown("Based on the batch analysis, we can observe:")

                            # Generate some basic insights
                            max_steps_capsule = (
                                capsule_types[step_counts.index(max(step_counts))]
                                if step_counts
                                else "N/A"
                            )
                            min_steps_capsule = (
                                capsule_types[step_counts.index(min(step_counts))]
                                if step_counts
                                else "N/A"
                            )
                            max_conf_capsule = (
                                capsule_types[
                                    avg_confidences.index(max(avg_confidences))
                                ]
                                if avg_confidences
                                else "N/A"
                            )

                            st.markdown(
                                f"- **{max_steps_capsule}** has the most reasoning steps ({max(step_counts) if step_counts else 0})"
                            )
                            st.markdown(
                                f"- **{min_steps_capsule}** has the fewest reasoning steps ({min(step_counts) if step_counts else 0})"
                            )
                            st.markdown(
                                f"- **{max_conf_capsule}** has the highest average confidence {max(avg_confidences):.2f if avg_confidences else 0}"
                            )
                        else:
                            st.warning(
                                "Could not generate comparison table from API results."
                            )
                    else:
                        st.error(
                            "Unexpected API response. Please check the API server."
                        )

        # --- CQSS Simulation Section ---
        st.subheader("CQSS Quality Score Simulator")
        st.markdown(
            "Analyze capsule quality scores and simulate changes to improve them."
        )

        # Select a capsule for CQSS analysis
        st.markdown("**Select a capsule to analyze:**")
        cqss_capsule_id = st.selectbox(
            "Select capsule for CQSS analysis",
            [c.capsule_id for c in filtered_chain],
            key="cqss_capsule",
        )

        # Get selected capsule
        cqss_capsule = next(
            (c for c in filtered_chain if c.capsule_id == cqss_capsule_id), None
        )

        if cqss_capsule:
            # Import CQSS modules
            from cqss.scorer import CQSSScorer
            from cqss.simulator import CQSSSimulator

            # Calculate current score
            current_score = CQSSScorer.calculate_score(cqss_capsule)

            # Display current score
            st.markdown("### Current CQSS Score")
            st.markdown(f"**Total Score:** {current_score['total_score']:.2f}/100")

            # Display score breakdown
            st.markdown("#### Score Breakdown")
            breakdown = current_score["breakdown"]

            # Create columns for score components
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Signature (40%)",
                    f"{breakdown.get('signature_verification', 0):.0f}",
                )

            with col2:
                st.metric("Confidence (30%)", f"{breakdown.get('confidence', 0):.0f}")

            with col3:
                st.metric(
                    "Reasoning (20%)", f"{breakdown.get('reasoning_depth', 0):.0f}"
                )

            with col4:
                st.metric(
                    "Ethical Policy (10%)", f"{breakdown.get('ethical_policy', 0):.0f}"
                )

            # Simulation section
            st.markdown("### Simulate Changes")
            st.markdown(
                "Select an attribute to modify and see how it affects the capsule's quality score:"
            )

            sim_type = st.radio(
                "Simulation Type",
                [
                    "Confidence",
                    "Reasoning Trace",
                    "Ethical Policy",
                    "Signature",
                    "Multiple Changes",
                    "Optimize",
                ],
                key="sim_type",
            )

            if sim_type == "Confidence":
                new_confidence = st.slider(
                    "New Confidence Value", 0.0, 1.0, cqss_capsule.confidence, 0.01
                )

                if st.button("Simulate Confidence Change"):
                    with st.spinner("Simulating confidence change..."):
                        result = CQSSSimulator.simulate_confidence_change(
                            cqss_capsule, new_confidence
                        )

                        # Display results
                        st.markdown("### Simulation Results")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(
                                "Original Score",
                                f"{result['original']['total_score']:.2f}",
                            )
                        with col2:
                            st.metric(
                                "Simulated Score",
                                f"{result['simulated']['total_score']:.2f}",
                            )
                        with col3:
                            st.metric(
                                "Difference",
                                f"{result['difference']:.2f}",
                                delta=round(result["difference"], 2),
                            )

                        # Show breakdown comparison
                        st.markdown("#### Score Breakdown Comparison")

                        breakdown_df = {
                            "Component": [
                                "Signature",
                                "Confidence",
                                "Reasoning",
                                "Ethical Policy",
                            ],
                            "Original": [
                                result["original"]["breakdown"].get(
                                    "signature_verification", 0
                                ),
                                result["original"]["breakdown"].get("confidence", 0),
                                result["original"]["breakdown"].get(
                                    "reasoning_depth", 0
                                ),
                                result["original"]["breakdown"].get(
                                    "ethical_policy", 0
                                ),
                            ],
                            "Simulated": [
                                result["simulated"]["breakdown"].get(
                                    "signature_verification", 0
                                ),
                                result["simulated"]["breakdown"].get("confidence", 0),
                                result["simulated"]["breakdown"].get(
                                    "reasoning_depth", 0
                                ),
                                result["simulated"]["breakdown"].get(
                                    "ethical_policy", 0
                                ),
                            ],
                        }

                        st.table(breakdown_df)

            elif sim_type == "Reasoning Trace":
                # Options for reasoning trace simulation
                trace_option = st.radio(
                    "Reasoning Trace Option",
                    ["Add steps", "Remove steps"],
                    key="trace_option",
                )

                current_trace = cqss_capsule.get_reasoning_trace_as_strings()
                current_steps = len(current_trace)

                if trace_option == "Add steps":
                    additional_steps = st.slider("Additional steps", 1, 5, 1)

                    if st.button("Simulate Adding Steps"):
                        with st.spinner("Simulating reasoning trace change..."):
                            new_trace = list(current_trace)
                            for i in range(additional_steps):
                                new_trace.append(
                                    f"Additional reasoning step {i+1} for simulation"
                                )

                            result = CQSSSimulator.simulate_reasoning_trace_change(
                                cqss_capsule, new_trace
                            )

                            # Display results
                            st.markdown("### Simulation Results")

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric(
                                    "Original Score",
                                    f"{result['original']['total_score']:.2f}",
                                )
                            with col2:
                                st.metric(
                                    "Simulated Score",
                                    f"{result['simulated']['total_score']:.2f}",
                                )
                            with col3:
                                st.metric(
                                    "Difference",
                                    f"{result['difference']:.2f}",
                                    delta=round(result["difference"], 2),
                                )

                            st.markdown(
                                f"**Step count:** {current_steps} → {len(new_trace)}"
                            )

                else:  # Remove steps
                    if current_steps > 0:
                        steps_to_remove = st.slider(
                            "Steps to remove", 1, max(1, current_steps - 1), 1
                        )

                        if st.button("Simulate Removing Steps"):
                            with st.spinner("Simulating reasoning trace change..."):
                                new_trace = (
                                    list(current_trace)[:-steps_to_remove]
                                    if steps_to_remove < current_steps
                                    else []
                                )

                                result = CQSSSimulator.simulate_reasoning_trace_change(
                                    cqss_capsule, new_trace
                                )

                                # Display results
                                st.markdown("### Simulation Results")

                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric(
                                        "Original Score",
                                        f"{result['original']['total_score']:.2f}",
                                    )
                                with col2:
                                    st.metric(
                                        "Simulated Score",
                                        f"{result['simulated']['total_score']:.2f}",
                                    )
                                with col3:
                                    st.metric(
                                        "Difference",
                                        f"{result['difference']:.2f}",
                                        delta=round(result["difference"], 2),
                                    )

                                st.markdown(
                                    f"**Step count:** {current_steps} → {len(new_trace)}"
                                )
                    else:
                        st.warning("No reasoning steps to remove.")

            elif sim_type == "Ethical Policy":
                current_policy = cqss_capsule.ethical_policy_id or "None"
                st.markdown(f"Current policy: **{current_policy}**")

                new_policy = st.text_input(
                    "New Ethical Policy ID", "default_ethical_policy"
                )

                if st.button("Simulate Policy Change"):
                    with st.spinner("Simulating ethical policy change..."):
                        result = CQSSSimulator.simulate_ethical_policy_change(
                            cqss_capsule, new_policy
                        )

                        # Display results
                        st.markdown("### Simulation Results")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(
                                "Original Score",
                                f"{result['original']['total_score']:.2f}",
                            )
                        with col2:
                            st.metric(
                                "Simulated Score",
                                f"{result['simulated']['total_score']:.2f}",
                            )
                        with col3:
                            st.metric(
                                "Difference",
                                f"{result['difference']:.2f}",
                                delta=round(result["difference"], 2),
                            )

                        st.markdown(f"**Policy ID:** {current_policy} → {new_policy}")

            elif sim_type == "Signature":
                valid_options = ["Valid", "Invalid"]
                signature_valid = st.radio("Signature Validity", valid_options)

                if st.button("Simulate Signature Change"):
                    with st.spinner("Simulating signature change..."):
                        is_valid = signature_valid == "Valid"
                        result = CQSSSimulator.simulate_signature_change(
                            cqss_capsule, is_valid
                        )

                        # Display results
                        st.markdown("### Simulation Results")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(
                                "Original Score",
                                f"{result['original']['total_score']:.2f}",
                            )
                        with col2:
                            st.metric(
                                "Simulated Score",
                                f"{result['simulated']['total_score']:.2f}",
                            )
                        with col3:
                            st.metric(
                                "Difference",
                                f"{result['difference']:.2f}",
                                delta=round(result["difference"], 2),
                            )

                        st.markdown(
                            f"**Signature:** {'Valid' if is_valid else 'Invalid'}"
                        )

            elif sim_type == "Multiple Changes":
                st.markdown("Simulate multiple changes at once:")

                # Confidence
                include_confidence = st.checkbox("Change Confidence", value=False)
                new_confidence = None
                if include_confidence:
                    new_confidence = st.slider(
                        "New Confidence Value", 0.0, 1.0, cqss_capsule.confidence, 0.01
                    )

                # Reasoning Trace
                include_trace = st.checkbox("Change Reasoning Trace", value=False)
                new_trace = None
                if include_trace:
                    current_trace = cqss_capsule.get_reasoning_trace_as_strings()
                    trace_option = st.radio(
                        "Trace Change Type",
                        ["Add steps", "Remove steps"],
                        key="multi_trace_option",
                    )

                    if trace_option == "Add steps":
                        additional_steps = st.slider("Additional steps", 1, 5, 1)
                        new_trace = list(current_trace)
                        for i in range(additional_steps):
                            new_trace.append(
                                f"Additional reasoning step {i+1} for simulation"
                            )
                    else:  # Remove steps
                        current_steps = len(current_trace)
                        if current_steps > 0:
                            steps_to_remove = st.slider(
                                "Steps to remove", 1, max(1, current_steps - 1), 1
                            )
                            new_trace = (
                                list(current_trace)[:-steps_to_remove]
                                if steps_to_remove < current_steps
                                else []
                            )
                        else:
                            st.warning("No reasoning steps to remove.")

                # Ethical Policy
                include_policy = st.checkbox("Change Ethical Policy", value=False)
                new_policy = None
                if include_policy:
                    current_policy = cqss_capsule.ethical_policy_id or "None"
                    st.markdown(f"Current policy: **{current_policy}**")
                    new_policy = st.text_input(
                        "New Ethical Policy ID", "default_ethical_policy"
                    )

                # Signature
                include_signature = st.checkbox(
                    "Change Signature Validity", value=False
                )
                valid_signature = None
                if include_signature:
                    signature_valid = st.radio(
                        "Signature Validity", ["Valid", "Invalid"]
                    )
                    valid_signature = signature_valid == "Valid"

                if st.button("Simulate Multiple Changes"):
                    if not any(
                        [
                            include_confidence,
                            include_trace,
                            include_policy,
                            include_signature,
                        ]
                    ):
                        st.warning("Please select at least one attribute to change.")
                    else:
                        with st.spinner("Simulating multiple changes..."):
                            result = CQSSSimulator.simulate_multiple_changes(
                                cqss_capsule,
                                new_confidence=new_confidence,
                                new_trace=new_trace,
                                new_policy_id=new_policy,
                                valid_signature=valid_signature,
                            )

                            # Display results
                            st.markdown("### Simulation Results")

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric(
                                    "Original Score",
                                    f"{result['original']['total_score']:.2f}",
                                )
                            with col2:
                                st.metric(
                                    "Simulated Score",
                                    f"{result['simulated']['total_score']:.2f}",
                                )
                            with col3:
                                st.metric(
                                    "Difference",
                                    f"{result['difference']:.2f}",
                                    delta=round(result["difference"], 2),
                                )

                            st.markdown("**Changes Made:**")
                            for attr in result.get("modified_attributes", []):
                                st.markdown(f"- Modified: {attr}")

                            # Show breakdown comparison
                            st.markdown("#### Score Breakdown Comparison")

                            breakdown_df = {
                                "Component": [
                                    "Signature",
                                    "Confidence",
                                    "Reasoning",
                                    "Ethical Policy",
                                ],
                                "Original": [
                                    result["original"]["breakdown"].get(
                                        "signature_verification", 0
                                    ),
                                    result["original"]["breakdown"].get(
                                        "confidence", 0
                                    ),
                                    result["original"]["breakdown"].get(
                                        "reasoning_depth", 0
                                    ),
                                    result["original"]["breakdown"].get(
                                        "ethical_policy", 0
                                    ),
                                ],
                                "Simulated": [
                                    result["simulated"]["breakdown"].get(
                                        "signature_verification", 0
                                    ),
                                    result["simulated"]["breakdown"].get(
                                        "confidence", 0
                                    ),
                                    result["simulated"]["breakdown"].get(
                                        "reasoning_depth", 0
                                    ),
                                    result["simulated"]["breakdown"].get(
                                        "ethical_policy", 0
                                    ),
                                ],
                            }

                            st.table(breakdown_df)

            elif sim_type == "Optimize":
                st.markdown(
                    "Let the system suggest optimizations to achieve a target score."
                )

                target_score = st.slider("Target Score", 50.0, 100.0, 90.0, 5.0)

                # Fixed attributes
                st.markdown("**Select attributes that should NOT be changed:**")
                fix_confidence = st.checkbox("Keep current confidence", value=False)
                fix_reasoning = st.checkbox("Keep current reasoning trace", value=False)
                fix_policy = st.checkbox("Keep current ethical policy", value=False)

                fixed_attributes = []
                if fix_confidence:
                    fixed_attributes.append("confidence")
                if fix_reasoning:
                    fixed_attributes.append("reasoning_trace")
                if fix_policy:
                    fixed_attributes.append("ethical_policy_id")

                if st.button("Run Optimizer"):
                    with st.spinner("Running CQSS optimization..."):
                        report, optimized_capsule = CQSSSimulator.optimize_capsule(
                            cqss_capsule,
                            target_score=target_score,
                            fixed_attributes=fixed_attributes,
                        )

                        # Display optimization results
                        st.markdown("### Optimization Results")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(
                                "Original Score", f"{report['original_score']:.2f}"
                            )
                        with col2:
                            st.metric(
                                "Optimized Score", f"{report['optimized_score']:.2f}"
                            )
                        with col3:
                            st.metric("Target Score", f"{report['target_score']:.2f}")

                        # Show if target was achieved
                        if report.get("target_achieved", False):
                            st.success("✅ Target score achieved!")
                        else:
                            st.warning(
                                "⚠️ Target score not achieved with current constraints."
                            )

                        # Show changes made
                        st.markdown("**Optimization Changes:**")
                        for change in report.get("changes_made", []):
                            st.markdown(f"- {change}")

                        # Show optimized capsule details
                        with st.expander("View Optimized Capsule Details"):
                            st.json(optimized_capsule.to_dict())

# Import components safely
try:
    from visualizer.components import (
        inspector,
        visualization_filters,
        specialized_creator,
    )
except ImportError as e:
    st.error(f"Error importing components: {e}")
    st.error("This may be due to missing specialized engine modules.")
    st.stop()
# Import dividend panel safely
try:
    from visualizer.components.dividend_panel import render_dividend_panel

    DIVIDEND_PANEL_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import dividend_panel: {e}")
    DIVIDEND_PANEL_AVAILABLE = False

    def render_dividend_panel(chain):
        st.info("Dividend panel not available - missing dependencies")


# Render the dividend panel in the sidebar
with st.sidebar:
    st.header("Economic Attribution")
    render_dividend_panel(chain)
