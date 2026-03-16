#!/usr/bin/env python3
"""
Test script for the Reasoning Analysis API endpoints.

This script demonstrates how to use the new reasoning analysis API endpoints
to validate, analyze, and compare reasoning traces.
"""

import json
import logging
import os
import pprint
import sys
import time
from typing import Any, Dict, Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("reasoning-api-tests")

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from reasoning.trace import ReasoningStep, ReasoningTrace, StepType

# Configuration
API_BASE_URL = "http://localhost:5006"  # Update if using a different port
API_KEY = "test-key"  # Replace with your actual API key
HEADERS = {"Content-Type": "application/json", "X-API-Key": API_KEY}


def create_sample_structured_reasoning():
    """Create a sample structured reasoning trace for testing."""
    trace = ReasoningTrace()

    # Add reasoning steps with different types
    trace.add_step(
        ReasoningStep(
            content="User requested information about climate change impacts",
            step_type=StepType.OBSERVATION,
            confidence=1.0,
        )
    )

    trace.add_step(
        ReasoningStep(
            content="Topic is potentially sensitive and requires accurate information",
            step_type=StepType.OBSERVATION,
            confidence=1.0,
        )
    )

    trace.add_step(
        ReasoningStep(
            content="Scientific consensus indicates global temperatures are rising",
            step_type=StepType.EVIDENCE,
            confidence=0.95,
            metadata={"source": "IPCC Report 2021"},
        )
    )

    trace.add_step(
        ReasoningStep(
            content="Rising temperatures will likely lead to sea level rise and extreme weather",
            step_type=StepType.INFERENCE,
            confidence=0.85,
        )
    )

    trace.add_step(
        ReasoningStep(
            content="I should provide balanced information from credible sources",
            step_type=StepType.REFLECTION,
            confidence=0.9,
        )
    )

    trace.add_step(
        ReasoningStep(
            content="Climate change impacts include sea level rise, extreme weather, and ecosystem disruption",
            step_type=StepType.CONCLUSION,
            confidence=0.9,
        )
    )

    return trace


def create_sample_poor_reasoning():
    """Create a sample poor reasoning trace for comparison."""
    trace = ReasoningTrace()

    # Add reasoning steps with problematic structure
    trace.add_step(
        ReasoningStep(
            content="User asked about climate change",
            step_type=StepType.OBSERVATION,
            confidence=1.0,
        )
    )

    # Jump straight to conclusion without evidence
    trace.add_step(
        ReasoningStep(
            content="Climate change is causing problems",
            step_type=StepType.CONCLUSION,
            confidence=1.0,  # Unreasonably high confidence
        )
    )

    return trace


def api_request(
    endpoint, method="GET", data=None, expected_status=200
) -> Optional[Dict[str, Any]]:
    """Make an API request with proper error handling and rate limit awareness."""
    url = f"{API_BASE_URL}/{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS)
        elif method == "POST":
            response = requests.post(url, headers=HEADERS, json=data)
        else:
            logger.error(f"Unsupported HTTP method: {method}")
            return None

        # Handle rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "5"))
            logger.warning(f"Rate limited. Waiting {retry_after} seconds before retry.")
            time.sleep(retry_after)
            return api_request(
                endpoint, method, data, expected_status
            )  # Retry after waiting

        # Check for expected status
        if response.status_code != expected_status:
            logger.error(f"API Error: {response.status_code} - {response.text}")
            return None

        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return None


def get_test_capsule_id() -> Optional[str]:
    """Get a valid capsule ID for testing."""
    data = api_request("capsules")
    if not data:
        logger.error("Failed to fetch capsules")
        return None

    # Handle both formats: list of capsules or dict with 'capsules' key
    if isinstance(data, dict) and "capsules" in data:
        capsules = data["capsules"]
    elif isinstance(data, list):
        capsules = data
    else:
        logger.error("Unexpected response format when fetching capsules")
        return None

    if not capsules:
        logger.error("No capsules found in the system")
        return None

    # Use the first capsule ID for testing
    if isinstance(capsules[0], dict) and "capsule_id" in capsules[0]:
        return capsules[0]["capsule_id"]
    else:
        logger.error("Unexpected capsule format")
        return None


def test_validate_reasoning_by_capsule_id():
    print("\n=== TEST: Validate Reasoning by Capsule ID ===")

    # Get a valid capsule ID for testing
    capsule_id = get_test_capsule_id()
    if not capsule_id:
        print("Cannot proceed with testing: no valid capsule ID found")
        return
    print(f"Using capsule ID: {capsule_id}")

    # Call the validate endpoint
    data = {"capsule_id": capsule_id}
    result = api_request("reasoning/validate", "POST", data)

    if not result:
        print("Error validating reasoning by capsule ID")
        return

    print("\nValidation Result:")
    pprint.pprint(result)


