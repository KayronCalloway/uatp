#!/usr/bin/env python3
"""
Create a demonstration capsule with per-step confidence tracking.

This demonstrates the new per-step confidence feature with:
- Varying confidence levels across steps
- Uncertainty source tracking
- Measurements and alternatives considered
- Confidence methodology explanation
"""

from datetime import datetime, timezone
from src.capsule_schema import (
    ReasoningTraceCapsule,
    ReasoningTracePayload,
    ReasoningStep,
    ConfidenceMethodology,
    CapsuleStatus,
    Verification,
)
import json


def create_performance_analysis_capsule():
    """Create a capsule analyzing system performance with per-step confidence."""

    # Step 1: Factual observation (high confidence)
    step1 = ReasoningStep(
        step_id=1,
        operation="measurement",
        reasoning="Measured current system latency at 45ms average over 1000 requests",
        confidence=0.95,
        confidence_basis="measured",
        measurements={
            "avg_latency_ms": 45.2,
            "p50_ms": 42.0,
            "p95_ms": 78.5,
            "p99_ms": 125.0,
            "sample_size": 1000,
        },
    )

    # Step 2: Performance estimation (medium confidence with uncertainty)
    step2 = ReasoningStep(
        step_id=2,
        operation="estimation",
        reasoning="Estimated system can handle 2000 RPS with caching enabled",
        confidence=0.72,
        confidence_basis="estimated",
        uncertainty_sources=[
            "Cache hit rate variability (65-85%)",
            "Database query performance under load",
            "Network latency fluctuations",
        ],
        measurements={
            "current_rps": 1000,
            "cache_hit_rate": 0.75,
            "db_query_time_ms": 8.5,
        },
        alternatives_considered=[
            "Load balancing across 3 servers (est. 2500 RPS)",
            "Database read replicas (est. 2200 RPS)",
            "Query optimization only (est. 1500 RPS)",
        ],
        depends_on_steps=[1],
    )

    # Step 3: Architecture decision (lower confidence)
    step3 = ReasoningStep(
        step_id=3,
        operation="decision",
        reasoning="Recommend implementing Redis caching layer as the primary optimization",
        confidence=0.68,
        confidence_basis="expert judgment",
        uncertainty_sources=[
            "Redis memory requirements unclear",
            "Cache invalidation strategy complexity",
            "Team familiarity with Redis operations",
        ],
        alternatives_considered=[
            "In-memory application cache (simpler but less effective)",
            "CDN caching (effective but limited to static content)",
            "Database query optimization (lower performance gain)",
        ],
        measurements={
            "estimated_memory_gb": 4.0,
            "estimated_setup_hours": 16,
            "estimated_performance_gain": 1.8,
        },
        depends_on_steps=[1, 2],
    )

    # Step 4: Security assessment (medium-high confidence)
    step4 = ReasoningStep(
        step_id=4,
        operation="security_assessment",
        reasoning="Redis caching poses minimal security risk with proper network isolation",
        confidence=0.82,
        confidence_basis="security audit",
        uncertainty_sources=[
            "Potential data leakage if cache keys predictable",
            "Redis AUTH strength depends on password complexity",
        ],
        measurements={
            "security_controls": 3,
            "compliance_requirements": [
                "network_isolation",
                "encryption_at_rest",
                "access_logs",
            ],
        },
        alternatives_considered=[
            "Client-side caching (higher security, lower performance)",
            "Database-level caching (lower risk, lower gain)",
        ],
        depends_on_steps=[3],
    )

    # Step 5: Final recommendation (confidence from critical path)
    step5 = ReasoningStep(
        step_id=5,
        operation="recommendation",
        reasoning="Implement Redis caching with network isolation and monitoring. Expected: 2000 RPS capacity with acceptable security posture.",
        confidence=0.68,  # Limited by step 3 (weakest critical link)
        confidence_basis="weakest_critical_link",
        depends_on_steps=[2, 3, 4],
        attribution_sources=[
            "system_architect",
            "security_team",
            "performance_engineer",
        ],
    )

    # Define confidence methodology
    methodology = ConfidenceMethodology(
        method="weakest_critical_link",
        critical_path_steps=[2, 3, 4, 5],
        explanation="Overall confidence limited by architectural decision (step 3) at 68%, which represents the highest uncertainty in the critical path. Steps 2, 4, and 5 depend on this decision.",
    )

    # Create reasoning trace
    trace = ReasoningTracePayload(
        reasoning_steps=[step1, step2, step3, step4, step5],
        total_confidence=0.68,  # From weakest critical link
        confidence_methodology=methodology,
    )

    # Create capsule (format: caps_YYYY_MM_DD_16hexchars)
    import secrets

    capsule_id = f"caps_2025_01_19_{secrets.token_hex(8)}"

    capsule = ReasoningTraceCapsule(
        capsule_id=capsule_id,
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        capsule_type="reasoning_trace",
        status=CapsuleStatus.ACTIVE,
        reasoning_trace=trace,
        verification=Verification(
            signer="performance_analysis_system",
            verify_key="demo_key_" + "0" * 56,
            hash="0" * 64,  # Just hex, no prefix
            signature="ed25519:" + "0" * 128,
            merkle_root="sha256:" + "0" * 64,
        ),
    )

    return capsule


def main():
    """Create and save the demonstration capsule."""

    print("🔧 Creating demonstration capsule with per-step confidence tracking...")
    print()

    capsule = create_performance_analysis_capsule()

    # Display summary
    print("✅ Created capsule:", capsule.capsule_id)
    print()
    print("📊 Reasoning Trace Summary:")
    print(f"   Total steps: {len(capsule.reasoning_trace.reasoning_steps)}")
    print(
        f"   Overall confidence: {capsule.reasoning_trace.total_confidence * 100:.1f}%"
    )
    print(f"   Methodology: {capsule.reasoning_trace.confidence_methodology.method}")
    print()

    print("🎯 Per-Step Confidence:")
    for step in capsule.reasoning_trace.reasoning_steps:
        confidence_emoji = (
            "🟢"
            if step.confidence >= 0.9
            else "🔵"
            if step.confidence >= 0.7
            else "🟡"
            if step.confidence >= 0.5
            else "🔴"
        )
        print(
            f"   {confidence_emoji} Step {step.step_id}: {step.confidence * 100:.1f}% - {step.operation}"
        )
        if step.uncertainty_sources:
            print(f"      ⚠️  {len(step.uncertainty_sources)} uncertainty source(s)")
        if step.alternatives_considered:
            print(
                f"      🔀 {len(step.alternatives_considered)} alternative(s) considered"
            )
        if step.measurements:
            print(f"      📊 {len(step.measurements)} measurement(s)")

    print()
    print(
        "💡 Critical Path:",
        capsule.reasoning_trace.confidence_methodology.critical_path_steps,
    )
    print()

    # Save to file
    output_file = "/Users/kay/uatp-capsule-engine/confidence_demo_capsule.json"
    with open(output_file, "w") as f:
        json.dump(capsule.model_dump(mode="json"), f, indent=2, default=str)

    print(f"💾 Saved to: {output_file}")
    print()
    print("🌐 View in dashboard:")
    print(f"   http://localhost:3000/capsules/{capsule.capsule_id}")
    print()
    print("✨ Per-step confidence tracking demonstration complete!")


if __name__ == "__main__":
    main()
