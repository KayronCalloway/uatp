"""
visualize_simulation.py - Enhanced Streamlit visualizer with CQSS simulation capabilities.
Allows interactive simulation of how changes to capsules would affect their quality scores.
"""

import json
from collections import defaultdict

import streamlit as st
from capsule_schema import Capsule
from cqss.scorer import CQSSScorer
from cqss.simulator import CQSSSimulator

# Path to the capsule chain file
CHAIN_PATH = "capsule_chain.jsonl"


def load_capsules_from_jsonl(path):
    """Load capsules from a JSONL file."""
    capsules = []
    try:
        with open(path) as f:
            for line in f:
                if line.strip():
                    capsules.append(Capsule.from_dict(json.loads(line)))
    except FileNotFoundError:
        st.error(f"Error: The file '{path}' was not found.")
    return capsules


def build_chain_trees(capsules):
    """Build a forest of capsule chains, handling forks."""
    capsule_map = {c.capsule_id: c for c in capsules}
    children_map = defaultdict(list)
    roots = []

    for capsule in capsules:
        parent_id = capsule.previous_capsule_id
        if parent_id and parent_id in capsule_map:
            children_map[parent_id].append(capsule)
        else:
            roots.append(capsule)

    def build_tree(capsule):
        """Recursively build a tree node."""
        return {
            "capsule": capsule,
            "children": [
                build_tree(child) for child in children_map.get(capsule.capsule_id, [])
            ],
        }

    return [build_tree(root) for root in roots]


def display_chain_tree(tree_node):
    """Recursively display a capsule chain tree using columns for forks."""
    cap = tree_node["capsule"]
    children = tree_node["children"]

    # Calculate CQSS score
    cqss_result = CQSSScorer.calculate_score(cap)
    score = cqss_result["total_score"]
    breakdown = cqss_result["breakdown"]

    # Display current capsule details with CQSS score
    expander_title = (
        f"**{cap.capsule_type}** - ID: `{cap.capsule_id[:8]}` | **CQSS: {score}**"
    )
    with st.expander(expander_title, expanded=True):
        # Use columns for a cleaner layout
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("**Capsule Details**")
            st.json(cap.to_dict())

            # Add simulation button
            if st.button(
                f"Simulate Changes for {cap.capsule_id[:8]}",
                key=f"sim_{cap.capsule_id}",
            ):
                st.session_state.selected_capsule = cap
                st.session_state.show_simulator = True

        with col2:
            st.markdown("**CQSS Breakdown**")
            st.metric(
                "Signature Integrity",
                f"{breakdown.get('signature_verification', 0)}/100",
            )
            st.metric("Confidence", f"{breakdown.get('confidence', 0):.1f}/100")
            st.metric("Reasoning Depth", f"{breakdown.get('reasoning_depth', 0)}/100")
            st.metric("Ethical Policy", f"{breakdown.get('ethical_policy', 0)}/100")

    # Display children (forks)
    if children:
        st.markdown("⬇️")
        if len(children) > 1:
            cols = st.columns(len(children))
            for i, child_node in enumerate(children):
                with cols[i]:
                    display_chain_tree(child_node)
        else:
            display_chain_tree(children[0])


