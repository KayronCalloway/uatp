import json
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from capsules.specialized_capsules import (
    CapsuleExpirationCapsule,
    ConsentCapsule,
    EconomicCapsule,
    GovernanceCapsule,
    SimulatedMaliceCapsule,
    TrustRenewalCapsule,
)

from visualizer.components.uatp7_inspector import (
    render_capsule_expiration_content,
    render_consent_content,
    render_economic_content,
    render_governance_content,
    render_simulated_malice_content,
    render_trust_renewal_content,
)

# Define icons (text-based) and colors for different capsule types
CAPSULE_ICONS = {
    "Consent": "[LOCK]",
    "Trust Renewal": "[RENEW]",
    "Governance": "[POLICY]",
    "Economic": "[VALUE]",
    "Simulated Malice": "[SECURITY]",
    "Capsule Expiration": "[EXPIRE]",
}

# Define colors for different capsule types
CAPSULE_COLORS = {
    "Consent": "#1e88e5",  # Blue
    "TrustRenewal": "#43a047",  # Green
    "Governance": "#6a1b9a",  # Purple
    "Economic": "#f57c00",  # Orange
    "SimulatedMalice": "#d32f2f",  # Red
    "CapsuleExpiration": "#546e7a",  # Slate
}


def convert_capsule_to_dict(capsule):
    """Convert a capsule object to a flat dictionary for export.

    This function attempts to convert a capsule object into a flat dictionary
    representation that can be easily exported to JSON or CSV formats. It handles
    various capsule implementations by trying different serialization methods
    and appropriately flattens nested data structures.

    Args:
        capsule (object): The capsule object to convert

    Returns:
        dict: A flattened dictionary representation of the capsule.
              Returns an empty dict if capsule is None or conversion fails.
    """
    if not capsule:
        return {}

    # Get capsule data as dict
    try:
        # First try the model_dump method (for Pydantic models)
        if hasattr(capsule, "model_dump"):
            capsule_dict = capsule.model_dump()
        # Then try dict method
        elif hasattr(capsule, "dict") and callable(capsule.dict):
            capsule_dict = capsule.dict()
        # Fall back to __dict__
        elif hasattr(capsule, "__dict__"):
            capsule_dict = capsule.__dict__
        else:
            # Last resort - try direct attribute access for common fields
            capsule_dict = {}
            common_fields = [
                "capsule_id",
                "capsule_type",
                "agent_id",
                "confidence",
                "signature",
                "timestamp",
                "reasoning_trace",
            ]

            for field in common_fields:
                if hasattr(capsule, field):
                    capsule_dict[field] = getattr(capsule, field)

            # If we couldn't extract any fields, log this issue
            if not capsule_dict:
                st.warning(
                    "Unable to extract data from capsule - no serialization method available"
                )

    except Exception as e:
        st.warning(
            f"Error converting capsule to dictionary: {type(e).__name__}: {str(e)}"
        )
        return {}

    # Flatten nested dictionaries with prefix
    flattened = {}
    try:
        for k, v in capsule_dict.items():
            # Skip None values
            if v is None:
                flattened[k] = ""
                continue

            if isinstance(v, dict):
                # Convert nested dict with prefix
                for sub_k, sub_v in v.items():
                    if isinstance(sub_v, (str, int, float, bool, type(None))):
                        flattened[f"{k}.{sub_k}"] = sub_v
                    else:
                        # Convert complex nested values to JSON
                        try:
                            flattened[f"{k}.{sub_k}"] = json.dumps(sub_v)
                        except:
                            flattened[f"{k}.{sub_k}"] = str(sub_v)
            elif isinstance(v, list):
                # Convert lists to JSON strings for proper export
                try:
                    flattened[k] = json.dumps(v)
                except:
                    flattened[k] = str(v)
            else:
                flattened[k] = v
    except Exception as e:
        st.warning(f"Error flattening capsule data: {type(e).__name__}: {str(e)}")
        # Return whatever we managed to process

    return flattened


def download_capsule_as_json(capsule, filename="capsule"):
    """Add a download button to download capsule as JSON.

    This function serializes a capsule object to JSON format and provides a
    download button in the Streamlit interface. It attempts multiple serialization
    methods to handle different capsule implementations.

    Args:
        capsule (object): Capsule object to download
        filename (str): Base filename without extension

    Returns:
        bool: True if successful, False if an error occurred
    """
    if not capsule:
        st.warning("Cannot download: No capsule data provided")
        return False

    try:
        # Get capsule dict
        capsule_dict = {}
        if hasattr(capsule, "model_dump"):
            capsule_dict = capsule.model_dump()
        elif hasattr(capsule, "dict") and callable(capsule.dict):
            capsule_dict = capsule.dict()
        elif hasattr(capsule, "__dict__"):
            capsule_dict = {
                k: v for k, v in capsule.__dict__.items() if not k.startswith("_")
            }

        if not capsule_dict:
            st.warning("Unable to extract data from capsule for JSON export")
            return False

        # Convert to JSON - handle non-serializable objects
        json_str = json.dumps(capsule_dict, indent=2, default=str)

        # Create download button
        st.download_button(
            label="Download as JSON",
            data=json_str,
            file_name=f"{filename}.json",
            mime="application/json",
        )
        return True

    except Exception as e:
        st.error("Error preparing JSON download")
        with st.expander("Error Details"):
            st.exception(e)
            st.text(f"Error type: {type(e).__name__}")
        return False


def download_capsule_as_csv(capsule, filename="capsule"):
    """Add a download button to download capsule as CSV.

    This function flattens a capsule object into a tabular format and provides
    a download button for CSV export in the Streamlit interface. Nested structures
    are flattened with dot notation for field names.

    Args:
        capsule (object): Capsule object to download
        filename (str): Base filename without extension

    Returns:
        bool: True if successful, False if an error occurred
    """
    if not capsule:
        st.warning("Cannot download: No capsule data provided")
        return False

    try:
        # Convert capsule to flat dict
        capsule_dict = convert_capsule_to_dict(capsule)

        if not capsule_dict:
            st.warning("Unable to extract data from capsule for CSV export")
            return False

        # Create pandas DataFrame
        df = pd.DataFrame([capsule_dict])

        # Convert to CSV
        csv = df.to_csv(index=False)

        # Create download button
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name=f"{filename}.csv",
            mime="text/csv",
        )
        return True

    except Exception as e:
        st.error("Error preparing CSV download")
        with st.expander("Error Details"):
            st.exception(e)
            st.text(f"Error type: {type(e).__name__}")
        return False


def safe_display_visualization(display_fn, capsule_fn=None):
    """Safely execute a visualization function with structured error handling.

    This function provides a standardized way to call visualization functions
    with proper error handling and user feedback. It can optionally create a sample
    capsule using the provided capsule creation function.

    Args:
        display_fn (callable): Function that displays the visualization
        capsule_fn (callable, optional): Function that creates a sample capsule

    Returns:
        bool: True if visualization was successful, False otherwise
    """
    try:
        # Create capsule if function provided
        if capsule_fn:
            with st.spinner("Loading capsule data..."):
                try:
                    capsule = capsule_fn()
                except Exception as capsule_err:
                    st.error("Failed to create sample capsule")
                    st.expander("Sample Data Error Details").exception(capsule_err)
                    return False

            # Display visualization with the created capsule
            display_fn(capsule)
        else:
            # Display visualization without capsule parameter
            display_fn()
        return True

    except Exception as e:
        # Provide structured error information
        st.error("Visualization Error: Unable to render the capsule visualization")
        with st.expander("Technical Error Details"):
            st.exception(e)
            st.info(
                f"Function: {display_fn.__name__} failed with error type: {type(e).__name__}"
            )
        return False


