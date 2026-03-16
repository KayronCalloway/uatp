"""
High-Stakes Decision Safety Rails - Demo

Demonstrates the safety validation system for medical, financial, legal,
and autonomous AI decisions.

Usage:
    python scripts/demo_high_stakes_safety.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

from src.safety import decision_safety_validator

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def demo_medical_decisions():
    """Demonstrate medical decision validation"""

    logger.info("\n" + "=" * 60)
    logger.info(" MEDICAL DECISION VALIDATION DEMO")
    logger.info("=" * 60)

    # Example 1: Low-risk medical decision (APPROVED)
    logger.info("\n Example 1: Low-Risk Medical Decision (Routine Checkup)")
    logger.info("-" * 60)

    validation1 = await decision_safety_validator.validate_decision(
        decision={
            "domain": "medical",
            "type": "routine_checkup",
            "recommendation": "Schedule annual physical exam",
            "confidence": 0.95,
            "explanation": "Patient is due for annual checkup based on last visit date",
            "decision_id": "med_001",
        },
        agent_id="medical_assistant_01",
        context={"patient_severity": "low"},
    )

    logger.info(
        f"   Result: {'[OK] APPROVED' if validation1.approved else '[ERROR] REJECTED'}"
    )
    logger.info(f"   Risk Level: {validation1.risk_level.value.upper()}")
    logger.info(f"   Confidence: {validation1.confidence:.2%}")
    logger.info(f"   Reason: {validation1.reason}")

    # Example 2: High-risk medical decision (REQUIRES HUMAN APPROVAL)
    logger.info("\n Example 2: High-Risk Medical Decision (Surgery Recommendation)")
    logger.info("-" * 60)

    validation2 = await decision_safety_validator.validate_decision(
        decision={
            "domain": "medical",
            "type": "surgery_recommendation",
            "recommendation": "Recommend minimally invasive cardiac surgery",
            "confidence": 0.92,
            "explanation": "Based on imaging results and symptom progression, surgery is recommended",
            "decision_id": "med_002",
        },
        agent_id="diagnostic_agent_02",
        context={"patient_severity": "high", "is_invasive": True},
    )

    logger.info(
        f"   Result: {'[OK] APPROVED' if validation2.approved else '⏳ PENDING APPROVAL'}"
    )
    logger.info(f"   Risk Level: {validation2.risk_level.value.upper()}")
    logger.info(f"   Confidence: {validation2.confidence:.2%}")
    logger.info(f"   Requires Human Approval: {validation2.requires_human_approval}")
    logger.info(f"   Approval Request ID: {validation2.approval_request_id}")
    logger.info(f"   Reason: {validation2.reason}")

    # Example 3: CRITICAL medical decision (REQUIRES MULTIPLE APPROVALS)
    logger.info("\n Example 3: CRITICAL Medical Decision (Emergency Treatment)")
    logger.info("-" * 60)

    validation3 = await decision_safety_validator.validate_decision(
        decision={
            "domain": "medical",
            "type": "emergency_intervention",
            "recommendation": "Administer thrombolytic therapy for suspected stroke",
            "confidence": 0.97,
            "explanation": "FAST test positive, within therapeutic window, no contraindications",
            "decision_id": "med_003",
        },
        agent_id="emergency_agent_03",
        context={"patient_severity": "critical", "is_irreversible": True},
    )

    logger.info(
        f"   Result: {'[OK] APPROVED' if validation3.approved else '⏳ PENDING APPROVAL'}"
    )
    logger.info(f"   Risk Level: {validation3.risk_level.value.upper()}")
    logger.info(f"   Confidence: {validation3.confidence:.2%}")
    logger.info(f"   Requires Human Approval: {validation3.requires_human_approval}")
    logger.info(f"   Requires Consensus: {validation3.requires_consensus}")
    logger.info(f"   Reason: {validation3.reason}")


async def demo_financial_decisions():
    """Demonstrate financial decision validation"""

    logger.info("\n" + "=" * 60)
    logger.info(" FINANCIAL DECISION VALIDATION DEMO")
    logger.info("=" * 60)

    # Example 1: Small transaction (APPROVED)
    logger.info("\n Example 1: Small Transaction ($500)")
    logger.info("-" * 60)

    validation1 = await decision_safety_validator.validate_decision(
        decision={
            "domain": "financial",
            "type": "trade_execution",
            "recommendation": "Execute trade: Buy 10 shares of AAPL",
            "confidence": 0.88,
            "explanation": "Market conditions favorable, within risk tolerance",
            "decision_id": "fin_001",
        },
        agent_id="trading_agent_01",
        context={"amount_usd": 500},
    )

    logger.info(
        f"   Result: {'[OK] APPROVED' if validation1.approved else '[ERROR] REJECTED'}"
    )
    logger.info(f"   Risk Level: {validation1.risk_level.value.upper()}")
    logger.info(f"   Confidence: {validation1.confidence:.2%}")
    logger.info(f"   Reason: {validation1.reason}")

    # Example 2: Large transaction (REQUIRES APPROVAL)
    logger.info("\n Example 2: Large Transaction ($150,000)")
    logger.info("-" * 60)

    validation2 = await decision_safety_validator.validate_decision(
        decision={
            "domain": "financial",
            "type": "investment_decision",
            "recommendation": "Allocate $150K to cryptocurrency portfolio",
            "confidence": 0.82,
            "explanation": "Diversification strategy based on risk analysis",
            "decision_id": "fin_002",
        },
        agent_id="investment_agent_02",
        context={"amount_usd": 150000},
    )

    logger.info(
        f"   Result: {'[OK] APPROVED' if validation2.approved else '⏳ PENDING APPROVAL'}"
    )
    logger.info(f"   Risk Level: {validation2.risk_level.value.upper()}")
    logger.info(f"   Confidence: {validation2.confidence:.2%}")
    logger.info(f"   Requires Human Approval: {validation2.requires_human_approval}")
    logger.info(f"   Reason: {validation2.reason}")


async def demo_autonomous_decisions():
    """Demonstrate autonomous vehicle decision validation"""

    logger.info("\n" + "=" * 60)
    logger.info(" AUTONOMOUS VEHICLE DECISION VALIDATION DEMO")
    logger.info("=" * 60)

    # Example 1: Low-speed decision (APPROVED)
    logger.info("\n Example 1: Parking Maneuver (5 mph)")
    logger.info("-" * 60)

    validation1 = await decision_safety_validator.validate_decision(
        decision={
            "domain": "autonomous",
            "type": "parking",
            "recommendation": "Execute parallel parking maneuver",
            "confidence": 0.94,
            "explanation": "Clear parking space detected, no obstacles",
            "decision_id": "auto_001",
        },
        agent_id="autonomous_vehicle_01",
        context={"speed_mph": 5, "involves_human_safety": False},
    )

    logger.info(
        f"   Result: {'[OK] APPROVED' if validation1.approved else '[ERROR] REJECTED'}"
    )
    logger.info(f"   Risk Level: {validation1.risk_level.value.upper()}")
    logger.info(f"   Confidence: {validation1.confidence:.2%}")
    logger.info(f"   Reason: {validation1.reason}")

    # Example 2: High-speed emergency maneuver (REQUIRES CONSENSUS)
    logger.info("\n Example 2: Emergency Collision Avoidance (60 mph)")
    logger.info("-" * 60)

    validation2 = await decision_safety_validator.validate_decision(
        decision={
            "domain": "autonomous",
            "type": "emergency_maneuver",
            "recommendation": "Execute emergency lane change to avoid collision",
            "confidence": 0.98,
            "explanation": "Pedestrian detected in path, adjacent lane clear, sufficient time/space",
            "decision_id": "auto_002",
        },
        agent_id="autonomous_vehicle_02",
        context={"speed_mph": 60, "involves_human_safety": True},
    )

    logger.info(
        f"   Result: {'[OK] APPROVED' if validation2.approved else '⏳ PENDING CONSENSUS'}"
    )
    logger.info(f"   Risk Level: {validation2.risk_level.value.upper()}")
    logger.info(f"   Confidence: {validation2.confidence:.2%}")
    logger.info(f"   Requires Consensus: {validation2.requires_consensus}")
    logger.info(f"   Reason: {validation2.reason}")
    logger.info(
        "   Note: Autonomous CRITICAL decisions use consensus, not human approval"
    )
    logger.info("         (too fast for human in the loop)")


async def demo_emergency_stop():
    """Demonstrate emergency stop mechanism"""

    logger.info("\n" + "=" * 60)
    logger.info(" EMERGENCY STOP MECHANISM DEMO")
    logger.info("=" * 60)

    # Create a decision
    logger.info("\n Creating a medical decision...")

    validation = await decision_safety_validator.validate_decision(
        decision={
            "domain": "medical",
            "type": "prescription",
            "recommendation": "Prescribe antibiotic X",
            "confidence": 0.90,
            "explanation": "Based on infection symptoms",
            "decision_id": "med_emergency_001",
        },
        agent_id="prescribing_agent_01",
        context={"patient_severity": "medium"},
    )

    logger.info("   Decision created: med_emergency_001")
    logger.info(
        f"   Initial status: {'APPROVED' if validation.approved else 'PENDING'}"
    )

    # Trigger emergency stop
    logger.info("\n Triggering emergency stop (patient condition changed)...")

    stop = await decision_safety_validator.trigger_emergency_stop(
        decision_id="med_emergency_001",
        agent_id="prescribing_agent_01",
        reason="Patient developed allergic reaction during assessment",
        triggered_by="human_physician",
    )

    logger.info(f"   [OK] Emergency stop triggered: {stop.stop_id}")
    logger.info(f"   Triggered by: {stop.triggered_by}")
    logger.info(f"   Reason: {stop.reason}")

    # Try to validate same decision again (should be blocked)
    logger.info("\n Attempting to re-validate stopped decision...")

    blocked_validation = await decision_safety_validator.validate_decision(
        decision={
            "domain": "medical",
            "type": "prescription",
            "recommendation": "Prescribe antibiotic X",
            "confidence": 0.90,
            "explanation": "Based on infection symptoms",
            "decision_id": "med_emergency_001",  # Same ID - should be blocked
        },
        agent_id="prescribing_agent_01",
        context={"patient_severity": "medium"},
    )

    logger.info(
        f"   Result: {'[OK] APPROVED' if blocked_validation.approved else ' EMERGENCY STOP ACTIVE'}"
    )
    logger.info(f"   Reason: {blocked_validation.reason}")


async def demo_insufficient_confidence():
    """Demonstrate confidence threshold rejection"""

    logger.info("\n" + "=" * 60)
    logger.info("[WARN] INSUFFICIENT CONFIDENCE DEMO")
    logger.info("=" * 60)

    logger.info("\n High-risk decision with low confidence (should be rejected)")
    logger.info("-" * 60)

    validation = await decision_safety_validator.validate_decision(
        decision={
            "domain": "medical",
            "type": "surgery_recommendation",
            "recommendation": "Recommend cardiac surgery",
            "confidence": 0.75,  # Below 0.95 threshold for HIGH risk medical
            "explanation": "Preliminary assessment suggests surgery may be beneficial",
            "decision_id": "med_low_conf_001",
        },
        agent_id="diagnostic_agent_low_conf",
        context={"patient_severity": "high", "is_invasive": True},
    )

    logger.info(
        f"   Result: {'[OK] APPROVED' if validation.approved else '[ERROR] REJECTED'}"
    )
    logger.info(f"   Risk Level: {validation.risk_level.value.upper()}")
    logger.info(f"   AI Confidence: {validation.confidence:.2%}")
    logger.info("   Required Confidence: 95% (for HIGH risk medical)")
    logger.info(f"   Reason: {validation.reason}")
    logger.info(f"   Warnings: {', '.join(validation.warnings)}")


async def demo_summary():
    """Display summary of safety system features"""

    logger.info("\n" + "=" * 60)
    logger.info(" SAFETY SYSTEM SUMMARY")
    logger.info("=" * 60)

    logger.info("\n[OK] Features Demonstrated:")
    logger.info("   1. Risk-based classification (Low → Medium → High → Critical)")
    logger.info(
        "   2. Confidence thresholds (higher risk = higher confidence required)"
    )
    logger.info("   3. Human-in-the-loop approval (for high-risk decisions)")
    logger.info("   4. Multi-agent consensus (for critical decisions)")
    logger.info("   5. Emergency stop mechanism (immediate decision blocking)")
    logger.info("   6. Explainable AI requirements (all decisions need explanations)")
    logger.info("   7. Complete audit trail (immutable logging of all decisions)")

    logger.info("\n Domain-Specific Safety:")
    logger.info(
        "   Medical:     HIGH/CRITICAL = Human approval + Consensus + 95-99% confidence"
    )
    logger.info("   Financial:   HIGH = Human approval based on transaction size")
    logger.info("   Legal:       HIGH = Human approval + Consensus (high liability)")
    logger.info("   Autonomous:  CRITICAL = Multi-agent consensus (too fast for human)")

    logger.info("\n Safety Metrics:")
    logger.info(
        f"   Pending Human Approvals: {len(decision_safety_validator.pending_approvals)}"
    )
    logger.info(
        f"   Pending Consensus Requests: {len(decision_safety_validator.pending_consensus)}"
    )
    logger.info(
        f"   Active Emergency Stops: {len(decision_safety_validator.emergency_stops)}"
    )

    logger.info("\n Storage Locations:")
    logger.info("   Validations: safety/high_stakes/validations.jsonl")
    logger.info("   Approval Requests: safety/high_stakes/approval_requests.jsonl")
    logger.info("   Consensus Requests: safety/high_stakes/consensus_requests.jsonl")
    logger.info("   Emergency Stops: safety/high_stakes/emergency_stops.jsonl")


async def main():
    """Run all demos"""

    logger.info("\n" + "=" * 60)
    logger.info("HIGH-STAKES DECISION SAFETY RAILS - COMPREHENSIVE DEMO")
    logger.info("=" * 60)

    # Run demos
    await demo_medical_decisions()
    await demo_financial_decisions()
    await demo_autonomous_decisions()
    await demo_emergency_stop()
    await demo_insufficient_confidence()
    await demo_summary()

    logger.info("\n" + "=" * 60)
    logger.info("[OK] DEMO COMPLETE")
    logger.info("=" * 60)

    logger.info("\n Next Steps:")
    logger.info("   1. Review generated files in safety/high_stakes/")
    logger.info("   2. Integrate with API: see src/api/safety_routes.py")
    logger.info("   3. Test approval workflows")
    logger.info("   4. Configure custom thresholds for your use case")
    logger.info("   5. Set up monitoring alerts for critical decisions")


if __name__ == "__main__":
    asyncio.run(main())