def test_validate_reasoning_directly():
    """Test validating a reasoning trace directly."""
    print("\n=== TEST: Validate Reasoning Trace Directly ===")

    # Create a sample reasoning trace
    trace = create_sample_structured_reasoning()

    # Create a sample reasoning trace
    trace = create_sample_structured_reasoning()

    # Prepare data for API call
    steps_data = []
    for step in trace.steps:
        steps_data.append(
            {
                "content": step.content,
                "step_type": step.step_type.name,
                "confidence": step.confidence,
                "metadata": step.metadata,
            }
        )

    data = {"reasoning_trace": {"steps": steps_data}}

    result = api_request("reasoning/validate", "POST", data)

    if not result:
        print("Error validating reasoning directly")
        return

    print("\nValidation Result:")
    pprint.pprint(result)


def test_analyze_reasoning():
    """Test analyzing a reasoning trace."""
    print("\n=== TEST: Analyze Reasoning Trace ===")

    # Wait to avoid rate limiting
    time.sleep(2)
    trace = create_sample_structured_reasoning()

    # Prepare data for API call
    steps_data = []
    for step in trace.steps:
        steps_data.append(
            {
                "content": step.content,
                "step_type": step.step_type.name,
                "confidence": step.confidence,
                "metadata": step.metadata,
            }
        )

    data = {"reasoning_trace": {"steps": steps_data}}

    result = api_request("reasoning/analyze", "POST", data)

    if not result:
        print("Error analyzing reasoning trace")
        return

    print("\nAnalysis Result:")
    pprint.pprint(result)


def test_compare_reasoning():
    """Test comparing two reasoning traces."""
    print("\n=== TEST: Compare Reasoning Traces ===")

    # Wait to avoid rate limiting
    time.sleep(2)

    # Create sample reasoning traces
    trace1 = create_sample_structured_reasoning()
    trace2 = create_sample_poor_reasoning()  # Returns a ReasoningTrace object

    # Prepare data for API call - convert ReasoningStep objects to dictionaries
    steps_data1 = []
    for step in trace1.steps:
        steps_data1.append(
            {
                "content": step.content,
                "step_type": step.step_type.name,
                "confidence": step.confidence,
                "metadata": step.metadata,
            }
        )

    # Convert trace2's ReasoningStep objects to dictionaries as well
    steps_data2 = []
    for step in trace2.steps:
        steps_data2.append(
            {
                "content": step.content,
                "step_type": step.step_type.name,
                "confidence": step.confidence,
                "metadata": step.metadata,
            }
        )

    data = {
        "reasoning_trace1": {"steps": steps_data1},
        "reasoning_trace2": {"steps": steps_data2},
    }

    result = api_request("reasoning/compare", "POST", data)

    if not result:
        print("Error comparing reasoning traces")
        return

    print("\nComparison Result:")
    pprint.pprint(result)


def test_analyze_batch():
    """Test analyzing multiple reasoning traces in batch."""
    print("\n=== TEST: Analyze Batch Reasoning ===")

    # Wait to avoid rate limiting
    time.sleep(2)

    # Create sample reasoning traces
    trace1 = create_sample_structured_reasoning()
    trace2 = create_sample_poor_reasoning()  # Returns a ReasoningTrace object

    # Prepare data for API call - convert ReasoningStep objects to dictionaries
    steps_data1 = []
    for step in trace1.steps:
        steps_data1.append(
            {
                "content": step.content,
                "step_type": step.step_type.name,
                "confidence": step.confidence,
                "metadata": step.metadata,
            }
        )

    # Convert trace2's ReasoningStep objects to dictionaries as well
    steps_data2 = []
    for step in trace2.steps:
        steps_data2.append(
            {
                "content": step.content,
                "step_type": step.step_type.name,
                "confidence": step.confidence,
                "metadata": step.metadata,
            }
        )

    data = {"reasoning_traces": [{"steps": steps_data1}, {"steps": steps_data2}]}

    result = api_request("reasoning/analyze-batch", "POST", data)

    if not result:
        print("Error analyzing batch reasoning")
        return

    print("\nBatch Analysis Result:")
    pprint.pprint(result)


def run_all_tests():
    """Run all the API tests."""
    print("=== REASONING API TEST SUITE ===")

    test_validate_reasoning_by_capsule_id()
    test_validate_reasoning_directly()
    test_analyze_reasoning()
    test_compare_reasoning()
    test_analyze_batch()

    print("\nAll tests completed!")


if __name__ == "__main__":
    run_all_tests()
