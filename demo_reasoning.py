#!/usr/bin/env python3
"""
demo_reasoning.py - Demonstration script for the UATP Reasoning capabilities.

This script showcases both the local and API-based reasoning capabilities of the UATP Capsule Engine,
including:

Local functionality:
- Creating structured reasoning traces with different step types
- Validating reasoning traces for quality and compliance
- Analyzing reasoning patterns and flow
- Comparing reasoning traces between capsules
- Converting legacy string-based reasoning to structured format

REST API functionality (requires running API server):
- Validating reasoning by capsule ID
- Validating reasoning traces directly
- Analyzing reasoning structure and quality
- Comparing multiple reasoning traces
- Batch analyzing reasoning traces

Environment variables:
- UATP_API_HOST: API server host (default: localhost)
- UATP_API_PORT: API server port (default: 5000)
- UATP_DEMO_API_KEY: API key for authentication
- UATP_RUN_API_DEMOS: Set to "false" to skip API demonstrations
"""

import os
import time
from typing import List

import requests
from capsule_schema import Capsule
from reasoning.analyzer import ReasoningAnalyzer
from reasoning.trace import ReasoningStep, ReasoningTrace, StepType

# API Configuration
API_HOST = os.environ.get("UATP_API_HOST", "localhost")
API_PORT = os.environ.get("UATP_API_PORT", "5000")
# The API endpoints may not include /api/v1 prefix, adjust based on the server configuration
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"

# API key (use a valid key from your configuration)
API_KEY = os.environ.get("UATP_DEMO_API_KEY", "demo-api-key-123")


# Helper function to convert a reasoning step to API format
def _convert_step_to_api_format(step):
    """Convert a ReasoningStep to the format expected by the API."""
    return {
        "content": step.content,
        "step_type": step.step_type.name.upper(),  # API expects uppercase enum values.upper(),  # API expects uppercase enum values
        "confidence": step.confidence,
        "metadata": step.metadata,
    }


def create_sample_capsule_with_structured_reasoning() -> Capsule:
    """Create a sample capsule with a structured reasoning trace."""
    # Create a structured reasoning trace
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

    # Create a capsule with the structured reasoning trace
    capsule = Capsule(
        capsule_id="demo-structured-reasoning-001",
        capsule_type="informational",
        agent_id="demo-agent",
        timestamp="2025-07-02T21:30:00Z",
        confidence=0.9,
        reasoning_trace=trace,  # Using the structured trace directly
        signature="demo-signature",
        ethical_policy_id="standard-informational-policy",
    )

    return capsule


def create_sample_capsule_with_poor_reasoning() -> Capsule:
    """Create a sample capsule with poor reasoning structure for comparison."""
    # Create a structured reasoning trace with issues
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

    # Create a capsule with the problematic reasoning trace
    capsule = Capsule(
        capsule_id="demo-poor-reasoning-001",
        capsule_type="informational",
        agent_id="demo-agent",
        timestamp="2025-07-02T21:31:00Z",
        confidence=1.0,  # Unreasonably high confidence
        reasoning_trace=trace,
        signature="demo-signature",
        ethical_policy_id="standard-informational-policy",
    )

    return capsule


def demonstrate_reasoning_validation(capsules: List[Capsule]) -> None:
    """Demonstrate reasoning validation capabilities."""
    print("\n=== REASONING VALIDATION DEMONSTRATION ===")

    for i, capsule in enumerate(capsules):
        print(f"\nCapsule {i+1}: {capsule.capsule_id}")

        # Validate the reasoning
        validation_result = capsule.validate_reasoning()

        # Print validation results
        print(f"Validation Score: {validation_result['score']:.1f}/100")
        print(f"Valid: {validation_result['is_valid']}")

        if validation_result["issues"]:
            print("\nIssues:")
            for issue in validation_result["issues"]:
                print(f"- [{issue['severity'].upper()}] {issue['message']}")

        if validation_result["suggestions"]:
            print("\nSuggestions:")
            for suggestion in validation_result["suggestions"]:
                print(f"- {suggestion}")