def main():
    """
    Unified dashboard for visualizing all UATP 7.0 capsule types.
    """
    try:
        st.set_page_config(
            page_title="UATP 7.0 Unified Capsule Visualization Dashboard",
            layout="wide",
            initial_sidebar_state="expanded",
        )
    except Exception:
        # This can happen if set_page_config is called twice (e.g., during hot reloading)
        pass

    # Create header with logo and title
    col1, col2 = st.columns([1, 4])
    with col1:
        # Display UATP icon or logo
        st.markdown(
            """
        <div style='text-align:center;font-size:42px;'></div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.title("UATP 7.0 Unified Capsule Visualization Dashboard")
        st.markdown(
            """
            <div style='margin-bottom:15px;'>
            Interactive visualization dashboard for exploring and understanding different UATP 7.0 capsule types.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Add descriptive information about UATP 7.0 capsules
    with st.expander("About UATP 7.0 Capsules"):
        st.markdown(
            """
        ### Unified Agent Trust Protocol (UATP) 7.0

        UATP 7.0 introduces specialized capsule types designed to address specific trust needs:

        - **Consent Capsules**: Record explicit user consent for specific actions or data usage
        - **Trust Renewal Capsules**: Establish ongoing verification and trust maintenance processes
        - **Governance Capsules**: Record policy decisions and governance processes
        - **Economic Capsules**: Track value attribution and dividend distributions
        - **Simulated Malice Capsules**: Document security testing scenarios
        - **Capsule Expiration Capsules**: Manage the lifecycle and validity period of other capsules
        - **Self Hallucination Capsules**: Document instances where an agent detected and corrected its own errors
        - **Value Inception Capsules**: Record ethical reasoning and value hierarchies in decision-making
        - **Temporal Signature Capsules**: Establish knowledge cutoff markers and temporal boundaries
        - **Remix Capsules**: Track derivative content creation with proper attribution and licensing
        """
        )

    # Create sidebar for capsule type selection
    st.sidebar.title("Navigation")

    # View mode selection - Single or Comparison
    view_mode = st.sidebar.radio(
        "View Mode", ["Single Capsule", "Comparison View"], index=0
    )

    # Capsule type selection
    capsule_type = st.sidebar.radio(
        "Select Capsule Type",
        [
            "Consent",
            "Trust Renewal",
            "Governance",
            "Economic",
            "Simulated Malice",
            "Capsule Expiration",
            "Self Hallucination",
            "Value Inception",
            "Temporal Signature",
            "Remix",
        ],
        index=0,
        format_func=lambda x: f"{CAPSULE_ICONS.get(x, '[*]')} {x}",
    )

    # Sample data options
    st.sidebar.subheader("Data Options")
    use_sample_data = st.sidebar.checkbox("Use sample data", value=True)

    # Add search and filter options
    st.sidebar.subheader("Search & Filter")
    search_query = st.sidebar.text_input("Search capsules", "")

    # Additional filters specific to capsule types
    if capsule_type == "Consent":
        st.sidebar.selectbox(
            "Consent Type", ["All", "Data Processing", "Service Usage", "Marketing"]
        )
    elif capsule_type == "Economic":
        st.sidebar.selectbox(
            "Economic Event Type",
            ["All", "Value Creation", "Value Transfer", "Dividend"],
        )

    # Display selected capsule visualization
    st.markdown("---")

    try:
        if view_mode == "Single Capsule":
            # Display single capsule visualization
            if capsule_type == "Consent":
                safe_display_visualization(display_consent_visualization)
            elif capsule_type == "Trust Renewal":
                safe_display_visualization(display_trust_renewal_visualization)
            elif capsule_type == "Governance":
                safe_display_visualization(display_governance_visualization)
            elif capsule_type == "Economic":
                safe_display_visualization(display_economic_visualization)
            elif capsule_type == "Simulated Malice":
                safe_display_visualization(display_simulated_malice_visualization)
            elif capsule_type == "Capsule Expiration":
                safe_display_visualization(display_capsule_expiration_visualization)
            elif capsule_type == "Self Hallucination":
                safe_display_visualization(display_self_hallucination_visualization)
            elif capsule_type == "Value Inception":
                safe_display_visualization(display_value_inception_visualization)
            elif capsule_type == "Temporal Signature":
                safe_display_visualization(display_temporal_signature_visualization)
            elif capsule_type == "Remix":
                safe_display_visualization(display_remix_visualization)
        else:
            # Comparison view
            st.header(f"Comparison View: {capsule_type} Capsules")

            # Create tabs for different comparison capsules
            tab1, tab2 = st.tabs(["Sample A", "Sample B"])

            # Generate two slightly different sample capsules of the same type
            with tab1:
                if capsule_type == "Consent":
                    capsule1 = create_sample_consent_capsule()
                    capsule1.consent_type = "Data Processing"
                    display_consent_visualization(capsule1)
                elif capsule_type == "Trust Renewal":
                    capsule1 = create_sample_trust_renewal_capsule()
                    if hasattr(capsule1, "renewal_frequency"):
                        capsule1.renewal_frequency = "P30D"  # 30 days
                    display_trust_renewal_visualization(capsule1)
                elif capsule_type == "Governance":
                    capsule1 = create_sample_governance_capsule()
                    if hasattr(capsule1, "governance_type"):
                        capsule1.governance_type = "Policy Change"
                    display_governance_visualization(capsule1)
                elif capsule_type == "Economic":
                    capsule1 = create_sample_economic_capsule()
                    if hasattr(capsule1, "economic_event_type"):
                        capsule1.economic_event_type = "Value Creation"
                    display_economic_visualization(capsule1)
                elif capsule_type == "Simulated Malice":
                    capsule1 = create_sample_simulated_malice_capsule()
                    if hasattr(capsule1, "simulation_type"):
                        capsule1.simulation_type = "Red Team Exercise"
                    display_simulated_malice_visualization(capsule1)
                elif capsule_type == "Capsule Expiration":
                    capsule1 = create_sample_capsule_expiration()
                    if hasattr(capsule1, "expiration_type"):
                        capsule1.expiration_type = "time_based"
                    display_capsule_expiration_visualization(capsule1)
                elif capsule_type == "Self Hallucination":
                    capsule1 = create_sample_self_hallucination_capsule()
                    if hasattr(capsule1, "hallucination_type"):
                        capsule1.hallucination_type = "factual_error"
                    display_self_hallucination_visualization(capsule1)
                elif capsule_type == "Value Inception":
                    capsule1 = create_sample_value_inception_capsule()
                    if hasattr(capsule1, "value_framework"):
                        capsule1.value_framework = "principled_pluralism"
                    display_value_inception_visualization(capsule1)
                elif capsule_type == "Temporal Signature":
                    capsule1 = create_sample_temporal_signature_capsule()
                    if hasattr(capsule1, "temporal_assertion_type"):
                        capsule1.temporal_assertion_type = "knowledge_boundary"
                    display_temporal_signature_visualization(capsule1)
                elif capsule_type == "Remix":
                    capsule1 = create_sample_remix_capsule()
                    if hasattr(capsule1, "attribution_strategy"):
                        capsule1.attribution_strategy = "content_volume_weighted"
                    display_remix_visualization(capsule1)

            with tab2:
                if capsule_type == "Consent":
                    capsule2 = create_sample_consent_capsule()
                    capsule2.consent_type = "Marketing"
                    display_consent_visualization(capsule2)
                elif capsule_type == "Trust Renewal":
                    capsule2 = create_sample_trust_renewal_capsule()
                    if hasattr(capsule2, "renewal_frequency"):
                        capsule2.renewal_frequency = "P90D"  # 90 days
                    display_trust_renewal_visualization(capsule2)
                elif capsule_type == "Governance":
                    capsule2 = create_sample_governance_capsule()
                    if hasattr(capsule2, "governance_type"):
                        capsule2.governance_type = "Protocol Amendment"
                    display_governance_visualization(capsule2)
                elif capsule_type == "Economic":
                    capsule2 = create_sample_economic_capsule()
                    if hasattr(capsule2, "economic_event_type"):
                        capsule2.economic_event_type = "Dividend Distribution"
                    display_economic_visualization(capsule2)
                elif capsule_type == "Simulated Malice":
                    capsule2 = create_sample_simulated_malice_capsule()
                    if hasattr(capsule2, "simulation_type"):
                        capsule2.simulation_type = "Penetration Test"
                    display_simulated_malice_visualization(capsule2)
                elif capsule_type == "Capsule Expiration":
                    capsule2 = create_sample_capsule_expiration()
                    if hasattr(capsule2, "expiration_type"):
                        capsule2.expiration_type = "event_based"
                    display_capsule_expiration_visualization(capsule2)
                elif capsule_type == "Self Hallucination":
                    capsule2 = create_sample_self_hallucination_capsule()
                    if hasattr(capsule2, "hallucination_type"):
                        capsule2.hallucination_type = "reasoning_error"
                    display_self_hallucination_visualization(capsule2)
                elif capsule_type == "Value Inception":
                    capsule2 = create_sample_value_inception_capsule()
                    if hasattr(capsule2, "value_framework"):
                        capsule2.value_framework = "utilitarian"
                    display_value_inception_visualization(capsule2)
                elif capsule_type == "Temporal Signature":
                    capsule2 = create_sample_temporal_signature_capsule()
                    if hasattr(capsule2, "temporal_assertion_type"):
                        capsule2.temporal_assertion_type = "data_currency"
                    display_temporal_signature_visualization(capsule2)
                elif capsule_type == "Remix":
                    capsule2 = create_sample_remix_capsule()
                    if hasattr(capsule2, "attribution_strategy"):
                        capsule2.attribution_strategy = "creative_contribution_weighted"
                    display_remix_visualization(capsule2)

            # Add a section for highlighting differences
            st.subheader("Key Differences")
            st.info(
                "This feature compares the key attributes of the capsules and highlights significant differences."
            )

            # Create a simple table showing differences between capsules
            differences = []

            if capsule_type == "Consent":
                differences = [
                    {
                        "Attribute": "Consent Type",
                        "Sample A": capsule1.consent_type,
                        "Sample B": capsule2.consent_type,
                    },
                    {
                        "Attribute": "Consenting Party",
                        "Sample A": capsule1.consenting_party,
                        "Sample B": capsule2.consenting_party,
                    },
                ]
            elif capsule_type == "Trust Renewal":
                differences = [
                    {
                        "Attribute": "Renewal Frequency",
                        "Sample A": getattr(capsule1, "renewal_frequency", "N/A"),
                        "Sample B": getattr(capsule2, "renewal_frequency", "N/A"),
                    }
                ]
            elif capsule_type == "Governance":
                differences = [
                    {
                        "Attribute": "Governance Type",
                        "Sample A": capsule1.governance_type,
                        "Sample B": capsule2.governance_type,
                    }
                ]
            elif capsule_type == "Economic":
                differences = [
                    {
                        "Attribute": "Economic Event Type",
                        "Sample A": capsule1.economic_event_type,
                        "Sample B": capsule2.economic_event_type,
                    }
                ]
            elif capsule_type == "Simulated Malice":
                differences = [
                    {
                        "Attribute": "Simulation Type",
                        "Sample A": capsule1.simulation_type,
                        "Sample B": capsule2.simulation_type,
                    }
                ]
            elif capsule_type == "Capsule Expiration":
                differences = [
                    {
                        "Attribute": "Expiration Type",
                        "Sample A": capsule1.expiration_type,
                        "Sample B": capsule2.expiration_type,
                    }
                ]
            elif capsule_type == "Self Hallucination":
                differences = [
                    {
                        "Attribute": "Hallucination Type",
                        "Sample A": capsule1.hallucination_type,
                        "Sample B": capsule2.hallucination_type,
                    },
                    {
                        "Attribute": "Detection Method",
                        "Sample A": getattr(
                            capsule1.correction_process, "detection_method", "N/A"
                        ),
                        "Sample B": getattr(
                            capsule2.correction_process, "detection_method", "N/A"
                        ),
                    },
                ]
            elif capsule_type == "Value Inception":
                differences = [
                    {
                        "Attribute": "Value Framework",
                        "Sample A": capsule1.value_framework,
                        "Sample B": capsule2.value_framework,
                    },
                    {
                        "Attribute": "Primary Value",
                        "Sample A": (
                            capsule1.values_hierarchy[0]["value"]
                            if hasattr(capsule1, "values_hierarchy")
                            and len(capsule1.values_hierarchy) > 0
                            else "N/A"
                        ),
                        "Sample B": (
                            capsule2.values_hierarchy[0]["value"]
                            if hasattr(capsule2, "values_hierarchy")
                            and len(capsule2.values_hierarchy) > 0
                            else "N/A"
                        ),
                    },
                ]
            elif capsule_type == "Temporal Signature":
                differences = [
                    {
                        "Attribute": "Temporal Assertion Type",
                        "Sample A": capsule1.temporal_assertion_type,
                        "Sample B": capsule2.temporal_assertion_type,
                    },
                    {
                        "Attribute": "Knowledge Cutoff Date",
                        "Sample A": capsule1.knowledge_cutoff_date,
                        "Sample B": capsule2.knowledge_cutoff_date,
                    },
                ]
            elif capsule_type == "Remix":
                differences = [
                    {
                        "Attribute": "Attribution Strategy",
                        "Sample A": capsule1.attribution_strategy,
                        "Sample B": capsule2.attribution_strategy,
                    },
                    {
                        "Attribute": "Source Count",
                        "Sample A": len(capsule1.source_capsule_ids),
                        "Sample B": len(capsule2.source_capsule_ids),
                    },
                ]

            df = pd.DataFrame(differences)
            st.table(df)

    except Exception as e:
        st.error("Failed to load visualization")
        st.expander("Error Details").exception(e)


def display_consent_visualization(capsule=None):
    """Display Consent capsule visualization.

    Args:
        capsule: Optional capsule instance. If None, creates a sample capsule.
    """
    st.header(f"{CAPSULE_ICONS['Consent']} Consent Capsule Visualization")
    st.markdown(
        f"""
    <div style='padding:10px;background-color:{CAPSULE_COLORS['Consent']}22;border-radius:5px;margin-bottom:20px;'>
    Consent capsules record explicit user consent for specific actions or data usage, providing a clear
    record of what was agreed to, when, and under what conditions.
    </div>
    """,
        unsafe_allow_html=True,
    )

    try:
        # If no capsule provided, create a sample one
        if capsule is None:
            capsule = create_sample_consent_capsule()

        # Validate capsule has required fields
        required_fields = [
            "consent_type",
            "consenting_party",
            "consent_scope",
            "consent_duration",
        ]
        missing_fields = [
            field for field in required_fields if not hasattr(capsule, field)
        ]

        if missing_fields:
            st.warning(
                f"WARNING: Capsule is missing required fields: {', '.join(missing_fields)}"
            )
            st.info("Displaying with limited information")

        # Render the specialized visualization
        render_consent_content(capsule)

        # Add export options
        st.subheader("Export Options")
        col1, col2 = st.columns(2)
        with col1:
            download_capsule_as_json(capsule, filename="consent_capsule")
        with col2:
            download_capsule_as_csv(capsule, filename="consent_capsule")

    except Exception as e:
        st.error(f"Error visualizing Consent capsule: {str(e)}")
        st.expander("Error Details").exception(e)


def display_trust_renewal_visualization(capsule=None):
    """Display Trust Renewal capsule visualization.

    Args:
        capsule: Optional capsule instance. If None, creates a sample capsule.
    """
    st.header(f"{CAPSULE_ICONS['Trust Renewal']} Trust Renewal Capsule Visualization")
    st.markdown(
        f"""
    <div style='padding:10px;background-color:{CAPSULE_COLORS['TrustRenewal']}22;border-radius:5px;margin-bottom:20px;'>
    Trust Renewal capsules establish ongoing verification and trust maintenance processes, ensuring
    that trust relationships remain valid and up-to-date.
    </div>
    """,
        unsafe_allow_html=True,
    )

    try:
        # If no capsule provided, create a sample one
        if capsule is None:
            capsule = create_sample_trust_renewal_capsule()

        # Validate capsule has required fields
        if not hasattr(capsule, "capsule_id") or not hasattr(
            capsule, "verified_claims"
        ):
            st.warning("WARNING: Capsule is missing required fields for visualization")
            st.info("Displaying with limited information")

        # Render the specialized visualization
        render_trust_renewal_content(capsule)

        # Add export options
        st.subheader("Export Options")
        col1, col2 = st.columns(2)
        with col1:
            download_capsule_as_json(capsule, filename="trust_renewal_capsule")
        with col2:
            download_capsule_as_csv(capsule, filename="trust_renewal_capsule")

    except Exception as e:
        st.error(f"Error visualizing Trust Renewal capsule: {str(e)}")
        st.expander("Error Details").exception(e)


def display_governance_visualization(capsule=None):
    """Display Governance capsule visualization.

    Args:
        capsule: Optional capsule instance. If None, creates a sample capsule.
    """
    st.header(f"{CAPSULE_ICONS['Governance']} Governance Capsule Visualization")
    st.markdown(
        f"""
    <div style='padding:10px;background-color:{CAPSULE_COLORS['Governance']}22;border-radius:5px;margin-bottom:20px;'>
    Governance capsules record policy decisions and governance processes, capturing decision-makers,
    rationale, and affected scopes.
    </div>
    """,
        unsafe_allow_html=True,
    )

    try:
        # If no capsule provided, create a sample one
        if capsule is None:
            capsule = create_sample_governance_capsule()

        # Validate capsule has required fields
        if not hasattr(capsule, "governance_type") or not hasattr(
            capsule, "decision_makers"
        ):
            st.warning("WARNING: Capsule is missing required fields for visualization")
            st.info("Displaying with limited information")

        # Render the specialized visualization
        render_governance_content(capsule)

        # Add export options
        st.subheader("Export Options")
        col1, col2 = st.columns(2)
        with col1:
            download_capsule_as_json(capsule, filename="governance_capsule")
        with col2:
            download_capsule_as_csv(capsule, filename="governance_capsule")

    except Exception as e:
        st.error(f"Error visualizing Governance capsule: {str(e)}")
        st.expander("Error Details").exception(e)


def display_economic_visualization(capsule=None):
    """Display Economic capsule visualization.

    Args:
        capsule: Optional capsule instance. If None, creates a sample capsule.
    """
    st.header(f"{CAPSULE_ICONS['Economic']} Economic Capsule Visualization")
    st.markdown(
        f"""
    <div style='padding:10px;background-color:{CAPSULE_COLORS['Economic']}22;border-radius:5px;margin-bottom:20px;'>
    Economic capsules track value attribution and dividend distributions, ensuring fair compensation
    and transparent economic relationships.
    </div>
    """,
        unsafe_allow_html=True,
    )

    try:
        # If no capsule provided, create a sample one
        if capsule is None:
            capsule = create_sample_economic_capsule()

        # Validate capsule has required fields
        required_fields = [
            "economic_event_type",
            "value_amount",
            "dividend_distribution",
        ]
        missing_fields = [
            field for field in required_fields if not hasattr(capsule, field)
        ]

        if missing_fields:
            st.warning(
                f"WARNING: Capsule is missing required fields: {', '.join(missing_fields)}"
            )
            st.info("Displaying with limited information")

        # Render the specialized visualization
        render_economic_content(capsule)

        # Add export options
        st.subheader("Export Options")
        col1, col2 = st.columns(2)
        with col1:
            download_capsule_as_json(capsule, filename="economic_capsule")
        with col2:
            download_capsule_as_csv(capsule, filename="economic_capsule")

    except Exception as e:
        st.error(f"Error visualizing Economic capsule: {str(e)}")
        st.expander("Error Details").exception(e)


def display_simulated_malice_visualization(capsule=None):
    """Display Simulated Malice capsule visualization.

    Args:
        capsule: Optional capsule instance. If None, creates a sample capsule.
    """
    st.header(
        f"{CAPSULE_ICONS['Simulated Malice']} Simulated Malice Capsule Visualization"
    )
    st.markdown(
        f"""
    <div style='padding:10px;background-color:{CAPSULE_COLORS['SimulatedMalice']}22;border-radius:5px;margin-bottom:20px;'>
    Simulated Malice capsules document security testing scenarios, including simulated attacks,
    vulnerabilities tested, and security responses.
    </div>
    """,
        unsafe_allow_html=True,
    )

    try:
        # If no capsule provided, create a sample one
        if capsule is None:
            capsule = create_sample_simulated_malice_capsule()

        # Validate capsule has required fields
        required_fields = [
            "simulation_type",
            "target_vulnerability",
            "simulation_outcome",
            "detection_success",
        ]
        missing_fields = [
            field for field in required_fields if not hasattr(capsule, field)
        ]

        if missing_fields:
            st.warning(
                f"WARNING: Capsule is missing required fields: {', '.join(missing_fields)}"
            )
            st.info("Displaying with limited information")

        # Render the specialized visualization
        render_simulated_malice_content(capsule)

        # Add export options
        st.subheader("Export Options")
        col1, col2 = st.columns(2)
        with col1:
            download_capsule_as_json(capsule, filename="simulated_malice_capsule")
        with col2:
            download_capsule_as_csv(capsule, filename="simulated_malice_capsule")

    except Exception as e:
        st.error(f"Error visualizing Simulated Malice capsule: {str(e)}")
        st.expander("Error Details").exception(e)


def display_capsule_expiration_visualization(capsule=None):
    """Display Capsule Expiration capsule visualization.

    Args:
        capsule: Optional capsule instance. If None, creates a sample capsule.
    """
    st.header(f"{CAPSULE_ICONS['Capsule Expiration']} Capsule Expiration Visualization")
    st.markdown(
        f"""
    <div style='padding:10px;background-color:{CAPSULE_COLORS['CapsuleExpiration']}22;border-radius:5px;margin-bottom:20px;'>
    Capsule Expiration capsules manage the lifecycle and validity period of other capsules, ensuring
    that expired content is properly handled.
    </div>
    """,
        unsafe_allow_html=True,
    )

    try:
        # If no capsule provided, create a sample one
        if capsule is None:
            capsule = create_sample_capsule_expiration()

        # Validate capsule has required fields
        required_fields = ["target_capsule_ids", "expiration_type", "expiration_date"]
        missing_fields = [
            field for field in required_fields if not hasattr(capsule, field)
        ]

        if missing_fields:
            st.warning(
                f"WARNING: Capsule is missing required fields: {', '.join(missing_fields)}"
            )
            st.info("Displaying with limited information")

        # Render the specialized visualization
        render_capsule_expiration_content(capsule)

        # Add export options
        st.subheader("Export Options")
        col1, col2 = st.columns(2)
        with col1:
            download_capsule_as_json(capsule, filename="capsule_expiration")
        with col2:
            download_capsule_as_csv(capsule, filename="capsule_expiration")

    except Exception as e:
        st.error(f"Error visualizing Capsule Expiration data: {str(e)}")
        st.expander("Error Details").exception(e)


def display_self_hallucination_visualization(capsule=None):
    """Display Self Hallucination capsule visualization.

    Args:
        capsule: Optional capsule instance. If None, creates a sample capsule.
    """
    st.header(
        f"{CAPSULE_ICONS.get('Self Hallucination', '')} Self Hallucination Capsule Visualization"
    )
    st.markdown(
        f"""
    <div style='padding:10px;background-color:{CAPSULE_COLORS.get('SelfHallucination', '#ff7f50')}22;border-radius:5px;margin-bottom:20px;'>
    Self Hallucination capsules document instances where an agent has detected and corrected its own
    inaccurate knowledge or reasoning, creating a transparent record of error detection and resolution.
    </div>
    """,
        unsafe_allow_html=True,
    )

    try:
        # If no capsule provided, create a sample one
        if capsule is None:
            capsule = create_sample_self_hallucination_capsule()

        # Validate capsule has required fields
        required_fields = [
            "hallucination_type",
            "detected_hallucinations",
            "correction_process",
        ]
        missing_fields = [
            field for field in required_fields if not hasattr(capsule, field)
        ]

        if missing_fields:
            st.warning(
                f"WARNING: Capsule is missing required fields: {', '.join(missing_fields)}"
            )
            st.info("Displaying with limited information")

        # Render the specialized visualization
        render_self_hallucination_content(capsule)

        # Add export options
        st.subheader("Export Options")
        col1, col2 = st.columns(2)
        with col1:
            download_capsule_as_json(capsule, filename="self_hallucination_capsule")
        with col2:
            download_capsule_as_csv(capsule, filename="self_hallucination_capsule")

    except Exception as e:
        st.error(f"Error visualizing Self Hallucination capsule: {str(e)}")
        st.expander("Error Details").exception(e)


def display_value_inception_visualization(capsule=None):
    """Display Value Inception capsule visualization.

    Args:
        capsule: Optional capsule instance. If None, creates a sample capsule.
    """
    st.header(
        f"{CAPSULE_ICONS.get('Value Inception', '')} Value Inception Capsule Visualization"
    )
    st.markdown(
        f"""
    <div style='padding:10px;background-color:{CAPSULE_COLORS.get('ValueInception', '#2e8b57')}22;border-radius:5px;margin-bottom:20px;'>
    Value Inception capsules document ethical reasoning processes, value hierarchies, and value trade-offs
    made by agents when making significant decisions with ethical implications.
    </div>
    """,
        unsafe_allow_html=True,
    )

    try:
        # If no capsule provided, create a sample one
        if capsule is None:
            capsule = create_sample_value_inception_capsule()

        # Validate capsule has required fields
        required_fields = [
            "value_framework",
            "value_assertions",
            "ethical_justification",
            "stakeholder_considerations",
        ]
        missing_fields = [
            field for field in required_fields if not hasattr(capsule, field)
        ]

        if missing_fields:
            st.warning(
                f"WARNING: Capsule is missing required fields: {', '.join(missing_fields)}"
            )
            st.info("Displaying with limited information")

        # Render the specialized visualization
        render_value_inception_content(capsule)

        # Add export options
        st.subheader("Export Options")
        col1, col2 = st.columns(2)
        with col1:
            download_capsule_as_json(capsule, filename="value_inception_capsule")
        with col2:
            download_capsule_as_csv(capsule, filename="value_inception_capsule")

    except Exception as e:
        st.error(f"Error visualizing Value Inception capsule: {str(e)}")
        st.expander("Error Details").exception(e)


def display_temporal_signature_visualization(capsule=None):
    """Display Temporal Signature capsule visualization.

    Args:
        capsule: Optional capsule instance. If None, creates a sample capsule.
    """
    st.header(
        f"{CAPSULE_ICONS.get('Temporal Signature', '')} Temporal Signature Capsule Visualization"
    )
    st.markdown(
        f"""
    <div style='padding:10px;background-color:{CAPSULE_COLORS.get('TemporalSignature', '#4682b4')}22;border-radius:5px;margin-bottom:20px;'>
    Temporal Signature capsules establish knowledge cutoff dates and temporal boundaries for content,
    providing clear documentation of data currency and validity periods.
    </div>
    """,
        unsafe_allow_html=True,
    )

    try:
        # If no capsule provided, create a sample one
        if capsule is None:
            capsule = create_sample_temporal_signature_capsule()

        # Validate capsule has required fields
        required_fields = [
            "temporal_assertion_type",
            "knowledge_cutoff_date",
            "temporal_scope",
            "verification_sources",
        ]
        missing_fields = [
            field for field in required_fields if not hasattr(capsule, field)
        ]

        if missing_fields:
            st.warning(
                f"WARNING: Capsule is missing required fields: {', '.join(missing_fields)}"
            )
            st.info("Displaying with limited information")

        # Render the specialized visualization
        render_temporal_signature_content(capsule)

        # Add export options
        st.subheader("Export Options")
        col1, col2 = st.columns(2)
        with col1:
            download_capsule_as_json(capsule, filename="temporal_signature_capsule")
        with col2:
            download_capsule_as_csv(capsule, filename="temporal_signature_capsule")

    except Exception as e:
        st.error(f"Error visualizing Temporal Signature capsule: {str(e)}")
        st.expander("Error Details").exception(e)


def display_remix_visualization(capsule=None):
    """Display Remix capsule visualization.

    Args:
        capsule: Optional capsule instance. If None, creates a sample capsule.
    """
    st.header(f"{CAPSULE_ICONS.get('Remix', '')} Remix Capsule Visualization")
    st.markdown(
        f"""
    <div style='padding:10px;background-color:{CAPSULE_COLORS.get('Remix', '#8a2be2')}22;border-radius:5px;margin-bottom:20px;'>
    Remix capsules track derivative content creation with proper attribution and licensing information,
    ensuring that content reuse and remixing follows appropriate rules and provides credit.
    </div>
    """,
        unsafe_allow_html=True,
    )

    try:
        # If no capsule provided, create a sample one
        if capsule is None:
            capsule = create_sample_remix_capsule()

        # Validate capsule has required fields
        required_fields = [
            "source_capsule_ids",
            "remix_proportions",
            "attribution_strategy",
            "license_terms",
        ]
        missing_fields = [
            field for field in required_fields if not hasattr(capsule, field)
        ]

        if missing_fields:
            st.warning(
                f"WARNING: Capsule is missing required fields: {', '.join(missing_fields)}"
            )
            st.info("Displaying with limited information")

        # Render the specialized visualization
        render_remix_content(capsule)

        # Add export options
        st.subheader("Export Options")
        col1, col2 = st.columns(2)
        with col1:
            download_capsule_as_json(capsule, filename="remix_capsule")
        with col2:
            download_capsule_as_csv(capsule, filename="remix_capsule")

    except Exception as e:
        st.error(f"Error visualizing Remix capsule: {str(e)}")
        st.expander("Error Details").exception(e)


def create_sample_consent_capsule():
    """Create a sample Consent capsule with realistic data.

    This function generates a realistic sample ConsentCapsule for visualization
    and testing purposes. It includes all required fields defined in the
    ConsentCapsule schema with representative values that demonstrate a
    typical user consent scenario.

    Returns:
        ConsentCapsule: A fully populated consent capsule instance.

    Raises:
        Exception: If capsule creation fails due to schema validation errors
                  or missing required dependencies.
    """
    try:
        # Calculate timestamps
        now = datetime.now()
        consent_time = now - timedelta(days=30)
        expiry_time = consent_time + timedelta(days=365)  # 1-year consent

        # Base capsule data
        capsule_data = {
            # Required base capsule fields
            "capsule_id": "consent_demo_123456",
            "capsule_type": "Consent",
            "agent_id": "privacy-management-agent-001",
            "confidence": 0.95,
            "signature": "0x8b2c4f6e8d0a2c4f6e8d0a2c4f6e8d0a2c4f6e8d",
            "reasoning_trace": [
                "User explicitly provided consent through the privacy portal after reviewing all terms and conditions."
            ],
            # Consent-specific fields - match the exact field names required by ConsentCapsule
            "consent_provider": "user12345",
            "consent_scope": "data_processing_and_analytics",
            "revocable": True,
            "conditions": [
                "Data will be anonymized before analysis",
                "Data will not be shared with third parties",
                "User can request data deletion at any time",
                "Processing limited to service improvement purposes",
            ],
            "consent_verification_method": "multi_factor_authentication",
            "consent_duration": "P1Y",  # ISO 8601 period format: 1 year
            "consent_details": {
                "context": "Web application usage data for service improvement",
                "revocation_method": "User dashboard or email to privacy@example.com",
                "revocation_status": "active",  # not revoked
                "expiration_timestamp": expiry_time.isoformat(),
                "related_entities": {
                    "data_controller": "Example Corp",
                    "data_processor": "Analytics Division",
                    "oversight_authority": "Privacy Office",
                },
                "verification_details": {
                    "method": "2FA",
                    "timestamp": consent_time.isoformat(),
                    "verification_id": "ver_12345abcde",
                },
                "affected_resources": [
                    "user_behavior_logs",
                    "feature_usage_statistics",
                    "performance_metrics",
                ],
            },
            # Additional metadata
            "timestamp": consent_time.isoformat(),
        }

        # Create and return the capsule instance
        return ConsentCapsule(**capsule_data)

    except ImportError as ie:
        raise Exception(
            f"Failed to import required modules: {str(ie)}. Check that all dependencies are installed."
        )

    except TypeError as te:
        raise Exception(
            f"Invalid parameter type in capsule data: {str(te)}. Check field formats match schema requirements."
        )

    except ValueError as ve:
        raise Exception(
            f"Invalid value in consent capsule data: {str(ve)}. Check date formats and ISO duration strings."
        )

    except Exception as e:
        raise Exception(
            f"Error creating sample Consent capsule: {type(e).__name__}: {str(e)}"
        )


def create_sample_trust_renewal_capsule():
    """Create a sample Trust Renewal capsule with realistic data.

    This function generates a realistic sample TrustRenewalCapsule for visualization
    and testing purposes. It includes all required fields defined in the
    TrustRenewalCapsule schema with representative values that demonstrate
    trust verification claims with various statuses and confidence levels.

    Returns:
        TrustRenewalCapsule: A fully populated trust renewal capsule instance.

    Raises:
        Exception: If capsule creation fails due to schema validation errors
                  or missing required dependencies.
    """
    try:
        # Calculate timestamps
        now = datetime.now()
        verification_time = now - timedelta(hours=12)
        creation_time = verification_time - timedelta(hours=1)

        # Base capsule data
        capsule_data = {
            # Required base capsule fields
            "capsule_id": "trust_renewal_demo_123456",
            "capsule_type": "TrustRenewal",
            "agent_id": "trust-verification-agent-001",
            "confidence": 0.92,
            "signature": "0xa1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4",
            "reasoning_trace": [
                "Periodic trust renewal triggered by time-based policy",
                "All verification checks passed with acceptable confidence levels",
            ],
            # Trust Renewal-specific fields
            "renewal_type": "Periodic",
            "previous_trust_capsule_id": "uatp_7_tr_93826401fe67bc3d",
            "trust_metrics": {
                "identity_confidence": 0.95,
                "behavior_consistency": 0.88,
                "historical_reliability": 0.92,
                "transparency_score": 0.85,
                "security_compliance": 0.91,
            },
            "renewal_period": "P90D",  # 90 days in ISO 8601 duration format
            "verification_method": "Hybrid Automated and Manual Review",
            # Additional Trust Renewal fields
            "verification_results": {
                "identity_verification": {
                    "status": "passed",
                    "confidence": 0.95,
                    "method": "biometric",
                    "timestamp": verification_time.isoformat(),
                },
                "credential_verification": {
                    "status": "passed",
                    "confidence": 0.98,
                    "method": "cryptographic",
                    "timestamp": verification_time.isoformat(),
                },
                "behavior_analysis": {
                    "status": "passed",
                    "confidence": 0.88,
                    "anomalies_detected": "none",
                    "timestamp": verification_time.isoformat(),
                },
                "compliance_check": {
                    "status": "passed",
                    "confidence": 0.91,
                    "details": "All required security policies satisfied",
                    "timestamp": verification_time.isoformat(),
                },
            },
            "verified_claims": [
                {
                    "claim_type": "identity",
                    "status": "verified",
                    "timestamp": verification_time.isoformat(),
                    "verification_method": "biometric",
                },
                {
                    "claim_type": "credentials",
                    "status": "verified",
                    "timestamp": verification_time.isoformat(),
                    "verification_method": "cryptographic",
                },
                {
                    "claim_type": "permissions",
                    "status": "verified",
                    "timestamp": verification_time.isoformat(),
                    "verification_method": "policy-based",
                },
                {
                    "claim_type": "security_compliance",
                    "status": "verified",
                    "timestamp": verification_time.isoformat(),
                    "verification_method": "automated",
                },
            ],
            "renewal_conditions": {
                "required_verifications": [
                    "identity verification",
                    "credential verification",
                    "behavior analysis",
                    "compliance check",
                ],
                "minimum_trust_score": 0.8,
                "required_claims": ["identity", "credentials", "permissions"],
            },
            "renewal_justification": """
            Trust renewal approved based on:
            1. All identity verification checks passed
            2. All credential verification checks passed
            3. Behavior analysis indicates normal patterns with no anomalies
            4. All security compliance requirements met
            5. Overall trust score remains above minimum threshold

            This renewal extends trust for a standard 90-day period with no restrictions.
            """,
            # Timestamp for timeline visualization
            "timestamp": creation_time.isoformat(),
        }

        # Create and return the capsule instance
        return TrustRenewalCapsule(**capsule_data)

    except ImportError as ie:
        raise Exception(
            f"Failed to import required modules: {str(ie)}. Check that all dependencies are installed."
        )

    except TypeError as te:
        raise Exception(
            f"Invalid parameter type in capsule data: {str(te)}. Check field formats match schema requirements."
        )

    except ValueError as ve:
        raise Exception(
            f"Invalid value in capsule data: {str(ve)}. Check date formats and value ranges."
        )

    except Exception as e:
        raise Exception(
            f"Error creating sample Trust Renewal capsule: {type(e).__name__}: {str(e)}"
        )


def create_sample_governance_capsule():
    """
    Create a sample Governance capsule with realistic data.

    This function generates a realistic sample GovernanceCapsule for visualization
    and testing purposes. It includes all required fields defined in the
    GovernanceCapsule schema with representative values that demonstrate a
    policy update governance action with voting results, stakeholder input,
    implementation timeline, and affected systems.

    Returns:
        GovernanceCapsule: A fully populated governance capsule instance.

    Raises:
        Exception: If capsule creation fails due to schema validation errors
                  or missing required dependencies.
    """
    try:
        # Calculate timestamps
        now = datetime.now()
        vote_end_time = now - timedelta(days=2)
        vote_start_time = vote_end_time - timedelta(days=7)
        implementation_time = now + timedelta(days=14)

        # Base capsule data
        capsule_data = {
            # Required base capsule fields
            "capsule_id": "governance_demo_123456",
            "capsule_type": "Governance",
            "agent_id": "governance-coordinator-001",
            "confidence": 0.98,
            "signature": "0xfe9a7c02e5d8b6a13c87d9e15f02c27a98c734b2",
            "reasoning_trace": [
                "Governance proposal submitted by authorized stakeholder",
                "Voting threshold achieved with 78% approval",
                "Decision ratified by governance committee",
            ],
            # Governance-specific fields
            "governance_type": "PolicyUpdate",
            "policy_id": "UATP-GOV-2025-042",
            "decision_makers": [
                "governance-committee-chair",
                "technical-director",
                "ethics-advisor",
                "stakeholder-representative",
            ],
            "decision_rationale": """
            This policy update introduces enhanced transparency requirements for
            automated decision-making processes. The update addresses concerns raised
            by stakeholders regarding visibility into AI reasoning chains and attribution
            of decision factors. The committee reviewed implementation feasibility and
            determined the benefits outweigh the technical complexity of implementation.
            """,
            "affected_scopes": [
                "automated-decision-systems",
                "reasoning-trace-requirements",
                "explainability-standards",
                "attribution-requirements",
            ],
            "voting_results": {
                "total_votes": 45,
                "approval_votes": 35,
                "rejection_votes": 8,
                "abstention_votes": 2,
            },
            # Additional fields for enhanced visualization
            "governance_action": "Update transparency requirements for automated decision-making processes",
            "governance_details": {
                "proposal_id": "PROP-2025-137",
                "proposal_date": vote_start_time.isoformat(),
                "voting_period": {
                    "start": vote_start_time.isoformat(),
                    "end": vote_end_time.isoformat(),
                },
                "implementation_timeline": {
                    "review_phase": (now + timedelta(days=1)).isoformat(),
                    "development_phase": (now + timedelta(days=7)).isoformat(),
                    "testing_phase": (now + timedelta(days=10)).isoformat(),
                    "deployment_phase": implementation_time.isoformat(),
                },
                "priority_level": "High",
                "legal_compliance": "Required for EU AI Act compliance",
                "technical_complexity": "Medium",
                "affected_systems": [
                    {
                        "system_id": "decision-engine-core",
                        "impact_level": "High",
                        "modification_required": "Update reasoning trace format and storage",
                    },
                    {
                        "system_id": "explainability-module",
                        "impact_level": "High",
                        "modification_required": "Enhance attribution tracking",
                    },
                    {
                        "system_id": "user-interface",
                        "impact_level": "Medium",
                        "modification_required": "Add visualization of decision factors",
                    },
                ],
            },
            "stakeholder_votes": {
                "technical_committee": {
                    "vote": 0.85,
                    "rationale": "Implementation is feasible with reasonable effort",
                    "concerns": "May require refactoring of core decision engine",
                },
                "ethics_board": {
                    "vote": 0.95,
                    "rationale": "Strong alignment with ethical AI principles",
                    "concerns": "None significant",
                },
                "business_stakeholders": {
                    "vote": 0.7,
                    "rationale": "Improves trust but adds development overhead",
                    "concerns": "May delay other planned features",
                },
                "user_representatives": {
                    "vote": 0.9,
                    "rationale": "Significantly improves user trust and understanding",
                    "concerns": "May require additional user education",
                },
                "security_team": {
                    "vote": 0.8,
                    "rationale": "No significant security concerns",
                    "concerns": "Additional logging may increase storage requirements",
                },
            },
            # Timestamp for timeline visualization
            "timestamp": now.isoformat(),
        }

        # Create and return the capsule instance
        return GovernanceCapsule(**capsule_data)

    except ImportError as ie:
        raise Exception(
            f"Failed to import required modules: {str(ie)}. Check that all dependencies are installed."
        )

    except TypeError as te:
        raise Exception(
            f"Invalid parameter type in governance capsule data: {str(te)}. Check field formats match schema requirements."
        )

    except ValueError as ve:
        raise Exception(
            f"Invalid value in governance capsule data: {str(ve)}. Check date formats and value ranges."
        )

    except Exception as e:
        raise Exception(
            f"Error creating sample Governance capsule: {type(e).__name__}: {str(e)}"
        )

    except TypeError as te:
        raise Exception(
            f"Invalid parameter type in governance capsule data: {str(te)}. Check field formats match schema requirements."
        )

    except ValueError as ve:
        raise Exception(
            f"Invalid value in governance capsule data: {str(ve)}. Check date formats and value ranges."
        )

    except Exception as e:
        raise Exception(
            f"Error creating sample Governance capsule: {type(e).__name__}: {str(e)}"
        )

    # Create and return the capsule instance
    return GovernanceCapsule(**capsule_data)


def create_sample_economic_capsule():
    """
    Create a sample Economic capsule with realistic data.

    This function generates a realistic sample EconomicCapsule for visualization
    and testing purposes. It includes all required fields defined in the
    EconomicCapsule schema with representative values that demonstrate a
    content creation value distribution scenario with detailed economic event data,
    value calculations, and dividend distribution information.

    Returns:
        EconomicCapsule: A fully populated economic capsule instance.

    Raises:
        Exception: If capsule creation fails due to schema validation errors
                  or missing required dependencies.
    """
    try:
        now = datetime.now()

        # Base capsule data
        capsule_data = {
            # Required base capsule fields
            "capsule_id": "economic_demo_123456",
            "capsule_type": "Economic",
            "agent_id": "economic-tracking-agent-001",
            "confidence": 0.97,
            "signature": "0xd1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0",
            "reasoning_trace": [
                "Economic attribution analysis completed with high confidence",
                "Dividend distribution calculated based on weighted contributions",
                "Value distribution verified against contribution records",
            ],
            # Economic-specific fields - match the exact field names required by the class
            "economic_event_type": "content_creation_value_distribution",  # required field
            "value_amount": 18500.00,  # total economic value being distributed
            "value_recipients": {  # required field - maps recipients to specific amounts
                "organization-alpha": 5550.00,
                "creator-group-beta": 4625.00,
                "individual-contributor-1": 3700.00,
                "individual-contributor-2": 2775.00,
                "technology-provider": 1850.00,
            },
            "value_calculation_method": "contribution_weighted_distribution",  # required field
            "dividend_distribution": {  # percentage allocation for each contributor
                "organization-alpha": 0.30,
                "creator-group-beta": 0.25,
                "individual-contributor-1": 0.20,
                "individual-contributor-2": 0.15,
                "technology-provider": 0.10,
            },
            "economic_value": {  # detailed breakdown of economic value creation
                "value_source": "collaborative_content_creation",
                "value_metric": "USD",
                "project_id": "content-collab-2025-01",
                "attribution_methodology": "hybrid_contribution_analysis",
                "contributors": [
                    "organization-alpha",
                    "creator-group-beta",
                    "individual-contributor-1",
                    "individual-contributor-2",
                    "technology-provider",
                ],
                "contribution_weights": {
                    "organization-alpha": 0.30,
                    "creator-group-beta": 0.25,
                    "individual-contributor-1": 0.20,
                    "individual-contributor-2": 0.15,
                    "technology-provider": 0.10,
                },
                "value_creation_events": [
                    {
                        "event_id": "content-creation-1",
                        "contributor": "creator-group-beta",
                        "value_contribution": 4500.00,
                        "timestamp": (now - timedelta(days=30)).isoformat(),
                    },
                    {
                        "event_id": "content-refinement-1",
                        "contributor": "individual-contributor-1",
                        "value_contribution": 3700.00,
                        "timestamp": (now - timedelta(days=25)).isoformat(),
                    },
                    {
                        "event_id": "content-review-1",
                        "contributor": "individual-contributor-2",
                        "value_contribution": 2800.00,
                        "timestamp": (now - timedelta(days=20)).isoformat(),
                    },
                    {
                        "event_id": "platform-hosting",
                        "contributor": "technology-provider",
                        "value_contribution": 1850.00,
                        "timestamp": (now - timedelta(days=15)).isoformat(),
                    },
                    {
                        "event_id": "marketing-distribution",
                        "contributor": "organization-alpha",
                        "value_contribution": 5650.00,
                        "timestamp": (now - timedelta(days=10)).isoformat(),
                    },
                ],
                "payment_verification": {
                    "verification_method": "blockchain_ledger",
                    "transaction_id": "0x7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b",
                    "verification_timestamp": now.isoformat(),
                },
            },
            # Optional field for transaction reference
            "transaction_reference": "txn_economic_value_dist_2025_042",
            # Timestamp for timeline visualization
            "timestamp": now.isoformat(),
        }

        # Create and return the capsule instance
        return EconomicCapsule(**capsule_data)

    except ImportError as ie:
        raise Exception(
            f"Failed to import required modules: {str(ie)}. Check that all dependencies are installed."
        )

    except TypeError as te:
        raise Exception(
            f"Invalid parameter type in economic capsule data: {str(te)}. Check field formats match schema requirements."
        )

    except ValueError as ve:
        raise Exception(
            f"Invalid value in economic capsule data: {str(ve)}. Check numeric values and ensure dividend distribution sums to 1.0."
        )

    except Exception as e:
        raise Exception(
            f"Error creating sample Economic capsule: {type(e).__name__}: {str(e)}"
        )


def create_sample_simulated_malice_capsule():
    """Create a sample Simulated Malice capsule with realistic data.

    This function generates a realistic sample SimulatedMaliceCapsule for visualization
    and testing purposes. It includes all required fields defined in the
    SimulatedMaliceCapsule schema with representative values that demonstrate a
    typical security penetration testing scenario with detailed attack vector,
    defense response, and security recommendations.

    Returns:
        SimulatedMaliceCapsule: A fully populated simulated malice capsule instance.

    Raises:
        Exception: If capsule creation fails due to schema validation errors
                  or missing required dependencies.
    """
    try:
        # Create timestamps
        now = datetime.now()
        attack_time = now - timedelta(days=3)

        # Base capsule data
        capsule_data = {
            # Required base capsule fields
            "capsule_id": "malice_simulation_54321",
            "capsule_type": "SimulatedMalice",
            "agent_id": "security-testing-agent-001",
            "confidence": 0.98,
            "signature": "0x9c8d7e6f5a4b3c2d1e0f1a2b3c4d5e6f7g8h9i0j",
            "reasoning_trace": [
                "Performing authorized simulated attack to test security systems",
                "Attack targeted known vulnerability in authentication system",
                "Attack detected by monitoring systems within 3.5 seconds",
                "Automated defenses engaged correctly",
            ],
            # SimulatedMalice-specific fields
            "simulation_type": "penetration_test",
            "target_vulnerability": "oauth_token_validation",
            "simulation_outcome": "vulnerability_confirmed",
            "detection_success": True,
            "time_to_detection": "PT3.5S",  # 3.5 seconds in ISO format
            "authorization": {  # Required dict
                "authorized_by": "security_officer_jane_doe",
                "authorization_id": "SEC-TEST-AUTH-789",
                "scope": "limited_production_environment",
                "notification_targets": ["security@example.com", "devops@example.com"],
            },
            "attack_vector": {  # Required dict
                "method": "token_manipulation",
                "technical_details": "Modified OAuth bearer tokens to bypass validation checks",
                "complexity": "medium",
                "prerequisites": [
                    "Access to valid bearer token format",
                    "Understanding of token validation flow",
                ],
                "cve_reference": "CVE-2023-12345",
            },
            "defense_response": {  # Required dict
                "detection_method": "anomaly_detection",
                "response_actions": [
                    "token_invalidation",
                    "ip_blocking",
                    "alert_generation",
                ],
                "response_time": "PT1.2S",  # 1.2 seconds in ISO format
                "effectiveness_rating": 0.85,
            },
            "recommendations": [  # Required list of dicts
                {
                    "priority": "Critical",
                    "recommendation": "Fix privilege escalation vulnerability in permission-management-system",
                    "timeline": "Immediate",
                },
                {
                    "priority": "High",
                    "recommendation": "Implement encryption for sensitive user data",
                    "timeline": "Within 2 weeks",
                },
            ],
            # Timestamp for timeline visualization
            "timestamp": now.isoformat(),
        }

        # Create and return the capsule instance
        return SimulatedMaliceCapsule(**capsule_data)

    except ImportError as ie:
        raise Exception(
            f"Failed to import required modules: {str(ie)}. Check that all dependencies are installed."
        )

    except TypeError as te:
        raise Exception(
            f"Invalid parameter type in capsule data: {str(te)}. Check field formats match schema requirements."
        )

    except ValueError as ve:
        raise Exception(
            f"Invalid value in capsule data: {str(ve)}. Check that all fields have appropriate values."
        )

    except Exception as e:
        raise Exception(
            f"Error creating sample Simulated Malice capsule: {type(e).__name__}: {str(e)}"
        )


def create_sample_capsule_expiration():
    """
    Create a sample Capsule Expiration capsule with realistic data.

    This function generates a realistic sample CapsuleExpirationCapsule for visualization
    and testing purposes. It includes all required fields defined in the
    CapsuleExpirationCapsule schema with representative values that demonstrate a
    time-based expiration policy with archival details, notification schedules,
    and renewal options.

    Returns:
        CapsuleExpirationCapsule: A fully populated capsule expiration capsule instance.

    Raises:
        Exception: If capsule creation fails due to schema validation errors
                  or missing required dependencies.
    """
    try:
        now = datetime.now()
        creation_time = now - timedelta(days=5)
        expiry_time = now + timedelta(days=90)  # 90-day expiration

        # Base capsule data
        capsule_data = {
            # Required base capsule fields
            "capsule_id": "expiration_demo_123456",
            "capsule_type": "CapsuleExpiration",
            "agent_id": "lifecycle-management-agent-001",
            "confidence": 0.99,
            "signature": "0x1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t",
            "reasoning_trace": [
                "Expiration policy applied to target capsule",
                "Expiration conditions validated and enforced",
                "Notification schedule created for affected parties",
            ],
            # CapsuleExpiration-specific fields - match the exact field names required by the class
            "target_capsule_ids": [
                "consent_capsule_98765432",
                "consent_capsule_87654321",
            ],  # List of IDs
            "expiration_type": "time_based",
            "expiration_date": expiry_time.isoformat(),
            "expiration_reason": "Standard consent validity period",
            # Required dictionary fields
            "archival_policy": {
                "retention_period": "P5Y",  # 5 years in ISO format
                "storage_location": "secure-archive-storage",
                "access_controls": {
                    "authorized_roles": [
                        "data_governance",
                        "legal_compliance",
                        "privacy_officer",
                    ],
                    "requires_justification": True,
                    "access_logging": True,
                },
                "deletion_schedule": "automatic",
                "deletion_date": (expiry_time + timedelta(days=365 * 5)).isoformat(),
            },
            "expiration_data": {
                "notification_targets": [
                    "user12345@example.com",
                    "privacy-officer@example.com",
                ],
                "notification_schedule": {
                    "first_notice": (expiry_time - timedelta(days=30)).isoformat(),
                    "second_notice": (expiry_time - timedelta(days=15)).isoformat(),
                    "final_notice": (expiry_time - timedelta(days=3)).isoformat(),
                },
                "expiration_actions": [
                    "invalidate_consent",
                    "notify_affected_parties",
                    "log_expiration_event",
                    "trigger_renewal_workflow",
                ],
                "renewal_options": {
                    "renewable": True,
                    "renewal_process": "user_initiated",
                    "renewal_url": "https://example.com/renew/consent/98765432",
                },
                "lifecycle_policy_id": "CONSENT-LIFECYCLE-POLICY-001",
                "affected_capsule_types": ["Consent"],
                "expiration_impact": "Renders consent invalid for further processing",
            },
            # Optional fields
            "grace_period": "P15D",  # 15 days grace period in ISO format
            # Timestamp for timeline visualization
            "timestamp": creation_time.isoformat(),
        }

        # Create and return the capsule instance
        return CapsuleExpirationCapsule(**capsule_data)

    except ImportError as ie:
        raise Exception(
            f"Failed to import required modules: {str(ie)}. Check that all dependencies are installed."
        )

    except TypeError as te:
        raise Exception(
            f"Invalid parameter type in capsule expiration data: {str(te)}. Check field formats match schema requirements."
        )

    except ValueError as ve:
        raise Exception(
            f"Invalid value in capsule expiration data: {str(ve)}. Check date formats and ISO duration strings."
        )

    except Exception as e:
        raise Exception(
            f"Error creating sample Capsule Expiration capsule: {type(e).__name__}: {str(e)}"
        )


def create_sample_self_hallucination_capsule():
    """
    Create a sample SelfHallucination capsule with realistic data.

    This function generates a realistic sample SelfHallucinationCapsule for visualization
    and testing purposes. It includes all required fields defined in the
    SelfHallucinationCapsule schema with representative values that demonstrate
    self-identified factual fabrication or uncertainty with detailed hallucination
    assessment and corrective actions.

    Returns:
        SelfHallucinationCapsule: A fully populated self-hallucination capsule instance.

    Raises:
        Exception: If capsule creation fails due to schema validation errors
                  or missing required dependencies.
    """
    try:
        # Calculate timestamps
        now = datetime.now()
        detection_time = now - timedelta(minutes=15)

        # Base capsule data
        capsule_data = {
            # Required base capsule fields
            "capsule_id": "self_hallucination_demo_123456",
            "capsule_type": "SelfHallucination",
            "agent_id": "self-monitoring-agent-001",
            "confidence": 0.93,
            "signature": "0x3f4e5d6c7b8a9f8e7d6c5b4a3f2e1d0c9b8a7f6e",
            "reasoning_trace": [
                "Internal consistency check triggered anomaly detection",
                "Factual verification against knowledge base failed",
                "Uncertainty threshold exceeded for generated claim",
            ],
            # SelfHallucination-specific fields
            "hallucination_type": "factual_fabrication",
            "affected_content": "The European Union was founded in 1975 with 8 initial member states",
            "confidence_assessment": {
                "factual_accuracy": 0.15,
                "internal_consistency": 0.35,
                "knowledge_boundary": 0.25,
                "uncertainty_level": 0.85,
            },
            "detection_method": "knowledge_validation_check",
            "corrective_action": "Content corrected with verified information: EU predecessor (EEC) founded in 1957 with 6 member states",
            # Required list of hallucination markers
            "self_hallucination_markers": [
                {
                    "marker_type": "factual_error",
                    "confidence": 0.92,
                    "description": "Incorrect founding date (1975 vs 1957)",
                    "detection_method": "knowledge_base_comparison",
                },
                {
                    "marker_type": "factual_error",
                    "confidence": 0.95,
                    "description": "Incorrect number of founding members (8 vs 6)",
                    "detection_method": "knowledge_base_comparison",
                },
                {
                    "marker_type": "concept_error",
                    "confidence": 0.88,
                    "description": "Terminology confusion between EU and EEC",
                    "detection_method": "entity_relationship_validation",
                },
            ],
            # Additional fields for enhanced visualization
            "hallucination_details": {
                "severity_score": 0.78,
                "verification_sources": [
                    "internal_knowledge_base",
                    "historical_records_database",
                    "fact_checking_system",
                ],
                "potential_causes": [
                    "knowledge_retrieval_error",
                    "context_misinterpretation",
                    "training_data_limitation",
                ],
                "correction_confidence": 0.96,
                "impact_assessment": "Medium - factual error without safety implications",
                "verification_process": {
                    "steps": [
                        "Initial content generation",
                        "Self-monitoring trigger based on confidence threshold",
                        "Knowledge base verification",
                        "Inconsistency identification",
                        "Correction formulation",
                    ],
                    "duration_ms": 342,
                    "verification_timestamp": detection_time.isoformat(),
                },
            },
            # Timestamp for timeline visualization
            "timestamp": now.isoformat(),
        }

        # Create and return the capsule instance
        return SelfHallucinationCapsule(**capsule_data)

    except ImportError as ie:
        raise Exception(
            f"Failed to import required modules: {str(ie)}. Check that all dependencies are installed."
        )

    except TypeError as te:
        raise Exception(
            f"Invalid parameter type in self-hallucination data: {str(te)}. Check field formats match schema requirements."
        )

    except ValueError as ve:
        raise Exception(
            f"Invalid value in self-hallucination data: {str(ve)}. Check confidence values are within 0-1 range."
        )

    except Exception as e:
        raise Exception(
            f"Error creating sample Self Hallucination capsule: {type(e).__name__}: {str(e)}"
        )


def create_sample_value_inception_capsule():
    """
    Create a sample ValueInception capsule with realistic data.

    This function generates a realistic sample ValueInceptionCapsule for visualization
    and testing purposes. It includes all required fields defined in the
    ValueInceptionCapsule schema with representative values that demonstrate
    ethical justification and value alignment decisions with detailed
    stakeholder considerations and value trade-offs.

    Returns:
        ValueInceptionCapsule: A fully populated value inception capsule instance.

    Raises:
        Exception: If capsule creation fails due to schema validation errors
                  or missing required dependencies.
    """
    try:
        # Current timestamp
        now = datetime.now()

        # Base capsule data
        capsule_data = {
            # Required base capsule fields
            "capsule_id": "value_inception_demo_123456",
            "capsule_type": "ValueInception",
            "agent_id": "ethical-reasoning-agent-001",
            "confidence": 0.89,
            "signature": "0x7d8e9f0a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
            "reasoning_trace": [
                "Ethical framework evaluation initiated for healthcare data access decision",
                "Multiple stakeholder values and rights identified and prioritized",
                "Balanced consideration of privacy, care quality, and research benefits",
            ],
            # ValueInception-specific fields
            "value_framework": "principled_pluralism",
            "value_assertions": [
                "Individual privacy rights must be respected",
                "Data use should maximize healthcare outcomes",
                "Informed consent is foundational to ethical data use",
                "Vulnerable populations require additional protections",
                "Transparency in data practices builds trust",
            ],
            "ethical_justification": """
            This decision balances the imperative to improve healthcare outcomes through
            data-driven insights with the fundamental right to privacy and data autonomy.
            By implementing tiered access controls, robust anonymization, clear consent
            mechanisms, and oversight protocols, we establish a framework that respects
            individual rights while enabling beneficial research and care improvement.

            The solution prioritizes informed consent while recognizing contexts where
            aggregate, anonymized data may ethically be used for public health benefits
            under appropriate governance structures.
            """,
            # Structured stakeholder considerations
            "stakeholder_considerations": {
                "patients": {
                    "interests": [
                        "privacy",
                        "improved_care",
                        "data_security",
                        "autonomy",
                    ],
                    "potential_harms": [
                        "privacy_violations",
                        "discrimination",
                        "loss_of_control",
                    ],
                    "potential_benefits": [
                        "better_treatments",
                        "improved_diagnostics",
                        "personalized_care",
                    ],
                },
                "healthcare_providers": {
                    "interests": [
                        "clinical_insights",
                        "efficiency",
                        "evidence_based_practice",
                    ],
                    "potential_harms": ["workflow_disruption", "liability_concerns"],
                    "potential_benefits": [
                        "better_decision_support",
                        "improved_outcomes",
                        "reduced_errors",
                    ],
                },
                "researchers": {
                    "interests": [
                        "data_access",
                        "statistical_significance",
                        "reproducibility",
                    ],
                    "potential_harms": ["research_delays", "incomplete_data"],
                    "potential_benefits": [
                        "discovery_acceleration",
                        "population_insights",
                    ],
                },
                "society": {
                    "interests": [
                        "public_health",
                        "medical_advancement",
                        "resource_efficiency",
                    ],
                    "potential_harms": ["trust_erosion", "equity_concerns"],
                    "potential_benefits": [
                        "disease_reduction",
                        "healthcare_improvement",
                        "cost_reduction",
                    ],
                },
            },
            # Value hierarchy (ordered by priority)
            "values_hierarchy": [
                {
                    "value": "individual_autonomy",
                    "priority_level": "highest",
                    "justification": "Fundamental respect for persons and their right to self-determination",
                },
                {
                    "value": "non_maleficence",
                    "priority_level": "very_high",
                    "justification": "Obligation to prevent harm, especially to vulnerable populations",
                },
                {
                    "value": "justice_and_equity",
                    "priority_level": "high",
                    "justification": "Fair distribution of benefits and burdens",
                },
                {
                    "value": "beneficence",
                    "priority_level": "high",
                    "justification": "Promoting welfare and advancing healthcare",
                },
                {
                    "value": "transparency",
                    "priority_level": "medium",
                    "justification": "Building trust and enabling accountability",
                },
            ],
            # Ethical trade-offs considered
            "trade_offs": [
                {
                    "values": ["individual_privacy", "population_health_benefits"],
                    "tension": "Restricting data access protects privacy but may limit medical advances",
                    "resolution": "Tiered access system with anonymization appropriate to sensitivity",
                    "reasoning": "Balances individual rights with collective benefits through proportional controls",
                },
                {
                    "values": ["research_advancement", "informed_consent"],
                    "tension": "Requiring specific consent for each use limits research agility",
                    "resolution": "Broad consent with governance and opt-out mechanisms",
                    "reasoning": "Respects autonomy while enabling beneficial research within ethical boundaries",
                },
                {
                    "values": ["data_accessibility", "security"],
                    "tension": "Easier access increases utility but may increase vulnerability",
                    "resolution": "Robust security infrastructure with access controls proportional to data sensitivity",
                    "reasoning": "Technical safeguards can mitigate security risks while supporting appropriate access",
                },
            ],
            # Additional metadata for visualization
            "decision_context": {
                "domain": "healthcare_data_ethics",
                "urgency": "medium",
                "scale_of_impact": "high",
                "decision_type": "policy_framework",
                "implementation_timeline": {
                    "policy_development": (now + timedelta(days=30)).isoformat(),
                    "stakeholder_review": (now + timedelta(days=60)).isoformat(),
                    "implementation": (now + timedelta(days=90)).isoformat(),
                    "evaluation": (now + timedelta(days=180)).isoformat(),
                },
            },
            # Timestamp for timeline visualization
            "timestamp": now.isoformat(),
        }

        # Create and return the capsule instance
        return ValueInceptionCapsule(**capsule_data)

    except ImportError as ie:
        raise Exception(
            f"Failed to import required modules: {str(ie)}. Check that all dependencies are installed."
        )

    except TypeError as te:
        raise Exception(
            f"Invalid parameter type in value inception data: {str(te)}. Check field formats match schema requirements."
        )

    except ValueError as ve:
        raise Exception(
            f"Invalid value in value inception data: {str(ve)}. Check that fields have appropriate values."
        )

    except Exception as e:
        raise Exception(
            f"Error creating sample Value Inception capsule: {type(e).__name__}: {str(e)}"
        )


def create_sample_temporal_signature_capsule():
    """
    Create a sample TemporalSignature capsule with realistic data.

    This function generates a realistic sample TemporalSignatureCapsule for visualization
    and testing purposes. It includes all required fields defined in the
    TemporalSignatureCapsule schema with representative values that demonstrate
    knowledge cutoff markers and temporal boundaries for content validation.

    Returns:
        TemporalSignatureCapsule: A fully populated temporal signature capsule instance.

    Raises:
        Exception: If capsule creation fails due to schema validation errors
                  or missing required dependencies.
    """
    try:
        # Calculate timestamps
        now = datetime.now()
        cutoff_date = now - timedelta(days=90)  # 90 days ago knowledge cutoff

        # Base capsule data
        capsule_data = {
            # Required base capsule fields
            "capsule_id": "temporal_signature_demo_123456",
            "capsule_type": "TemporalSignature",
            "agent_id": "temporal-verification-agent-001",
            "confidence": 0.99,
            "signature": "0x5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b",
            "reasoning_trace": [
                "Knowledge boundaries established for financial report content",
                "Temporal boundaries verified against authoritative sources",
                "Content validated against established cutoff date",
            ],
            # TemporalSignature-specific fields
            "temporal_assertion_type": "knowledge_boundary",
            "knowledge_cutoff_date": cutoff_date.isoformat(),
            # Required dictionary with temporal scope details
            "temporal_scope": {
                "scope_type": "financial_reporting_period",
                "start_date": (cutoff_date - timedelta(days=90)).isoformat(),
                "end_date": cutoff_date.isoformat(),
                "relevant_jurisdictions": ["US", "EU", "APAC"],
                "applicable_standards": ["GAAP", "IFRS"],
                "scope_description": "Q2 2025 Financial Reporting Period",
            },
            # Required list of verification sources
            "verification_sources": [
                "SEC EDGAR Database (as of " + cutoff_date.strftime("%Y-%m-%d") + ")",
                "Bloomberg Financial Terminal (data version "
                + cutoff_date.strftime("%Y%m%d")
                + ")",
                "Internal Financial Knowledge Database v2025.2.1",
                "OECD Economic Reports Q2 2025",
            ],
            # Required dictionary with detailed temporal signature metadata
            "temporal_signature_data": {
                "certification_authority": "Financial Knowledge Verification Board",
                "certification_id": "FKVB-TS-2025-06-" + str(cutoff_date.day).zfill(2),
                "verification_method": "cryptographic_timestamping",
                "timestamp_signature": "0xfd8c7b6a5e4d3c2b1a9f8e7d6c5b4a3f2e1d0c9b8",
                "data_integrity_hash": "0x1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t",
                "verification_status": "certified",
                "temporal_assertions": [
                    {
                        "assertion_type": "data_completeness",
                        "assertion": "All required financial data for Q2 2025 included",
                        "confidence": 0.99,
                        "verification_timestamp": (
                            now - timedelta(hours=2)
                        ).isoformat(),
                    },
                    {
                        "assertion_type": "data_currency",
                        "assertion": "All market data current as of cutoff date",
                        "confidence": 0.98,
                        "verification_timestamp": (
                            now - timedelta(hours=2)
                        ).isoformat(),
                    },
                    {
                        "assertion_type": "regulation_compliance",
                        "assertion": "Content complies with reporting regulations effective during period",
                        "confidence": 0.97,
                        "verification_timestamp": (
                            now - timedelta(hours=2)
                        ).isoformat(),
                    },
                ],
                "temporal_boundaries": {
                    "absolute_boundaries": {
                        "earliest_relevant_date": (
                            cutoff_date - timedelta(days=365)
                        ).isoformat(),
                        "latest_relevant_date": cutoff_date.isoformat(),
                    },
                    "relative_boundaries": {
                        "primary_reporting_period": "P3M",  # 3 months in ISO format
                        "historical_context_period": "P1Y",  # 1 year in ISO format
                        "forward_looking_limitations": "Content does not include events or data after cutoff date",
                    },
                },
            },
            # Timestamp for timeline visualization
            "timestamp": now.isoformat(),
        }

        # Create and return the capsule instance
        return TemporalSignatureCapsule(**capsule_data)

    except ImportError as ie:
        raise Exception(
            f"Failed to import required modules: {str(ie)}. Check that all dependencies are installed."
        )

    except TypeError as te:
        raise Exception(
            f"Invalid parameter type in temporal signature data: {str(te)}. Check field formats match schema requirements."
        )

    except ValueError as ve:
        raise Exception(
            f"Invalid value in temporal signature data: {str(ve)}. Check date formats and ISO duration strings."
        )

    except Exception as e:
        raise Exception(
            f"Error creating sample Temporal Signature capsule: {type(e).__name__}: {str(e)}"
        )


def create_sample_remix_capsule():
    """
    Create a sample Remix capsule with realistic data.

    This function generates a realistic sample RemixCapsule for visualization
    and testing purposes. It includes all required fields defined in the
    RemixCapsule schema with representative values that demonstrate
    derivative content with attribution and licensing information.

    Returns:
        RemixCapsule: A fully populated remix capsule instance.

    Raises:
        Exception: If capsule creation fails due to schema validation errors
                  or missing required dependencies.
    """
    try:
        # Current timestamp
        now = datetime.now()

        # Base capsule data
        capsule_data = {
            # Required base capsule fields
            "capsule_id": "remix_demo_123456",
            "capsule_type": "Remix",
            "agent_id": "content-remixing-agent-001",
            "confidence": 0.96,
            "signature": "0x9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b",
            "reasoning_trace": [
                "Source content identified and retrieved",
                "Attribution proportions calculated based on content usage",
                "Derivative work assembled with proper licensing",
            ],
            # Remix-specific fields
            "source_capsule_ids": [
                "original_content_789012",
                "original_content_345678",
                "original_content_901234",
            ],
            # Required attribution proportions by source capsule ID
            "remix_proportions": {
                "original_content_789012": 0.55,  # 55% attribution
                "original_content_345678": 0.30,  # 30% attribution
                "original_content_901234": 0.15,  # 15% attribution
            },
            "attribution_strategy": "content_volume_weighted",
            "derivative_content_hash": "0x2a3b4c5d6e7f8g9h0i1j2k3l4m5n6o7p8q9r0s",
            # Required license terms for the remix
            "license_terms": {
                "remix_license": "Creative Commons Attribution-ShareAlike 4.0",
                "compatible_with_source": True,
                "additional_restrictions": [],
                "permissions": ["share", "adapt", "commercial_use"],
                "conditions": ["attribution", "share_alike"],
                "limitations": ["liability", "warranty"],
                "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
                "license_version": "4.0",
            },
            # Required attribution data with economic metadata
            "attribution_data": {
                "attribution_method": "proportional_content_usage",
                "attribution_calculation": {
                    "content_volume": 0.6,
                    "creative_contribution": 0.3,
                    "uniqueness_factor": 0.1,
                },
                "economic_rights": {
                    "royalty_model": "proportional_revenue_share",
                    "payment_mechanisms": ["direct_deposit", "crypto_wallet"],
                    "payment_thresholds": {
                        "minimum_payment": 5.00,
                        "payment_frequency": "monthly",
                    },
                    "revenue_calculation": "gross_revenue_after_platform_fees",
                },
                "source_creator_data": {
                    "original_content_789012": {
                        "creator_id": "creator_12345",
                        "creator_name": "Alex Johnson",
                        "payment_address": "0x1234...5678",
                    },
                    "original_content_345678": {
                        "creator_id": "creator_67890",
                        "creator_name": "Taylor Smith",
                        "payment_address": "0x9876...5432",
                    },
                    "original_content_901234": {
                        "creator_id": "creator_24680",
                        "creator_name": "Jordan Lee",
                        "payment_address": "0x1357...2468",
                    },
                },
                "attribution_verification": {
                    "verification_authority": "Creative Content Attribution Board",
                    "verification_method": "content_fingerprinting",
                    "verification_timestamp": (now - timedelta(hours=1)).isoformat(),
                    "verification_signature": "0x3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u",
                },
            },
            # Additional visualization-specific metadata
            "remix_details": {
                "remix_type": "multi_modal_content_assembly",
                "creation_date": (now - timedelta(days=1)).isoformat(),
                "content_description": "Educational video on climate change combining elements from multiple sources",
                "remix_tools": [
                    "content_editor_pro",
                    "attribution_calculator",
                    "license_compatibility_checker",
                ],
                "derivative_elements": {
                    "visual_elements": 0.45,  # 45% of remix is visual elements
                    "audio_elements": 0.30,  # 30% of remix is audio
                    "text_elements": 0.25,  # 25% of remix is text
                },
                "content_modifications": [
                    {
                        "source_id": "original_content_789012",
                        "modification_type": "excerpt_selection",
                        "modification_description": "Selected key sections from original documentary",
                    },
                    {
                        "source_id": "original_content_345678",
                        "modification_type": "format_conversion",
                        "modification_description": "Converted written report to narrated summary",
                    },
                    {
                        "source_id": "original_content_901234",
                        "modification_type": "visual_adaptation",
                        "modification_description": "Adapted static graphs to animated visualizations",
                    },
                ],
            },
            # Timestamp for timeline visualization
            "timestamp": now.isoformat(),
        }

        # Create and return the capsule instance
        return RemixCapsule(**capsule_data)

    except ImportError as ie:
        raise Exception(
            f"Failed to import required modules: {str(ie)}. Check that all dependencies are installed."
        )

    except TypeError as te:
        raise Exception(
            f"Invalid parameter type in remix data: {str(te)}. Check field formats match schema requirements."
        )

    except ValueError as ve:
        raise Exception(
            f"Invalid value in remix data: {str(ve)}. Check that attribution proportions sum to 1.0."
        )

    except Exception as e:
        raise Exception(
            f"Error creating sample Remix capsule: {type(e).__name__}: {str(e)}"
        )


def create_sample_implicit_consent_capsule():
    """
    Create a sample ImplicitConsent capsule with realistic data.

    This function generates a realistic sample ImplicitConsentCapsule for visualization
    and testing purposes. It includes all required fields defined in the
    ImplicitConsentCapsule schema with representative values that demonstrate
    scenarios where consent is inferred from user behavior or context rather than
    explicit opt-in actions.

    Returns:
        ImplicitConsentCapsule: A fully populated implicit consent capsule instance.

    Raises:
        Exception: If capsule creation fails due to schema validation errors
                  or missing required dependencies.
    """
    try:
        # Calculate timestamps
        now = datetime.now()
        first_interaction = now - timedelta(days=45)  # First interaction 45 days ago
        last_interaction = now - timedelta(hours=2)  # Latest interaction 2 hours ago

        # Base capsule data
        capsule_data = {
            # Required base capsule fields
            "capsule_id": "implicit_consent_demo_123456",
            "capsule_type": "ImplicitConsent",
            "agent_id": "consent-monitoring-agent-001",
            "confidence": 0.91,
            "signature": "0x8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c",
            "reasoning_trace": [
                "User behavior pattern analysis initiated",
                "Consistent engagement with relevant features detected",
                "Multiple opportunities for opt-out were provided but not taken",
                "Context and user history suggest awareness of data processing",
            ],
            # ImplicitConsent-specific fields
            "consent_context": "feature_personalization",
            "behavioral_indicators": [
                "repeated_feature_usage",
                "settings_customization",
                "continued_service_use_after_notice",
                "direct_benefit_from_processing",
            ],
            "interaction_history": [
                {
                    "timestamp": first_interaction.isoformat(),
                    "event_type": "service_signup",
                    "notice_provided": True,
                    "notice_type": "privacy_policy",
                    "user_action": "continued_use",
                },
                {
                    "timestamp": (first_interaction + timedelta(days=7)).isoformat(),
                    "event_type": "feature_introduction",
                    "notice_provided": True,
                    "notice_type": "feature_announcement",
                    "user_action": "feature_exploration",
                },
                {
                    "timestamp": (first_interaction + timedelta(days=14)).isoformat(),
                    "event_type": "preference_suggestion",
                    "notice_provided": True,
                    "notice_type": "in_app_notification",
                    "user_action": "accepted_suggestion",
                },
                {
                    "timestamp": (first_interaction + timedelta(days=30)).isoformat(),
                    "event_type": "feature_enhancement",
                    "notice_provided": True,
                    "notice_type": "email_update",
                    "user_action": "increased_engagement",
                },
                {
                    "timestamp": last_interaction.isoformat(),
                    "event_type": "content_personalization",
                    "notice_provided": True,
                    "notice_type": "inline_explanation",
                    "user_action": "positive_feedback",
                },
            ],
            "inference_justification": """
            Consent is reasonably inferred based on consistent user engagement with
            personalization features over a 45-day period. The user has received multiple
            transparent notices about data processing for personalization purposes,
            has been provided with clear opt-out options at each stage, and has demonstrated
            positive engagement with personalized content. The user's behavior shows an
            unambiguous indication of preferences through repeated interactions that
            benefit from the processing in question.
            """,
            "opt_out_opportunities": [
                {
                    "timestamp": (first_interaction + timedelta(days=1)).isoformat(),
                    "context": "welcome_email",
                    "mechanism": "preference_center_link",
                    "was_exercised": False,
                },
                {
                    "timestamp": (first_interaction + timedelta(days=10)).isoformat(),
                    "context": "account_settings",
                    "mechanism": "toggle_switch",
                    "was_exercised": False,
                },
                {
                    "timestamp": (first_interaction + timedelta(days=25)).isoformat(),
                    "context": "feature_update",
                    "mechanism": "notification_preferences",
                    "was_exercised": False,
                },
            ],
            "transparency_measures": {
                "disclosure_methods": [
                    "privacy_policy",
                    "in_product_notices",
                    "preference_center",
                    "contextual_explanations",
                ],
                "language_clarity": "high",
                "accessibility_considerations": [
                    "multiple_formats",
                    "clear_visual_cues",
                    "non_technical_language",
                ],
                "verification_method": "periodic_usage_reminders",
            },
            "legal_basis": {
                "basis_type": "legitimate_interest",
                "applicable_regulations": ["GDPR", "CCPA", "CPRA"],
                "balancing_assessment": {
                    "business_need": "service_functionality_improvement",
                    "user_impact": "positive_personalization",
                    "proportionality_analysis": "Processing is limited to what is necessary for the specific personalization features the user actively engages with",
                    "safeguards": [
                        "data_minimization",
                        "purpose_limitation",
                        "retention_limits",
                        "ongoing_opt_out",
                    ],
                },
                "documentation_reference": "LIA-PERSONALIZATION-2025-06",
            },
            # Additional metadata for visualization and context
            "consent_metadata": {
                "scope_of_processing": [
                    "usage_patterns",
                    "feature_preferences",
                    "content_interactions",
                ],
                "processing_purpose": "personalized_user_experience",
                "data_categories": [
                    "behavioral_data",
                    "preference_settings",
                    "interaction_history",
                ],
                "benefit_description": "Tailored content recommendations and interface adaptations based on usage patterns",
                "periodic_reassessment": {
                    "frequency": "P90D",  # 90 days in ISO format
                    "next_assessment_date": (now + timedelta(days=45)).isoformat(),
                    "metrics": [
                        "continued_engagement",
                        "opt_out_rate",
                        "user_satisfaction",
                    ],
                },
                "user_control_options": {
                    "granular_controls": True,
                    "control_locations": [
                        "account_settings",
                        "profile_page",
                        "footer_links",
                    ],
                    "data_portability": True,
                    "deletion_option": True,
                },
            },
            # Timestamp for timeline visualization
            "timestamp": now.isoformat(),
        }

        # Create and return the capsule instance
        return ImplicitConsentCapsule(**capsule_data)

    except ImportError as ie:
        raise Exception(
            f"Failed to import required modules: {str(ie)}. Check that all dependencies are installed."
        )

    except TypeError as te:
        raise Exception(
            f"Invalid parameter type in implicit consent data: {str(te)}. Check field formats match schema requirements."
        )

    except ValueError as ve:
        raise Exception(
            f"Invalid value in implicit consent data: {str(ve)}. Check that all fields have appropriate values."
        )

    except Exception as e:
        raise Exception(
            f"Error creating sample Implicit Consent capsule: {type(e).__name__}: {str(e)}"
        )


if __name__ == "__main__":
    main()
