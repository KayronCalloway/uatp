"""API client for reasoning validation and analysis services.

This module provides functions to interact with the reasoning API services
for validation, analysis, comparison and batch analysis of reasoning traces.
"""

import json

import requests
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential

# Default API configuration
DEFAULT_API_BASE_URL = "https://reasoning-api.example.com/v1"
DEFAULT_API_KEY = ""


def get_api_config():
    """Get API configuration from session state or default values."""
    return {
        "base_url": st.session_state.get("api_base_url", DEFAULT_API_BASE_URL),
        "api_key": st.session_state.get("api_key", DEFAULT_API_KEY),
    }


def normalize_steps(reasoning_trace):
    """Normalize reasoning steps to match API expectations.

    Converts reasoning trace steps to the format expected by the API.
    """
    if isinstance(reasoning_trace, list):
        # Convert list of strings to structured format
        normalized_steps = []
        for i, step in enumerate(reasoning_trace):
            normalized_steps.append(
                {
                    "step_id": str(i + 1),
                    "step_type": "OBSERVATION",  # Default step type, using uppercase enum as expected
                    "content": step,
                }
            )
        return normalized_steps
    elif isinstance(reasoning_trace, dict):
        # Already in structured format, ensure step_type is uppercase
        for step in reasoning_trace.get("steps", []):
            if "step_type" in step:
                step["step_type"] = step["step_type"].upper()
        return reasoning_trace.get("steps", [])
    else:
        return []


# For backward compatibility
normalize_reasoning_steps = normalize_steps


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def make_api_request(endpoint, data, method="POST"):
    """Make an API request with retry logic.

    Args:
        endpoint: API endpoint path
        data: Request payload
        method: HTTP method (default: POST)

    Returns:
        API response as dict
    """
    config = get_api_config()
    base_url = config["base_url"].rstrip("/")
    url = f"{base_url}/{endpoint.lstrip('/')}"

    headers = {"Content-Type": "application/json"}

    if config["api_key"]:
        headers["Authorization"] = f"Bearer {config['api_key']}"

    response = requests.request(
        method=method, url=url, headers=headers, data=json.dumps(data)
    )

    # Raise exception on error
    response.raise_for_status()

    return response.json()


def validate_reasoning_trace(capsule):
    """Validate a reasoning trace using the API.

    Args:
        capsule: Capsule containing the reasoning trace to validate

    Returns:
        Validation results as dict
    """
    if not hasattr(capsule, "reasoning_trace") or not capsule.reasoning_trace:
        return {"valid": False, "errors": ["No reasoning trace found"]}

    # Show loading state
    with st.spinner("Validating reasoning trace via API..."):
        try:
            # Prepare payload
            payload = {
                "trace": {"steps": normalize_reasoning_steps(capsule.reasoning_trace)}
            }

            # Make API request
            result = make_api_request("reasoning/validate", payload)
            return result
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return {"valid": False, "errors": [str(e)]}


def analyze_reasoning_trace(capsule):
    """Analyze a reasoning trace using the API.

    Args:
        capsule: Capsule containing the reasoning trace to analyze

    Returns:
        Analysis results as dict
    """
    if not hasattr(capsule, "reasoning_trace") or not capsule.reasoning_trace:
        return {"error": "No reasoning trace found"}

    # Show loading state
    with st.spinner("Analyzing reasoning trace via API..."):
        try:
            # Prepare payload
            payload = {
                "trace": {"steps": normalize_reasoning_steps(capsule.reasoning_trace)}
            }

            # Make API request
            result = make_api_request("reasoning/analyze", payload)
            return result
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return {"error": str(e)}


def compare_reasoning_traces(capsule1, capsule2):
    """Compare two reasoning traces using the API.

    Args:
        capsule1: First capsule containing a reasoning trace
        capsule2: Second capsule containing a reasoning trace

    Returns:
        Comparison results as dict
    """
    if not hasattr(capsule1, "reasoning_trace") or not capsule1.reasoning_trace:
        return {"error": "No reasoning trace found in first capsule"}

    if not hasattr(capsule2, "reasoning_trace") or not capsule2.reasoning_trace:
        return {"error": "No reasoning trace found in second capsule"}

    # Show loading state
    with st.spinner("Comparing reasoning traces via API..."):
        try:
            # Prepare payload
            payload = {
                "trace1": {
                    "steps": normalize_reasoning_steps(capsule1.reasoning_trace)
                },
                "trace2": {
                    "steps": normalize_reasoning_steps(capsule2.reasoning_trace)
                },
            }

            # Make API request
            result = make_api_request("reasoning/compare", payload)
            return result
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return {"error": str(e)}


def batch_analyze_reasoning_traces(capsules):
    """Batch analyze multiple reasoning traces using the API.

    Args:
        capsules: List of capsules containing reasoning traces

    Returns:
        Batch analysis results as dict
    """
    if not capsules:
        return {"error": "No capsules provided"}

    # Show loading state
    with st.spinner("Performing batch analysis of reasoning traces..."):
        try:
            # Prepare payload
            traces = []

            for capsule in capsules:
                if hasattr(capsule, "reasoning_trace") and capsule.reasoning_trace:
                    traces.append(
                        {
                            "capsule_id": capsule.capsule_id,
                            "steps": normalize_reasoning_steps(capsule.reasoning_trace),
                        }
                    )

            if not traces:
                return {"error": "No valid reasoning traces found"}

            payload = {"traces": traces}

            # Make API request
            result = make_api_request("reasoning/batch-analyze", payload)
            return result
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return {"error": str(e)}


def format_api_results(results):
    """Format API results for display in the UI.

    Args:
        results: Results from API call

    Returns:
        Formatted results suitable for display
    """
    if not results or isinstance(results, str):
        return {"formatted": "No results to display"}

    if "error" in results:
        return {"error": results["error"], "formatted": f"Error: {results['error']}"}

    # Format based on result type
    if "valid" in results:
        # Validation results
        if results["valid"]:
            return {"formatted": "✅ Reasoning trace is valid", "details": results}
        else:
            errors = "\n".join(
                [
                    f"• {error}"
                    for error in results.get("errors", ["Unknown validation error"])
                ]
            )
            return {"formatted": f"❌ Validation failed:\n{errors}", "details": results}

    # Analysis results
    if "analysis" in results:
        summary = []
        analysis = results["analysis"]

        if "coherence_score" in analysis:
            summary.append(f"Coherence: {analysis['coherence_score']:.2f}/10")

        if "step_count" in analysis:
            summary.append(f"Steps: {analysis['step_count']}")

        if "patterns" in analysis and analysis["patterns"]:
            patterns = ", ".join(analysis["patterns"])
            summary.append(f"Patterns: {patterns}")

        return {"formatted": "\n".join(summary), "details": results}

    # Comparison results
    if "comparison" in results:
        comp = results["comparison"]
        summary = []

        if "similarity_score" in comp:
            summary.append(f"Similarity: {comp['similarity_score']:.2f}/10")

        if "differences" in comp and comp["differences"]:
            summary.append(f"Differences: {len(comp['differences'])}")

        return {"formatted": "\n".join(summary), "details": results}

    # Batch analysis
    if "batch_results" in results:
        count = len(results["batch_results"])
        return {"formatted": f"Analyzed {count} traces", "details": results}

    # Generic fallback
    return {"formatted": "Results available in details tab", "details": results}