def demonstrate_reasoning_analysis(capsules: List[Capsule]) -> None:
    """Demonstrate reasoning analysis capabilities."""
    print("\n=== REASONING ANALYSIS DEMONSTRATION ===")

    for i, capsule in enumerate(capsules):
        print(f"\nCapsule {i+1}: {capsule.capsule_id}")

        # Analyze the reasoning
        analysis = capsule.analyze_reasoning()

        # Print analysis results
        print(f"Step Count: {analysis['step_count']}")
        print(f"Average Confidence: {analysis['average_confidence']:.2f}")

        print("\nStep Type Distribution:")
        for step_type, percentage in analysis["type_distribution"].items():
            print(f"- {step_type}: {percentage*100:.1f}%")

        print("\nReasoning Patterns:")
        for pattern in analysis["patterns"]:
            print(f"- {pattern}")

        print("\nFlow Analysis:")
        for key, value in analysis["flow"].items():
            print(f"- {key}: {value}")


def demonstrate_trace_comparison(capsule1: Capsule, capsule2: Capsule) -> None:
    """Demonstrate comparison between two reasoning traces."""
    print("\n=== REASONING COMPARISON DEMONSTRATION ===")

    # Get structured traces
    trace1 = capsule1.get_reasoning_trace_as_structured()
    trace2 = capsule2.get_reasoning_trace_as_structured()

    # Compare traces
    comparison = ReasoningAnalyzer.compare_traces(trace1, trace2)

    # Print comparison results
    print(f"\nComparing {capsule1.capsule_id} with {capsule2.capsule_id}:")
    print(f"Step Count Difference: {comparison['step_count_diff']}")
    print(f"Confidence Difference: {comparison['confidence_diff']:.2f}")

    print("\nStep Type Distribution Differences:")
    for step_type, diff in comparison["type_distribution_diffs"].items():
        direction = "higher" if diff > 0 else "lower"
        print(f"- {step_type}: {abs(diff)*100:.1f}% {direction}")

    if comparison["common_patterns"]:
        print("\nCommon Patterns:")
        for pattern in comparison["common_patterns"]:
            print(f"- {pattern}")

    print("\nUnique Patterns:")
    print("Capsule 1:")
    for pattern in comparison["unique_patterns"]["trace1"]:
        print(f"- {pattern}")
    print("Capsule 2:")
    for pattern in comparison["unique_patterns"]["trace2"]:
        print(f"- {pattern}")


def demonstrate_multi_trace_analysis(capsules: List[Capsule]) -> None:
    """Demonstrate analysis across multiple reasoning traces."""
    print("\n=== MULTI-TRACE ANALYSIS DEMONSTRATION ===")

    # Get all traces
    traces = [capsule.get_reasoning_trace_as_structured() for capsule in capsules]

    # Analyze multiple traces
    analysis = ReasoningAnalyzer.analyze_multiple_traces(traces)

    # Print analysis results
    print(f"\nAnalyzed {analysis['trace_count']} traces")

    print("\nStep Statistics:")
    for key, value in analysis["step_statistics"].items():
        print(f"- {key}: {value}")

    print("\nConfidence Statistics:")
    for key, value in analysis["confidence_statistics"].items():
        print(f"- {key}: {value:.2f}")

    print("\nAggregate Step Type Distribution:")
    for step_type, percentage in analysis["aggregate_type_distribution"].items():
        print(f"- {step_type}: {percentage*100:.1f}%")

    print("\nCommon Patterns:")
    for pattern_info in analysis["common_patterns"]:
        print(f"- {pattern_info['pattern']}: {pattern_info['frequency']*100:.1f}%")


