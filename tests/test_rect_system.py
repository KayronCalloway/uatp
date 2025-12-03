"""
Tests for the Real-time Ethical Capsule Triggers (RECTs) system.
"""

from datetime import datetime, timezone

from src.capsule_schema import (
    CapsuleStatus,
    ReasoningStep,
    ReasoningTraceCapsule,
    ReasoningTracePayload,
    Verification,
)
from src.ethics.rect_system import (
    EthicalInterventionSystem,
    EthicalMonitor,
    EthicalRule,
    EthicalRuleEngine,
    EthicalViolationType,
    InterventionAction,
    SeverityLevel,
    rect_system,
)


def test_ethical_rule_engine():
    """Test ethical rule engine functionality."""

    engine = EthicalRuleEngine()

    # Test rule creation
    rule = EthicalRule(
        rule_id="test_rule_001",
        rule_type=EthicalViolationType.HARMFUL_CONTENT,
        pattern="keywords:harmful,dangerous",
        severity=SeverityLevel.HIGH,
        confidence_threshold=0.8,
        intervention=InterventionAction.QUARANTINE,
    )

    engine.add_rule(rule)
    assert rule.rule_id in engine.rules

    # Test content evaluation
    harmful_content = "This contains harmful and dangerous content"
    violations = engine.evaluate_content(harmful_content, "test_capsule_001")

    assert len(violations) > 0
    violation = violations[0]
    assert violation.violation_type == EthicalViolationType.HARMFUL_CONTENT
    assert violation.severity == SeverityLevel.HIGH
    assert violation.intervention_recommended == InterventionAction.QUARANTINE


def test_ethical_intervention_system():
    """Test ethical intervention system."""

    from src.ethics.rect_system import EthicalViolation

    intervention_system = EthicalInterventionSystem()

    # Create test violation
    violation = EthicalViolation(
        violation_id="test_violation_001",
        capsule_id="caps_2024_01_01_0123456789abcdef",
        violation_type=EthicalViolationType.TOXICITY,
        severity=SeverityLevel.MEDIUM,
        confidence=0.85,
        message="Test violation message",
        detected_content="Test content",
        context={},
        timestamp=datetime.now(timezone.utc),
        detector_id="test_detector",
        intervention_recommended=InterventionAction.WARNING,
    )

    # Execute intervention
    result = intervention_system.execute_intervention(violation)

    assert result.violation_id == violation.violation_id
    assert result.action_taken == InterventionAction.WARNING
    assert result.success is True


def test_ethical_monitor():
    """Test ethical monitor."""

    monitor = EthicalMonitor()

    # Create capsule with potentially harmful content
    capsule = ReasoningTraceCapsule(
        capsule_id="caps_2024_01_01_0123456789abcdef",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
        verification=Verification(),
        reasoning_trace=ReasoningTracePayload(
            steps=[
                ReasoningStep(
                    content="This content contains harmful and toxic language",
                    step_type="observation",
                    metadata={},
                )
            ]
        ),
    )

    # Monitor capsule
    violations = monitor.monitor_capsule(capsule)

    # Should detect violations
    assert len(violations) > 0

    # Check violation details
    violation = violations[0]
    assert violation.capsule_id == capsule.capsule_id
    assert violation.violation_type in [
        EthicalViolationType.HARMFUL_CONTENT,
        EthicalViolationType.TOXICITY,
    ]


def test_rect_system():
    """Test complete RECT system."""

    # Create capsule with ethical concerns
    capsule = ReasoningTraceCapsule(
        capsule_id="caps_2024_01_01_0123456789abcdef",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
        verification=Verification(),
        reasoning_trace=ReasoningTracePayload(
            steps=[
                ReasoningStep(
                    content="This is manipulative content designed to deceive users",
                    step_type="observation",
                    metadata={},
                )
            ]
        ),
    )

    # Process through RECT system
    result = rect_system.process_capsule(capsule)

    assert result["rect_enabled"] is True
    assert result["capsule_id"] == capsule.capsule_id
    assert "violations" in result
    assert "violation_count" in result
    assert "actions_taken" in result


