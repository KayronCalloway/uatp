"""
Create a Test Rich Capsule with Full Analytics

This script creates a reasoning capsule using the integrated rich capture system,
which automatically includes:
- Uncertainty analysis (epistemic, aleatoric, total, risk score, confidence interval)
- Critical path analysis (critical steps, bottlenecks, decision points)
- Improvement recommendations
- Trust score
- Step-level metadata

Usage:
    python3 create_test_rich_capsule.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.analysis.critical_path import CriticalPathAnalyzer
from src.analysis.uncertainty_quantification import UncertaintyQuantifier
from src.app_factory import create_app
from src.core.database import db
from src.utils.rich_capsule_creator import (
    RichReasoningStep,
    create_rich_reasoning_capsule,
)


async def create_test_capsule():
    """Create a test capsule with rich metadata."""

    print("=" * 70)
    print("  CREATING TEST RICH CAPSULE")
    print("=" * 70)

    # Initialize database
    app = create_app()
    if not db.engine:
        db.init_app(app)

    # Define a sample reasoning problem
    prompt = "How can we improve the performance of a web application?"

    # Create rich reasoning steps with detailed metadata
    steps = [
        RichReasoningStep(
            step=1,
            reasoning="Analyze current performance metrics to identify bottlenecks",
            confidence=0.92,
            operation="analysis",
            measurements={"analysis_depth": "comprehensive", "metrics_reviewed": 15},
            uncertainty_sources=[
                "Incomplete metrics data",
                "Tool measurement variance",
            ],
            confidence_basis="Based on standard profiling methodologies",
            alternatives_considered=[
                "Quick visual inspection",
                "User feedback only",
                "Comprehensive profiling (chosen)",
            ],
            attribution_sources=["performance_team", "profiling_tools"],
        ),
        RichReasoningStep(
            step=2,
            reasoning="Identified database queries as primary bottleneck (47% of total response time)",
            confidence=0.89,
            operation="measurement",
            measurements={
                "query_time_ms": 235,
                "total_request_time_ms": 500,
                "percentage": 47.0,
            },
            uncertainty_sources=["Network latency variation"],
            confidence_basis="Direct measurement over 1000 requests",
            depends_on_steps=[1],
            attribution_sources=["performance_team", "apm_tool"],
        ),
        RichReasoningStep(
            step=3,
            reasoning="Recommend implementing query caching and indexing strategy",
            confidence=0.85,
            operation="recommendation",
            measurements={
                "expected_improvement": "60-70%",
                "implementation_effort": "medium",
            },
            uncertainty_sources=[
                "Cache hit rate assumptions",
                "Index selectivity estimates",
            ],
            confidence_basis="Based on similar optimization case studies",
            alternatives_considered=[
                "Database replication",
                "Query optimization only",
                "Combined caching + indexing (chosen)",
            ],
            depends_on_steps=[1, 2],
            attribution_sources=["performance_team", "database_team"],
        ),
        RichReasoningStep(
            step=4,
            reasoning="Identified N+1 query pattern in user profile loading",
            confidence=0.94,
            operation="diagnosis",
            measurements={"queries_per_request": 45, "should_be": 2},
            uncertainty_sources=[],
            confidence_basis="Clear code inspection showing multiple sequential queries",
            depends_on_steps=[2],
            attribution_sources=["performance_team"],
        ),
        RichReasoningStep(
            step=5,
            reasoning="Implement eager loading for user profiles and related data",
            confidence=0.88,
            operation="solution",
            measurements={
                "expected_query_reduction": "95%",
                "estimated_time_saving_ms": 180,
            },
            uncertainty_sources=["ORM behavior variation", "Data size growth"],
            confidence_basis="Standard ORM eager loading patterns",
            alternatives_considered=[
                "Manual query optimization",
                "Data denormalization",
                "Eager loading (chosen)",
            ],
            depends_on_steps=[4],
            attribution_sources=["performance_team", "backend_team"],
        ),
    ]

    final_answer = """
Performance improvement strategy:

1. **Database Optimization** (Primary - 47% of response time)
   - Implement Redis caching layer for frequently accessed queries
   - Add strategic indexes on user_id, created_at, and status fields
   - Expected improvement: 60-70% reduction in database query time

2. **N+1 Query Fix** (Critical - 45 queries → 2 queries)
   - Implement eager loading for user profiles and relationships
   - Expected improvement: 95% query reduction, ~180ms time saving

3. **Implementation Priority:**
   - Phase 1: Fix N+1 queries (quick win, high impact)
   - Phase 2: Add caching layer (medium effort, high impact)
   - Phase 3: Optimize indexes (low effort, medium impact)