def demonstrate_backward_compatibility() -> None:
    """Demonstrate backward compatibility with string-based reasoning traces."""
    print("\n=== BACKWARD COMPATIBILITY DEMONSTRATION ===")

    # Create a capsule with traditional string-based reasoning
    legacy_capsule = Capsule(
        capsule_id="legacy-reasoning-001",
        capsule_type="informational",
        agent_id="legacy-agent",
        timestamp="2025-07-02T21:32:00Z",
        confidence=0.85,
        reasoning_trace=[
            "User asked about climate change",
            "I should provide scientific information",
            "IPCC reports indicate global warming",
            "Therefore I will explain climate impacts",
        ],
        signature="legacy-signature",
    )

    print("\nOriginal string-based reasoning trace:")
    for i, step in enumerate(legacy_capsule.reasoning_trace):
        print(f"{i+1}. {step}")

    # Convert to structured format
    structured_trace = legacy_capsule.get_reasoning_trace_as_structured()

    print("\nAutomatically converted to structured format:")
    for i, step in enumerate(structured_trace):
        print(f"{i+1}. [{step.step_type.value}] {step.content}")

    # Validate the converted trace
    validation_result = legacy_capsule.validate_reasoning()
    print(f"\nValidation Score: {validation_result['score']:.1f}/100")


def demonstrate_api_validate_by_capsule_id(capsule: Capsule) -> None:
    """Demonstrate validating reasoning via API using a capsule ID."""
    print("\n=== API: VALIDATE REASONING BY CAPSULE ID ===")
    print(
        "Note: This demonstration is skipped because the demo capsules aren't in the server's chain."
    )
    print("See the direct trace validation demonstration below instead.")

    # In a production environment, you would use this approach with real capsule IDs
    # that exist in the server's capsule chain.
    #
    # # Prepare API request headers
    # headers = {
    #     "X-API-Key": API_KEY,
    #     "Content-Type": "application/json"
    # }
    #
    # # Prepare request data
    # data = {"capsule_id": capsule.capsule_id}
    #
    # try:
    #     # Make API request
    #     print(f"Sending request to validate capsule ID: {capsule.capsule_id}")
    #     response = requests.post(
    #         f"{API_BASE_URL}/reasoning/validate",
    #         headers=headers,
    #         json=data
    #     )
    #
    #     # Process response
    #     if response.status_code == 200:
    #         result = response.json()
    #         validation_result = result.get('validation_result', {})
    #         print(f"\nValidation Result for {capsule.capsule_id}:")
    #         print(f"Score: {validation_result.get('score', 0)}/100")
    #         print(f"Valid: {validation_result.get('valid', False)}")
    #
    #         if 'issues' in validation_result and validation_result['issues']:
    #             print("\nIssues:")
    #             for issue in validation_result['issues']:
    #                 print(f"- {issue}")
    #
    #         if 'suggestions' in validation_result and validation_result['suggestions']:
    #             print("\nSuggestions:")
    #             for suggestion in validation_result['suggestions']:
    #                 print(f"- {suggestion}")
    #     else:
    #         print(f"Error: {response.status_code} - {response.text}")
    # except Exception as e:
    #     print(f"API request failed: {str(e)}")