def test_whitelist_blacklist():
    """Test whitelist and blacklist functionality."""

    monitor = EthicalMonitor()

    # Create test capsule
    capsule = ReasoningTraceCapsule(
        capsule_id="caps_2024_01_01_0123456789abcdef",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
        verification=Verification(),
        reasoning_trace=ReasoningTracePayload(
            steps=[
                ReasoningStep(
                    content="This has harmful content",
                    step_type="observation",
                    metadata={},
                )
            ]
        ),
    )

    # Add to whitelist
    monitor.add_to_whitelist(capsule.capsule_id)

    # Should not detect violations for whitelisted capsule
    violations = monitor.monitor_capsule(capsule)
    assert len(violations) == 0

    # Remove from whitelist and add to blacklist
    monitor.whitelist.remove(capsule.capsule_id)
    monitor.add_to_blacklist(capsule.capsule_id)

    # Should detect blacklist violation
    violations = monitor.monitor_capsule(capsule)
    assert len(violations) > 0
    assert violations[0].violation_type == EthicalViolationType.HARMFUL_CONTENT


def test_monitoring_report():
    """Test monitoring report generation."""

    monitor = EthicalMonitor()

    # Create and monitor some capsules
    for i in range(3):
        capsule = ReasoningTraceCapsule(
            capsule_id=f"report_test_{i}",
            version="7.0",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.ACTIVE,
            verification=Verification(),
            reasoning_trace=ReasoningTracePayload(
                steps=[
                    ReasoningStep(
                        content=f"Test content {i} with harmful elements",
                        step_type="observation",
                        metadata={},
                    )
                ]
            ),
        )
        monitor.monitor_capsule(capsule)

    # Generate report
    report = monitor.get_monitoring_report()

    assert "monitoring_stats" in report
    assert "recent_violations" in report
    assert "violation_breakdown" in report
    assert "severity_distribution" in report
    assert "rule_statistics" in report


def test_false_positive_reporting():
    """Test false positive reporting."""

    monitor = EthicalMonitor()

    initial_false_positives = monitor.monitoring_stats["false_positives"]

    # Report false positive
    monitor.report_false_positive("fake_violation_id")

    assert monitor.monitoring_stats["false_positives"] == initial_false_positives + 1


def test_rule_pattern_matching():
    """Test different rule pattern matching methods."""

    # Test regex pattern
    regex_rule = EthicalRule(
        rule_id="regex_test",
        rule_type=EthicalViolationType.PRIVACY_VIOLATION,
        pattern="regex:\\b\\d{3}-\\d{2}-\\d{4}\\b",  # SSN pattern
        severity=SeverityLevel.HIGH,
        confidence_threshold=0.9,
        intervention=InterventionAction.CONTENT_FILTER,
    )

    # Test with SSN-like content
    matches, confidence = regex_rule.matches("My SSN is 123-45-6789")
    assert matches is True
    assert confidence > 0.0

    # Test with non-matching content
    matches, confidence = regex_rule.matches("No SSN here")
    assert matches is False
    assert confidence == 0.0

    # Test keyword pattern
    keyword_rule = EthicalRule(
        rule_id="keyword_test",
        rule_type=EthicalViolationType.BIAS_DETECTION,
        pattern="keywords:biased,prejudiced",
        severity=SeverityLevel.MEDIUM,
        confidence_threshold=0.7,
        intervention=InterventionAction.WARNING,
    )

    matches, confidence = keyword_rule.matches("This is a biased statement")
    assert matches is True
    assert confidence > 0.0


def test_system_enable_disable():
    """Test enabling and disabling the RECT system."""

    # Test disabling
    rect_system.disable_system()
    assert rect_system.enabled is False

    # Test enabling
    rect_system.enable_system()
    assert rect_system.enabled is True


if __name__ == "__main__":
    test_ethical_rule_engine()
    test_ethical_intervention_system()
    test_ethical_monitor()
    test_rect_system()
    test_whitelist_blacklist()
    test_monitoring_report()
    test_false_positive_reporting()
    test_rule_pattern_matching()
    test_system_enable_disable()
    print("✅ All RECT system tests passed!")