**Expected Total Improvement:** 70-80% reduction in response time
**Implementation Time:** 2-3 weeks
**Risk Level:** Low (standard optimization patterns)
"""

    overall_confidence = 0.89

    print("\n📝 Creating capsule:")
    print(f"   Prompt: {prompt}")
    print(f"   Steps: {len(steps)}")
    print(f"   Confidence: {overall_confidence:.2%}")

    # Generate a capsule ID
    import uuid
    from datetime import datetime

    capsule_id = f"caps_{datetime.now().strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

    # Create the base capsule
    capsule = create_rich_reasoning_capsule(
        capsule_id=capsule_id,
        prompt=prompt,
        reasoning_steps=steps,
        final_answer=final_answer,
        overall_confidence=overall_confidence,
        model_used="Claude Sonnet 4.5",
        created_by="test_rich_capsule_script",
    )

    # Add critical path analysis
    critical_path_analysis = CriticalPathAnalyzer.analyze(steps)
    critical_path_dict = CriticalPathAnalyzer.to_dict(critical_path_analysis)
    capsule["payload"]["critical_path_analysis"] = critical_path_dict

    # Add improvement recommendations
    step_map = {step.step: step for step in steps}
    improvement_recommendations = (
        CriticalPathAnalyzer.generate_improvement_recommendations(
            critical_path_analysis, step_map
        )
    )
    if improvement_recommendations:
        capsule["payload"]["improvement_recommendations"] = improvement_recommendations

    # Add uncertainty analysis
    step_uncertainties = []
    for step in steps:
        step_unc = UncertaintyQuantifier.estimate_confidence_uncertainty(
            confidence=step.confidence, sample_size=len(steps), prior_mean=0.8
        )
        step_uncertainties.append(step_unc)

    overall_uncertainty = UncertaintyQuantifier.propagate_uncertainty(
        step_uncertainties
    )
    capsule["payload"]["uncertainty_analysis"] = {
        "epistemic_uncertainty": round(overall_uncertainty.epistemic_uncertainty, 3),
        "aleatoric_uncertainty": round(overall_uncertainty.aleatoric_uncertainty, 3),
        "total_uncertainty": round(overall_uncertainty.total_uncertainty, 3),
        "confidence_interval": [
            round(overall_uncertainty.confidence_interval[0], 3),
            round(overall_uncertainty.confidence_interval[1], 3),
        ],
        "risk_score": round(overall_uncertainty.risk_score, 3),
    }

    # Save to database
    from datetime import datetime

    from dateutil import parser

    from src.models.capsule import CapsuleModel

    # Convert timestamp string to datetime
    if isinstance(capsule["timestamp"], str):
        timestamp_dt = parser.parse(capsule["timestamp"])
    else:
        timestamp_dt = capsule["timestamp"]

    async with db.get_session() as session:
        capsule_model = CapsuleModel(
            capsule_id=capsule["capsule_id"],
            capsule_type=capsule.get("type", "reasoning_trace"),  # Use 'type' field
            version=capsule["version"],
            timestamp=timestamp_dt,
            status=capsule["status"],
            payload=capsule["payload"],
            verification=capsule["verification"],
        )
        session.add(capsule_model)
        await session.commit()

    print("\n✅ Rich capsule created successfully!")
    print("\n📦 Capsule Details:")
    print(f"   ID: {capsule['capsule_id']}")
    print(f"   Type: {capsule.get('type', 'reasoning_trace')}")
    print(f"   Version: {capsule['version']}")

    print("\n🎯 Rich Metadata Included:")
    payload = capsule["payload"]

    if "uncertainty_analysis" in payload:
        unc = payload["uncertainty_analysis"]
        print("   ✓ Uncertainty Analysis:")
        print(f"      - Epistemic: {unc['epistemic_uncertainty']:.3f}")
        print(f"      - Aleatoric: {unc['aleatoric_uncertainty']:.3f}")
        print(f"      - Total: {unc['total_uncertainty']:.3f}")
        print(f"      - Risk Score: {unc['risk_score']:.3f}")
        print(
            f"      - 95% CI: [{unc['confidence_interval'][0]:.3f}, {unc['confidence_interval'][1]:.3f}]"
        )

    if "critical_path_analysis" in payload:
        cpa = payload["critical_path_analysis"]
        print("   ✓ Critical Path Analysis:")
        print(f"      - Critical Steps: {cpa['critical_steps']}")
        print(f"      - Bottleneck Steps: {cpa.get('bottleneck_steps', [])}")
        print(f"      - Path Strength: {cpa['critical_path_strength']:.3f}")
        print(f"      - Dependency Depth: {cpa['dependency_depth']}")

    if "improvement_recommendations" in payload:
        recs = payload["improvement_recommendations"]
        print(f"   ✓ Improvement Recommendations: {len(recs)} items")
        for i, rec in enumerate(recs[:3], 1):
            print(f"      {i}. {rec[:70]}...")

    if "trust_score" in capsule["verification"]:
        print(f"   ✓ Trust Score: {capsule['verification']['trust_score']:.3f}")

    print("\n🌐 View in Frontend:")
    print("   1. Start frontend: cd frontend && npm run dev")
    print("   2. Navigate to: http://localhost:3000")
    print(f"   3. Go to Capsules → Click on: {capsule['capsule_id']}")
    print("   4. See all rich analytics displayed!")

    print("\n" + "=" * 70)
    print("  DONE!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(create_test_capsule())