def demonstrate_api_validate_direct_trace(trace: ReasoningTrace) -> None:
    """Demonstrate validating reasoning via API using a direct reasoning trace."""
    print("\n=== API: VALIDATE REASONING TRACE DIRECTLY ===")

    # Setup API request headers
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

    # Convert trace to API format
    steps_data = []
    for step in trace.steps:
        steps_data.append(
            {
                "content": step.content,
                "step_type": step.step_type.name.upper(),  # API expects uppercase enum values
                "confidence": step.confidence,
                "metadata": step.metadata,
            }
        )

    # Prepare request data
    data = {"reasoning_trace": {"steps": steps_data}}

    try:
        # Make API request
        print("Sending request to validate reasoning trace directly")
        response = requests.post(
            f"{API_BASE_URL}/reasoning/validate", headers=headers, json=data
        )

        # Process response
        if response.status_code == 200:
            result = response.json()
            print("\nValidation Result:")
            print(f"Valid: {result['validation_result']['is_valid']}")
            print(f"Score: {result['validation_result']['score']:.1f}/100")

            if result["validation_result"]["issues"]:
                print("\nIssues:")
                for issue in result["validation_result"]["issues"]:
                    print(f"- {issue['message']} ({issue['severity']})")

            if result["validation_result"]["suggestions"]:
                print("\nSuggestions:")
                for suggestion in result["validation_result"]["suggestions"]:
                    print(f"- {suggestion}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"API request failed: {str(e)}")


def demonstrate_api_analyze_reasoning(trace: ReasoningTrace) -> None:
    """Demonstrate analyzing reasoning via API."""
    print("\n=== API: ANALYZE REASONING TRACE ===")

    # Setup API request headers
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

    # Convert trace to API format
    steps_data = []
    for step in trace.steps:
        steps_data.append(
            {
                "content": step.content,
                "step_type": step.step_type.name.upper(),  # API expects uppercase enum values
                "confidence": step.confidence,
                "metadata": step.metadata,
            }
        )

    # Prepare request data
    data = {"reasoning_trace": {"steps": steps_data}}

    try:
        # Make API request
        print("Sending request to analyze reasoning trace")
        response = requests.post(
            f"{API_BASE_URL}/reasoning/analyze", headers=headers, json=data
        )

        # Process response
        if response.status_code == 200:
            result = response.json()
            analysis = result["analysis"]
            print("\nAnalysis Result:")
            print(f"Step Count: {analysis['step_count']}")
            print(f"Average Confidence: {analysis['average_confidence']:.2f}")

            print("\nStep Type Distribution:")
            for step_type, percentage in analysis["type_distribution"].items():
                print(f"- {step_type}: {percentage*100:.1f}%")

            print(f"\nHas Conclusion: {analysis['has_conclusion']}")

            if analysis["patterns"]:
                print("\nDetected Patterns:")
                for pattern in analysis["patterns"]:
                    print(f"- {pattern}")

            print("\nFlow Quality Assessment:")
            for aspect, rating in analysis["flow"].items():
                print(f"- {aspect}: {rating}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"API request failed: {str(e)}")


def demonstrate_api_compare_reasoning(
    trace1: ReasoningTrace, trace2: ReasoningTrace
) -> None:
    """Demonstrate comparing reasoning traces via API."""
    print("\n=== API: COMPARE REASONING TRACES ===")

    # Setup API request headers
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

    # Convert trace1 to API format
    steps_data1 = []
    for step in trace1.steps:
        steps_data1.append(
            {
                "content": step.content,
                "step_type": step.step_type.name.upper(),  # API expects uppercase enum values
                "confidence": step.confidence,
                "metadata": step.metadata,
            }
        )

    # Convert trace2 to API format
    steps_data2 = []
    for step in trace2.steps:
        steps_data2.append(
            {
                "content": step.content,
                "step_type": step.step_type.name.upper(),  # API expects uppercase enum values
                "confidence": step.confidence,
                "metadata": step.metadata,
            }
        )

    # Prepare request data
    data = {
        "reasoning_trace1": {"steps": steps_data1},
        "reasoning_trace2": {"steps": steps_data2},
    }

    try:
        # Make API request
        print("Sending request to compare reasoning traces")
        response = requests.post(
            f"{API_BASE_URL}/reasoning/compare", headers=headers, json=data
        )

        # Process response
        if response.status_code == 200:
            result = response.json()
            comparison = result["comparison"]
            print("\nComparison Result:")

            print(f"Step Count Difference: {comparison['step_count_diff']}")
            print(f"Confidence Difference: {comparison['confidence_diff']:.2f}")

            print("\nStep Type Distribution Differences:")
            for step_type, diff in comparison["type_distribution_diffs"].items():
                direction = "higher" if diff > 0 else "lower"
                print(f"- {step_type}: {abs(diff)*100:.1f}% {direction}")

            if comparison["common_patterns"]:
                print("\nCommon Patterns:")
                for pattern in comparison["common_patterns"]:
                    print(f"- {pattern}")

            print("\nUnique Patterns:")
            print("Trace 1:")
            for pattern in comparison["unique_patterns"]["trace1"]:
                print(f"- {pattern}")
            print("Trace 2:")
            for pattern in comparison["unique_patterns"]["trace2"]:
                print(f"- {pattern}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"API request failed: {str(e)}")


def demonstrate_api_analyze_batch(traces: List[ReasoningTrace]) -> None:
    """Demonstrate batch analysis of reasoning traces via API."""
    print("\n=== API: ANALYZE BATCH REASONING ===")

    # Setup API request headers
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

    # Convert traces to API format
    traces_data = []
    for trace in traces:
        steps_data = []
        for step in trace.steps:
            steps_data.append(
                {
                    "content": step.content,
                    "step_type": step.step_type.name.upper(),  # API expects uppercase enum values
                    "confidence": step.confidence,
                    "metadata": step.metadata,
                }
            )
        traces_data.append({"steps": steps_data})

    # Prepare request data
    data = {"reasoning_traces": traces_data}

    try:
        # Make API request
        print("Sending request to analyze batch reasoning traces")
        response = requests.post(
            f"{API_BASE_URL}/reasoning/analyze-batch", headers=headers, json=data
        )

        # Process response
        if response.status_code == 200:
            result = response.json()
            analysis = result["analysis"]
            print("\nBatch Analysis Result:")
            print(f"Analyzed {analysis['trace_count']} traces")

            print("\nStep Statistics:")
            for key, value in analysis["step_statistics"].items():
                print(f"- {key}: {value}")

            print("\nConfidence Statistics:")
            for key, value in analysis["confidence_statistics"].items():
                print(f"- {key}: {value:.2f}")

            print("\nAggregate Step Type Distribution:")
            for step_type, percentage in analysis[
                "aggregate_type_distribution"
            ].items():
                print(f"- {step_type}: {percentage*100:.1f}%")

            print("\nCommon Patterns:")
            for pattern_info in analysis["common_patterns"]:
                print(
                    f"- {pattern_info['pattern']}: {pattern_info['frequency']*100:.1f}%"
                )
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"API request failed: {str(e)}")


def demonstrate_api_functionality(good_capsule: Capsule, poor_capsule: Capsule) -> None:
    """Run all API demonstrations."""
    print("\n=== REASONING API DEMONSTRATIONS ===")
    print("Note: Ensure the UATP API server is running before running these demos.")
    print(f"API Base URL: {API_BASE_URL}")

    # Get traces from capsules
    good_trace = good_capsule.get_reasoning_trace_as_structured()
    poor_trace = poor_capsule.get_reasoning_trace_as_structured()
    traces = [good_trace, poor_trace]

    # Run API demonstrations with delays to prevent rate limiting
    demonstrate_api_validate_by_capsule_id(good_capsule)
    time.sleep(1)

    demonstrate_api_validate_direct_trace(good_trace)
    time.sleep(1)

    demonstrate_api_analyze_reasoning(good_trace)
    time.sleep(1)

    demonstrate_api_compare_reasoning(good_trace, poor_trace)
    time.sleep(1)

    demonstrate_api_analyze_batch(traces)

    print("\nAPI demonstrations completed!")


def main():
    """Main demonstration function."""
    print("=== UATP ENHANCED REASONING FIDELITY DEMONSTRATION ===")

    # Create sample capsules
    good_capsule = create_sample_capsule_with_structured_reasoning()
    poor_capsule = create_sample_capsule_with_poor_reasoning()
    capsules = [good_capsule, poor_capsule]

    # Run local demonstrations
    demonstrate_reasoning_validation(capsules)
    demonstrate_reasoning_analysis(capsules)
    demonstrate_trace_comparison(good_capsule, poor_capsule)
    demonstrate_multi_trace_analysis(capsules)
    demonstrate_backward_compatibility()

    # Add a separator between local and API demos
    print("\n" + "-" * 50)

    # Check if API demos should be run (can be controlled by environment variable)
    run_api_demos = os.environ.get("UATP_RUN_API_DEMOS", "true").lower() == "true"

    if run_api_demos:
        demonstrate_api_functionality(good_capsule, poor_capsule)
    else:
        print("\nSkipping API demonstrations. Set UATP_RUN_API_DEMOS=true to run them.")

    print("\nDemonstration complete!")


if __name__ == "__main__":
    main()