def display_simulator(capsule):
    """Display the CQSS simulator interface."""
    st.markdown("## CQSS Simulator")
    st.markdown(f"Simulating changes for capsule: `{capsule.capsule_id[:8]}`")

    # Create tabs for different simulation types
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Confidence", "Reasoning", "Ethical Policy", "Signature", "Optimize"]
    )

    # Tab 1: Confidence Simulation
    with tab1:
        st.markdown("### Simulate Confidence Change")
        new_confidence = st.slider(
            "New confidence value:",
            min_value=0.0,
            max_value=1.0,
            value=capsule.confidence,
            step=0.05,
        )

        if st.button("Simulate Confidence Change"):
            report = CQSSSimulator.simulate_confidence_change(capsule, new_confidence)
            display_simulation_results(report)

    # Tab 2: Reasoning Trace Simulation
    with tab2:
        st.markdown("### Simulate Reasoning Trace Change")

        # Show current reasoning trace
        st.markdown("**Current Reasoning Trace:**")
        for i, step in enumerate(capsule.reasoning_trace):
            st.text(f"{i+1}. {step}")

        # Options for simulation
        sim_option = st.radio(
            "Simulation option:", ["Modify existing trace", "Set number of steps"]
        )

        if sim_option == "Modify existing trace":
            new_trace = []
            for i, step in enumerate(capsule.reasoning_trace):
                new_step = st.text_area(f"Step {i+1}:", value=step, key=f"step_{i}")
                new_trace.append(new_step)

            # Option to add more steps
            add_steps = st.number_input(
                "Add additional steps:", min_value=0, max_value=10, value=0
            )
            for i in range(add_steps):
                new_step = st.text_area(
                    f"New Step {len(capsule.reasoning_trace) + i + 1}:",
                    key=f"new_step_{i}",
                )
                new_trace.append(new_step)
        else:
            num_steps = st.slider(
                "Number of reasoning steps:",
                min_value=0,
                max_value=10,
                value=len(capsule.reasoning_trace),
            )
            new_trace = [f"Simulated reasoning step {i+1}" for i in range(num_steps)]
            st.info(f"Will simulate with {num_steps} generic reasoning steps")

        if st.button("Simulate Reasoning Change"):
            report = CQSSSimulator.simulate_reasoning_trace_change(capsule, new_trace)
            display_simulation_results(report)

    # Tab 3: Ethical Policy Simulation
    with tab3:
        st.markdown("### Simulate Ethical Policy Change")

        current_policy = capsule.ethical_policy_id or "None"
        st.markdown(f"**Current Ethical Policy ID:** {current_policy}")

        new_policy = st.text_input(
            "New ethical policy ID:",
            value=current_policy
            if current_policy != "None"
            else "default_ethical_policy",
        )

        if st.button("Simulate Policy Change"):
            report = CQSSSimulator.simulate_ethical_policy_change(capsule, new_policy)
            display_simulation_results(report)

    # Tab 4: Signature Simulation
    with tab4:
        st.markdown("### Simulate Signature Validity")

        # Calculate current signature validity
        try:
            from crypto_utils import hash_for_signature, verify_capsule

            capsule_hash = hash_for_signature(capsule)
            verify_key_hex = capsule.metadata.get("verify_key_hex")
            current_valid = False
            if verify_key_hex and capsule.signature:
                current_valid = verify_capsule(
                    capsule_hash, capsule.signature, verify_key_hex
                )
        except Exception:
            current_valid = False

        st.markdown(f"**Current Signature Valid:** {current_valid}")

        valid_options = ["Valid", "Invalid"]
        selected_option = valid_options[0] if current_valid else valid_options[1]
        new_valid = st.radio(
            "Simulate signature as:",
            valid_options,
            index=valid_options.index(selected_option),
        )

        if st.button("Simulate Signature Change"):
            report = CQSSSimulator.simulate_signature_change(
                capsule, new_valid == "Valid"
            )
            display_simulation_results(report)

    # Tab 5: Optimize
    with tab5:
        st.markdown("### Optimize Capsule")

        target_score = st.slider(
            "Target CQSS score:", min_value=0.0, max_value=100.0, value=90.0, step=5.0
        )

        fixed_options = [
            "confidence",
            "reasoning_trace",
            "ethical_policy_id",
            "signature",
        ]
        fixed_attributes = st.multiselect(
            "Attributes to keep fixed:", options=fixed_options
        )

        if st.button("Optimize Capsule"):
            report, optimized = CQSSSimulator.optimize_capsule(
                capsule, target_score, fixed_attributes
            )

            # Display optimization report
            st.markdown("### Optimization Report")
            st.markdown(f"**Original Score:** {report['original_score']:.1f}")
            st.markdown(f"**Optimized Score:** {report['optimized_score']:.1f}")
            st.markdown(f"**Target Score:** {report['target_score']:.1f}")
            st.markdown(
                f"**Target Achieved:** {'Yes' if report['target_achieved'] else 'No'}"
            )

            st.markdown("**Changes Made:**")
            if report["changes_made"]:
                for change in report["changes_made"]:
                    st.markdown(f"- {change}")
            else:
                st.markdown("- No changes were necessary")

            # Show optimized capsule
            with st.expander("View Optimized Capsule"):
                st.json(optimized.to_dict())

            # Option to save optimized capsule
            if st.button("Save Optimized Capsule"):
                # Generate a filename
                filename = f"optimized_{capsule.capsule_id[:8]}.json"
                with open(filename, "w") as f:
                    json.dump(optimized.to_dict(), f, indent=2)
                st.success(f"Saved optimized capsule to {filename}")


def display_simulation_results(report):
    """Display the results of a simulation."""
    st.markdown("### Simulation Results")

    # Show the difference in total score
    original = report["original"]["total_score"]
    simulated = report["simulated"]["total_score"]
    difference = report["difference"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Original Score", f"{original:.1f}")
    with col2:
        st.metric("Simulated Score", f"{simulated:.1f}")
    with col3:
        st.metric("Difference", f"{difference:.1f}", delta=difference)

    # Show the breakdown comparison
    st.markdown("#### Score Breakdown Comparison")

    # Create a table for comparison
    data = []
    headers = ["Metric", "Original", "Simulated", "Change"]

    # Add rows for each component
    for key in report["original"]["breakdown"]:
        if key in report["simulated"]["breakdown"]:
            orig_val = report["original"]["breakdown"][key]
            sim_val = report["simulated"]["breakdown"][key]
            diff = sim_val - orig_val
            data.append(
                [
                    key.replace("_", " ").title(),
                    f"{orig_val:.1f}",
                    f"{sim_val:.1f}",
                    f"{diff:.1f}",
                ]
            )

    # Display as a dataframe for better formatting
    import pandas as pd

    df = pd.DataFrame(data, columns=headers)
    st.dataframe(df)


def main():
    st.set_page_config(layout="wide", page_title="UATP CQSS Simulator")
    st.title("UATP Capsule Chain Visualizer & CQSS Simulator")

    # Initialize session state
    if "show_simulator" not in st.session_state:
        st.session_state.show_simulator = False
    if "selected_capsule" not in st.session_state:
        st.session_state.selected_capsule = None

    # Add a button to return to the main view
    if st.session_state.show_simulator:
        if st.button("← Back to Chain View"):
            st.session_state.show_simulator = False
            st.session_state.selected_capsule = None
            st.experimental_rerun()

    # Show either the simulator or the chain view
    if st.session_state.show_simulator and st.session_state.selected_capsule:
        display_simulator(st.session_state.selected_capsule)
    else:
        capsules = load_capsules_from_jsonl(CHAIN_PATH)

        if not capsules:
            st.warning(f"No capsules found in '{CHAIN_PATH}'.")
        else:
            chain_trees = build_chain_trees(capsules)
            st.info(f"Found {len(chain_trees)} root(s) or separate chain(s).")

            for i, tree in enumerate(chain_trees):
                st.markdown(f"---_Chain {i+1}_---")
                display_chain_tree(tree)


if __name__ == "__main__":
    main()
