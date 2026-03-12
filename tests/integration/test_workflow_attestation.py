"""
Integration tests for UATP Workflow Attestations.

Tests the in-toto/Witness inspired chain-of-custody verification.
"""

import hashlib
import json
from datetime import datetime, timezone

import pytest

from src.attestation import (
    PERMISSIVE_POLICY,
    STRICT_POLICY,
    AttestationValidity,
    AttestationVerifier,
    ChainVerificationResult,
    LinkAttestation,
    PolicyResult,
    ResourceDescriptor,
    SimplePolicy,
    WorkflowAttestation,
    build_workflow_from_capsule_chain,
    compute_digest,
    create_link_from_capsules,
)


class TestResourceDescriptor:
    """Tests for ResourceDescriptor."""

    def test_from_content(self):
        content = b"test content"
        desc = ResourceDescriptor.from_content(content, uri="file://test.txt")

        expected_hash = hashlib.sha256(content).hexdigest()
        assert desc.digest["sha256"] == expected_hash
        assert desc.uri == "file://test.txt"
        assert desc.name == "test.txt"

    def test_from_capsule_id(self):
        desc = ResourceDescriptor.from_capsule_id(
            "caps_123",
            content_hash="sha256:abcd1234",
        )

        assert desc.uri == "capsule://caps_123"
        assert desc.digest["sha256"] == "abcd1234"
        assert desc.media_type == "application/vnd.uatp.capsule.v1+json"

    def test_matches_digest(self):
        desc1 = ResourceDescriptor(
            uri="a",
            digest={"sha256": "abc123"},
        )
        desc2 = ResourceDescriptor(
            uri="b",
            digest={"sha256": "abc123"},
        )
        desc3 = ResourceDescriptor(
            uri="c",
            digest={"sha256": "different"},
        )

        assert desc1.matches_digest(desc2) == True
        assert desc1.matches_digest(desc3) == False

    def test_canonical_digest(self):
        desc = ResourceDescriptor(
            uri="test",
            digest={"sha256": "abc123", "sha384": "def456"},
        )
        assert desc.canonical_digest() == "sha256:abc123"

    def test_hash_allows_set_membership(self):
        desc1 = ResourceDescriptor(uri="a", digest={"sha256": "abc"})
        desc2 = ResourceDescriptor(uri="b", digest={"sha256": "def"})
        desc3 = ResourceDescriptor(uri="a", digest={"sha256": "abc"})  # Same as desc1

        # Should be usable in a set
        s = {desc1, desc2}
        assert len(s) == 2

        # desc3 should be considered equal to desc1
        assert desc1 == desc3
        s.add(desc3)
        assert len(s) == 2  # No new element added

    def test_repr(self):
        desc = ResourceDescriptor(
            uri="capsule://caps_123",
            digest={"sha256": "abcdef1234567890"},
            name="caps_123",
        )
        repr_str = repr(desc)
        assert "caps_123" in repr_str
        assert "sha256:abcdef" in repr_str

    def test_to_dict_from_dict(self):
        original = ResourceDescriptor(
            uri="capsule://caps_123",
            digest={"sha256": "abc"},
            name="caps_123",
            media_type="application/json",
            annotations={"key": "value"},
        )

        d = original.to_dict()
        restored = ResourceDescriptor.from_dict(d)

        assert restored.uri == original.uri
        assert restored.digest == original.digest
        assert restored.annotations == original.annotations


class TestLinkAttestation:
    """Tests for LinkAttestation."""

    def test_create_basic(self):
        link = LinkAttestation(name="test_step")

        assert link.name == "test_step"
        assert link.step_id is not None
        assert len(link.materials) == 0
        assert len(link.products) == 0

    def test_repr(self):
        link = LinkAttestation(name="inference")
        link.add_material("in", digest={"sha256": "abc"})
        link.add_product("out1", digest={"sha256": "def"})
        link.add_product("out2", digest={"sha256": "ghi"})

        repr_str = repr(link)
        assert "inference" in repr_str
        assert "materials=1" in repr_str
        assert "products=2" in repr_str
        assert "unsigned" in repr_str

    def test_repr_signed(self):
        link = LinkAttestation(name="signed_step")
        link.signature = "abc123"

        repr_str = repr(link)
        assert "signed" in repr_str

    def test_add_materials_and_products(self):
        link = LinkAttestation(name="inference")
        link.add_material("file://input.txt", digest={"sha256": "abc"})
        link.add_capsule_product("caps_output", "sha256:def")

        assert len(link.materials) == 1
        assert len(link.products) == 1
        assert link.materials[0].uri == "file://input.txt"
        assert link.products[0].uri == "capsule://caps_output"

    def test_content_hash_deterministic(self):
        link1 = LinkAttestation(name="step1", step_id="fixed")
        link1.add_capsule_material("caps_a", "sha256:123")

        link2 = LinkAttestation(name="step1", step_id="fixed")
        link2.add_capsule_material("caps_a", "sha256:123")

        assert link1.content_hash() == link2.content_hash()

    def test_materials_match_products(self):
        prev_link = LinkAttestation(name="step1")
        prev_link.add_product("out", digest={"sha256": "abc123"})

        next_link = LinkAttestation(name="step2")
        next_link.add_material("in", digest={"sha256": "abc123"})

        assert next_link.materials_match_products(prev_link) == True

    def test_materials_dont_match_products(self):
        prev_link = LinkAttestation(name="step1")
        prev_link.add_product("out", digest={"sha256": "abc123"})

        next_link = LinkAttestation(name="step2")
        next_link.add_material("in", digest={"sha256": "different"})

        assert next_link.materials_match_products(prev_link) == False

    def test_to_dict_from_dict(self):
        original = LinkAttestation(
            name="test",
            step_id="step_001",
            command=["python", "run.py"],
            byproducts={"stdout": "output"},
        )
        original.add_capsule_material("caps_in", "sha256:abc")
        original.add_capsule_product("caps_out", "sha256:def")
        original.signed_by = "key_123"
        original.started_at = datetime.now(timezone.utc)

        d = original.to_dict()
        restored = LinkAttestation.from_dict(d)

        assert restored.name == original.name
        assert restored.step_id == original.step_id
        assert len(restored.materials) == 1
        assert len(restored.products) == 1
        assert restored.command == original.command

    def test_products_contain_matching_digest(self):
        """Test products_contain finds matching digest."""
        link = LinkAttestation(name="step")
        link.add_product("out1", digest={"sha256": "abc123"})
        link.add_product("out2", digest={"sha256": "def456"})

        desc = ResourceDescriptor(uri="different", digest={"sha256": "abc123"})
        assert link.products_contain(desc) == True

    def test_products_contain_no_match(self):
        """Test products_contain returns False when no match."""
        link = LinkAttestation(name="step")
        link.add_product("out", digest={"sha256": "abc123"})

        desc = ResourceDescriptor(uri="x", digest={"sha256": "no_match"})
        assert link.products_contain(desc) == False

    def test_products_contain_empty_products(self):
        """Test products_contain with no products."""
        link = LinkAttestation(name="empty_step")

        desc = ResourceDescriptor(uri="x", digest={"sha256": "abc"})
        assert link.products_contain(desc) == False

    def test_canonical_bytes_includes_optional_fields(self):
        """Test canonical_bytes includes command, env, byproducts when set."""
        link = LinkAttestation(
            name="with_context",
            step_id="fixed_id",
            command=["python", "script.py"],
            environment={"PATH": "/usr/bin"},
            byproducts={"exit_code": 0},
        )

        canonical = link.canonical_bytes()
        assert b"command" in canonical
        assert b"python" in canonical
        assert b"environment" in canonical
        assert b"PATH" in canonical
        assert b"byproducts" in canonical
        assert b"exit_code" in canonical

    def test_canonical_bytes_excludes_empty_optional_fields(self):
        """Test canonical_bytes excludes None/empty optional fields."""
        link = LinkAttestation(name="minimal", step_id="fixed_id")

        canonical = link.canonical_bytes()
        assert b"command" not in canonical
        assert b"environment" not in canonical
        assert b"byproducts" not in canonical

    def test_materials_match_products_empty_materials(self):
        """Test that empty materials always match."""
        prev_link = LinkAttestation(name="prev")
        prev_link.add_product("out", digest={"sha256": "abc"})

        # Link with no materials should match (no materials to verify)
        next_link = LinkAttestation(name="next")

        assert next_link.materials_match_products(prev_link) == True

    def test_to_dict_from_dict_with_all_timestamps(self):
        """Test serialization with all timestamp fields."""
        now = datetime.now(timezone.utc)
        original = LinkAttestation(name="full", step_id="s1")
        original.signed_by = "key1"
        original.signature = "sig_base64"
        original.signed_at = now
        original.started_at = now
        original.completed_at = now

        d = original.to_dict()

        assert "signedAt" in d
        assert "startedAt" in d
        assert "completedAt" in d
        assert d["signedBy"] == "key1"
        assert d["signature"] == "sig_base64"

        restored = LinkAttestation.from_dict(d)

        assert restored.signed_at is not None
        assert restored.started_at is not None
        assert restored.completed_at is not None
        assert restored.signed_by == "key1"


class TestSimplePolicy:
    """Tests for SimplePolicy."""

    def test_permissive_policy(self):
        links = [LinkAttestation(name="any_step")]
        result = PERMISSIVE_POLICY.evaluate(links)
        assert result.passed == True

    def test_required_steps(self):
        policy = SimplePolicy(required_steps=["step_a", "step_b"])

        links = [LinkAttestation(name="step_a")]
        result = policy.evaluate(links)

        assert result.passed == False
        assert any("step_b" in v.message for v in result.violations)

    def test_step_order(self):
        policy = SimplePolicy(
            required_steps=["first", "second"],
            step_order=["first", "second"],
        )

        # Correct order
        links_correct = [
            LinkAttestation(name="first"),
            LinkAttestation(name="second"),
        ]
        result = policy.evaluate(links_correct)
        assert result.passed == True

        # Wrong order
        links_wrong = [
            LinkAttestation(name="second"),
            LinkAttestation(name="first"),
        ]
        result = policy.evaluate(links_wrong)
        assert result.passed == False
        assert any(v.rule == "step_order" for v in result.violations)

    def test_allowed_signers(self):
        policy = SimplePolicy(
            allowed_signers={"sign_step": ["key_1", "key_2"]},
        )

        # Authorized signer
        link_ok = LinkAttestation(name="sign_step")
        link_ok.signed_by = "key_1"
        result = policy.evaluate([link_ok])
        assert result.passed == True

        # Unauthorized signer
        link_bad = LinkAttestation(name="sign_step")
        link_bad.signed_by = "unauthorized_key"
        result = policy.evaluate([link_bad])
        assert result.passed == False

    def test_extra_steps_not_allowed(self):
        policy = SimplePolicy(
            required_steps=["allowed"],
            allow_extra_steps=False,
        )

        links = [
            LinkAttestation(name="allowed"),
            LinkAttestation(name="extra"),
        ]
        result = policy.evaluate(links)

        assert result.passed == False
        assert any("extra" in v.message for v in result.violations)

    def test_missing_signature_warning(self):
        """Test that missing signature generates a warning, not failure."""
        policy = SimplePolicy(
            allowed_signers={"sign_step": ["key_1"]},
        )

        link = LinkAttestation(name="sign_step")
        # No signature set
        result = policy.evaluate([link])

        assert result.passed == True  # Warnings don't fail
        assert len(result.warnings) == 1
        assert "no signature" in result.warnings[0].message.lower()

    def test_require_material_digests(self):
        """Test that missing material digests fail strict policy."""
        policy = SimplePolicy(require_material_digests=True)

        link = LinkAttestation(name="step")
        link.add_material("file://test", digest=None)  # No digest

        result = policy.evaluate([link])

        assert result.passed == False
        assert any("digest" in v.message.lower() for v in result.violations)

    def test_require_product_digests(self):
        """Test that missing product digests fail strict policy."""
        policy = SimplePolicy(require_product_digests=True)

        link = LinkAttestation(name="step")
        link.add_product("file://out", digest=None)  # No digest

        result = policy.evaluate([link])

        assert result.passed == False
        assert any("digest" in v.message.lower() for v in result.violations)

    def test_policy_to_dict_from_dict(self):
        """Test policy serialization roundtrip."""
        original = SimplePolicy(
            name="test_policy",
            description="Test description",
            required_steps=["a", "b"],
            allowed_signers={"a": ["key1"]},
            step_order=["a", "b"],
            allow_extra_steps=False,
        )

        d = original.to_dict()
        restored = SimplePolicy.from_dict(d)

        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.required_steps == original.required_steps
        assert restored.allowed_signers == original.allowed_signers
        assert restored.step_order == original.step_order
        assert restored.allow_extra_steps == original.allow_extra_steps


class TestPolicyResult:
    """Tests for PolicyResult serialization and methods."""

    def test_policy_result_to_dict_passing(self):
        """Test to_dict for a passing result."""
        result = PolicyResult(passed=True)
        d = result.to_dict()

        assert d["passed"] == True
        assert d["violations"] == []
        assert d["warnings"] == []

    def test_policy_result_to_dict_with_violations(self):
        """Test to_dict with violations and warnings."""
        result = PolicyResult(passed=True)
        result.add_violation("test_rule", "Test violation message", step="step1")
        result.add_warning("warn_rule", "Test warning message", step="step2")

        d = result.to_dict()

        assert d["passed"] == False
        assert len(d["violations"]) == 1
        assert d["violations"][0]["rule"] == "test_rule"
        assert d["violations"][0]["message"] == "Test violation message"
        assert d["violations"][0]["step"] == "step1"

        assert len(d["warnings"]) == 1
        assert d["warnings"][0]["rule"] == "warn_rule"

    def test_policy_result_add_violation_sets_passed_false(self):
        """Test that add_violation sets passed to False."""
        result = PolicyResult(passed=True)
        assert result.passed == True

        result.add_violation("rule", "message")
        assert result.passed == False

    def test_policy_result_add_warning_keeps_passed_true(self):
        """Test that add_warning doesn't change passed status."""
        result = PolicyResult(passed=True)

        result.add_warning("rule", "warning message")

        assert result.passed == True
        assert len(result.warnings) == 1

    def test_policy_result_multiple_violations(self):
        """Test accumulating multiple violations."""
        result = PolicyResult(passed=True)
        result.add_violation("rule1", "msg1", step="s1")
        result.add_violation("rule2", "msg2", step="s2")
        result.add_violation("rule3", "msg3")

        assert len(result.violations) == 3
        assert result.violations[2].step is None


class TestWorkflowAttestation:
    """Tests for WorkflowAttestation."""

    def test_create_empty_workflow(self):
        workflow = WorkflowAttestation(
            workflow_id="wf_001",
            name="Test Workflow",
        )

        assert workflow.workflow_id == "wf_001"
        assert workflow.status == "pending"
        assert len(workflow.steps) == 0

    def test_add_steps(self):
        workflow = WorkflowAttestation(workflow_id="wf_001")

        link1 = LinkAttestation(name="step1")
        workflow.add_step(link1)

        assert len(workflow.steps) == 1
        assert workflow.status == "running"

    def test_is_complete_property(self):
        workflow = WorkflowAttestation(workflow_id="wf_001")
        assert workflow.is_complete == False

        workflow.complete()
        assert workflow.is_complete == True

    def test_is_complete_on_failure(self):
        workflow = WorkflowAttestation(workflow_id="wf_001")
        workflow.fail()
        assert workflow.is_complete == True

    def test_step_count_property(self):
        workflow = WorkflowAttestation(workflow_id="wf_001")
        assert workflow.step_count == 0

        workflow.add_step(LinkAttestation(name="s1"))
        assert workflow.step_count == 1

        workflow.add_step(LinkAttestation(name="s2"))
        assert workflow.step_count == 2

    def test_duration_seconds_not_complete(self):
        workflow = WorkflowAttestation(workflow_id="wf_001")
        assert workflow.duration_seconds is None

    def test_duration_seconds_complete(self):
        from datetime import timedelta

        workflow = WorkflowAttestation(workflow_id="wf_001")
        workflow.created_at = datetime.now(timezone.utc) - timedelta(seconds=30)
        workflow.complete()

        duration = workflow.duration_seconds
        assert duration is not None
        assert duration >= 30

    def test_repr(self):
        workflow = WorkflowAttestation(workflow_id="wf_123", name="Test")
        workflow.add_step(LinkAttestation(name="s1"))
        workflow.add_step(LinkAttestation(name="s2"))

        repr_str = repr(workflow)
        assert "wf_123" in repr_str
        assert "steps=2" in repr_str
        assert "running" in repr_str

    def test_verify_chain_single_step(self):
        workflow = WorkflowAttestation(workflow_id="wf_001")
        workflow.add_step(LinkAttestation(name="only"))

        result = workflow.verify_chain()
        assert result.is_valid == True
        assert result.total_handoffs == 0

    def test_verify_chain_valid(self):
        """Test valid chain: products flow to materials."""
        workflow = WorkflowAttestation(workflow_id="wf_001")

        # Step 1: produces capsule A
        step1 = LinkAttestation(name="step1")
        step1.add_product("caps_a", digest={"sha256": "hash_a"})
        workflow.add_step(step1)

        # Step 2: consumes capsule A, produces capsule B
        step2 = LinkAttestation(name="step2")
        step2.add_material("caps_a", digest={"sha256": "hash_a"})
        step2.add_product("caps_b", digest={"sha256": "hash_b"})
        workflow.add_step(step2)

        # Step 3: consumes capsule B
        step3 = LinkAttestation(name="step3")
        step3.add_material("caps_b", digest={"sha256": "hash_b"})
        step3.add_product("caps_final", digest={"sha256": "hash_final"})
        workflow.add_step(step3)

        result = workflow.verify_chain()

        assert result.is_valid == True
        assert result.verified_handoffs == 2
        assert result.total_handoffs == 2
        assert len(result.breaks) == 0

    def test_verify_chain_broken(self):
        """Test broken chain: material doesn't match previous product."""
        workflow = WorkflowAttestation(workflow_id="wf_001")

        # Step 1: produces with hash_a
        step1 = LinkAttestation(name="step1")
        step1.add_product("caps_a", digest={"sha256": "hash_a"})
        workflow.add_step(step1)

        # Step 2: claims material with DIFFERENT hash
        step2 = LinkAttestation(name="step2")
        step2.add_material("caps_a", digest={"sha256": "TAMPERED_hash"})
        workflow.add_step(step2)

        result = workflow.verify_chain()

        assert result.is_valid == False
        assert result.verified_handoffs == 0
        assert len(result.breaks) == 1
        assert result.breaks[0]["fromStep"] == "step1"
        assert result.breaks[0]["toStep"] == "step2"

    def test_full_verification(self):
        """Test combined chain + policy verification."""
        policy = SimplePolicy(
            required_steps=["inference", "review"],
            step_order=["inference", "review"],
        )

        workflow = WorkflowAttestation(
            workflow_id="wf_001",
            policy=policy,
        )

        step1 = LinkAttestation(name="inference")
        step1.add_product("out", digest={"sha256": "hash1"})
        workflow.add_step(step1)

        step2 = LinkAttestation(name="review")
        step2.add_material("in", digest={"sha256": "hash1"})
        step2.add_product("final", digest={"sha256": "hash2"})
        workflow.add_step(step2)

        result = workflow.verify()

        assert result.is_valid == True
        assert result.chain_result.is_valid == True
        assert result.policy_result.passed == True

    def test_to_dict_from_dict(self):
        original = WorkflowAttestation(
            workflow_id="wf_001",
            name="Test",
            description="A test workflow",
        )
        step = LinkAttestation(name="step1")
        step.add_capsule_product("caps_out", "sha256:abc")
        original.add_step(step)
        original.complete()

        d = original.to_dict()
        restored = WorkflowAttestation.from_dict(d)

        assert restored.workflow_id == original.workflow_id
        assert restored.name == original.name
        assert restored.status == "completed"
        assert len(restored.steps) == 1


class TestWorkflowAccessorMethods:
    """Tests for WorkflowAttestation accessor methods."""

    def test_get_step_by_name(self):
        """Test get_step finds step by name."""
        workflow = WorkflowAttestation(workflow_id="wf_001")
        workflow.add_step(LinkAttestation(name="step_a"))
        workflow.add_step(LinkAttestation(name="step_b"))

        step = workflow.get_step("step_b")
        assert step is not None
        assert step.name == "step_b"

    def test_get_step_not_found(self):
        """Test get_step returns None for missing step."""
        workflow = WorkflowAttestation(workflow_id="wf_001")
        workflow.add_step(LinkAttestation(name="step_a"))

        assert workflow.get_step("nonexistent") is None

    def test_get_step_by_id(self):
        """Test get_step_by_id finds step by ID."""
        workflow = WorkflowAttestation(workflow_id="wf_001")
        step_a = LinkAttestation(name="step_a", step_id="id_123")
        workflow.add_step(step_a)

        found = workflow.get_step_by_id("id_123")
        assert found is not None
        assert found.name == "step_a"

    def test_get_step_by_id_not_found(self):
        """Test get_step_by_id returns None for missing ID."""
        workflow = WorkflowAttestation(workflow_id="wf_001")
        workflow.add_step(LinkAttestation(name="step_a", step_id="id_123"))

        assert workflow.get_step_by_id("wrong_id") is None

    def test_get_all_materials(self):
        """Test get_all_materials returns unique materials."""
        workflow = WorkflowAttestation(workflow_id="wf_001")

        step1 = LinkAttestation(name="step1")
        step1.add_material("m1", digest={"sha256": "h1"})

        step2 = LinkAttestation(name="step2")
        step2.add_material("m1", digest={"sha256": "h1"})  # Duplicate
        step2.add_material("m2", digest={"sha256": "h2"})

        workflow.add_step(step1)
        workflow.add_step(step2)

        materials = workflow.get_all_materials()
        assert len(materials) == 2  # Deduplicated

    def test_get_all_products(self):
        """Test get_all_products returns unique products."""
        workflow = WorkflowAttestation(workflow_id="wf_001")

        step1 = LinkAttestation(name="step1")
        step1.add_product("p1", digest={"sha256": "h1"})

        step2 = LinkAttestation(name="step2")
        step2.add_product("p1", digest={"sha256": "h1"})  # Duplicate
        step2.add_product("p2", digest={"sha256": "h2"})

        workflow.add_step(step1)
        workflow.add_step(step2)

        products = workflow.get_all_products()
        assert len(products) == 2  # Deduplicated

    def test_get_final_products(self):
        """Test get_final_products returns last step's products."""
        workflow = WorkflowAttestation(workflow_id="wf_001")

        step1 = LinkAttestation(name="step1")
        step1.add_product("intermediate", digest={"sha256": "h1"})
        workflow.add_step(step1)

        step2 = LinkAttestation(name="step2")
        step2.add_product("final_output", digest={"sha256": "h2"})
        workflow.add_step(step2)

        final = workflow.get_final_products()
        assert len(final) == 1
        assert final[0].name == "final_output"

    def test_get_final_products_empty_workflow(self):
        """Test get_final_products on empty workflow."""
        workflow = WorkflowAttestation(workflow_id="wf_empty")

        assert workflow.get_final_products() == []

    def test_workflow_fail(self):
        """Test fail() method sets status and completed_at."""
        workflow = WorkflowAttestation(workflow_id="wf_001")
        workflow.add_step(LinkAttestation(name="step"))

        workflow.fail(reason="Test failure")

        assert workflow.status == "failed"
        assert workflow.completed_at is not None
        assert workflow.is_complete == True


class TestChainVerificationResult:
    """Tests for ChainVerificationResult."""

    def test_to_dict_valid_chain(self):
        """Test to_dict for valid chain result."""
        result = ChainVerificationResult(
            is_valid=True,
            verified_handoffs=3,
            total_handoffs=3,
        )
        d = result.to_dict()

        assert d["isValid"] == True
        assert d["verifiedHandoffs"] == 3
        assert d["totalHandoffs"] == 3
        assert d["breaks"] == []

    def test_add_break_sets_invalid(self):
        """Test add_break sets is_valid to False."""
        result = ChainVerificationResult(
            is_valid=True,
            verified_handoffs=0,
            total_handoffs=2,
        )

        result.add_break(
            from_step="step1",
            to_step="step2",
            missing_material="data.txt",
            message="Material not found in products",
        )

        assert result.is_valid == False
        assert len(result.breaks) == 1
        assert result.breaks[0]["fromStep"] == "step1"
        assert result.breaks[0]["toStep"] == "step2"
        assert result.breaks[0]["missingMaterial"] == "data.txt"


class TestWorkflowVerificationResult:
    """Tests for WorkflowVerificationResult."""

    def test_to_dict(self):
        """Test WorkflowVerificationResult.to_dict()."""
        from src.attestation.workflow import (
            ChainVerificationResult,
            WorkflowVerificationResult,
        )

        chain_result = ChainVerificationResult(
            is_valid=True,
            verified_handoffs=2,
            total_handoffs=2,
        )
        policy_result = PolicyResult(passed=True)

        wf_result = WorkflowVerificationResult(
            workflow_id="wf_test",
            is_valid=True,
            chain_result=chain_result,
            policy_result=policy_result,
            step_count=3,
        )

        d = wf_result.to_dict()

        assert d["workflowId"] == "wf_test"
        assert d["isValid"] == True
        assert d["stepCount"] == 3
        assert "verifiedAt" in d
        assert d["chain"]["verifiedHandoffs"] == 2
        assert d["policy"]["passed"] == True


class TestAttestationVerifier:
    """Tests for AttestationVerifier."""

    def test_verify_link_basic(self):
        verifier = AttestationVerifier()

        link = LinkAttestation(name="test")
        link.add_material("in", digest={"sha256": "abc"})
        link.add_product("out", digest={"sha256": "def"})

        result = verifier.verify_link(link)

        assert result.is_valid == True
        assert result.link_name == "test"

    def test_verify_link_content_hash(self):
        verifier = AttestationVerifier()

        link = LinkAttestation(name="test", step_id="fixed_id")
        expected_hash = link.content_hash()

        result = verifier.verify_link(link, expected_hash=expected_hash)

        assert result.is_valid == True
        assert result.content_hash_valid == True

    def test_verify_chain(self):
        verifier = AttestationVerifier()

        link1 = LinkAttestation(name="s1")
        link1.add_product("p1", digest={"sha256": "h1"})

        link2 = LinkAttestation(name="s2")
        link2.add_material("m1", digest={"sha256": "h1"})
        link2.add_product("p2", digest={"sha256": "h2"})

        result = verifier.verify_chain([link1, link2])

        assert result.is_valid == True
        assert result.verified_handoffs == 1

    def test_verify_links_batch(self):
        """Test batch verification of multiple links."""
        verifier = AttestationVerifier()

        link1 = LinkAttestation(name="step1", step_id="s1")
        link1.add_material("in1", digest={"sha256": "abc"})

        link2 = LinkAttestation(name="step2", step_id="s2")
        link2.add_product("out2", digest={"sha256": "def"})

        link3 = LinkAttestation(name="step3", step_id="s3")

        results = verifier.verify_links([link1, link2, link3])

        assert len(results) == 3
        assert all(r.is_valid for r in results)
        assert results[0].link_name == "step1"
        assert results[1].link_name == "step2"
        assert results[2].link_name == "step3"

    def test_verify_links_with_expected_hashes(self):
        """Test batch verification with expected content hashes."""
        verifier = AttestationVerifier()

        link1 = LinkAttestation(name="step1", step_id="s1")
        link2 = LinkAttestation(name="step2", step_id="s2")

        expected_hashes = {
            "s1": link1.content_hash(),  # Correct hash
            "s2": "wrong_hash",  # Wrong hash
        }

        results = verifier.verify_links([link1, link2], expected_hashes)

        assert results[0].is_valid == True
        assert results[0].content_hash_valid == True
        assert results[1].is_valid == False
        assert results[1].content_hash_valid == False


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_create_link_from_capsules(self):
        link = create_link_from_capsules(
            step_name="inference",
            input_capsules=[("caps_in", "sha256:abc")],
            output_capsules=[("caps_out", "sha256:def")],
            command=["python", "infer.py"],
        )

        assert link.name == "inference"
        assert len(link.materials) == 1
        assert len(link.products) == 1
        assert link.command == ["python", "infer.py"]

    def test_build_workflow_from_capsule_chain(self):
        chain = [
            {
                "capsule_id": "caps_1",
                "content_hash": "sha256:h1",
                "step_name": "capture",
            },
            {
                "capsule_id": "caps_2",
                "content_hash": "sha256:h2",
                "step_name": "process",
            },
            {
                "capsule_id": "caps_3",
                "content_hash": "sha256:h3",
                "step_name": "verify",
            },
        ]

        workflow = build_workflow_from_capsule_chain("wf_test", chain)

        assert workflow.workflow_id == "wf_test"
        assert len(workflow.steps) == 3
        assert workflow.steps[0].name == "capture"
        assert workflow.steps[1].name == "process"
        assert workflow.steps[2].name == "verify"

        # Verify chain is valid
        result = workflow.verify_chain()
        assert result.is_valid == True

    def test_compute_digest(self):
        data = {"key": "value", "nested": {"a": 1}}
        digest = compute_digest(data)

        # Should be deterministic
        assert digest == compute_digest(data)
        assert len(digest) == 64  # SHA256 hex

    def test_compute_digest_bytes_input(self):
        """Test compute_digest with bytes input."""
        data = b"raw bytes content"
        digest = compute_digest(data)

        assert len(digest) == 64
        assert digest == compute_digest(data)  # Deterministic

    def test_compute_digest_string_input(self):
        """Test compute_digest with string input."""
        data = "plain string"
        digest = compute_digest(data)

        assert len(digest) == 64
        # String should be UTF-8 encoded
        assert digest == compute_digest(data.encode("utf-8"))

    def test_compute_digest_sha384(self):
        """Test compute_digest with SHA384 algorithm."""
        data = {"test": "data"}
        digest = compute_digest(data, algorithm="sha384")

        assert len(digest) == 96  # SHA384 is 96 hex chars

    def test_compute_digest_sha512(self):
        """Test compute_digest with SHA512 algorithm."""
        data = {"test": "data"}
        digest = compute_digest(data, algorithm="sha512")

        assert len(digest) == 128  # SHA512 is 128 hex chars

    def test_compute_digest_unsupported_algorithm(self):
        """Test compute_digest raises for unsupported algorithm."""
        data = {"test": "data"}
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            compute_digest(data, algorithm="md5")

    def test_compute_digest_canonical_json(self):
        """Test that dict keys are sorted for deterministic output."""
        # Different key order should produce same digest
        data1 = {"z": 1, "a": 2, "m": 3}
        data2 = {"a": 2, "m": 3, "z": 1}

        assert compute_digest(data1) == compute_digest(data2)


class TestRealWorldScenario:
    """Test realistic workflow scenarios."""

    def test_ai_review_pipeline(self):
        """
        Simulate: Model Inference -> Human Review -> Final Approval

        This is the core use case: proving that AI output went through review.
        """
        policy = SimplePolicy(
            name="ai_review_policy",
            required_steps=["model_inference", "human_review", "final_approval"],
            step_order=["model_inference", "human_review", "final_approval"],
        )

        workflow = WorkflowAttestation(
            workflow_id="wf_ai_review_001",
            name="AI Review Pipeline",
            policy=policy,
        )

        # Step 1: Model produces inference result
        inference = LinkAttestation(name="model_inference")
        inference.add_capsule_material("prompt_caps_001", "sha256:prompt_hash")
        inference.add_capsule_product("inference_caps_002", "sha256:inference_hash")
        inference.byproducts = {
            "model": "claude-3",
            "confidence": 0.95,
        }
        workflow.add_step(inference)

        # Step 2: Human reviews inference
        review = LinkAttestation(name="human_review")
        review.add_capsule_material("inference_caps_002", "sha256:inference_hash")
        review.add_capsule_product("reviewed_caps_003", "sha256:reviewed_hash")
        review.byproducts = {
            "reviewer": "human@example.com",
            "decision": "approved_with_edits",
        }
        workflow.add_step(review)

        # Step 3: Final approval
        approval = LinkAttestation(name="final_approval")
        approval.add_capsule_material("reviewed_caps_003", "sha256:reviewed_hash")
        approval.add_capsule_product("final_caps_004", "sha256:final_hash")
        approval.byproducts = {
            "approver": "manager@example.com",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        workflow.add_step(approval)

        workflow.complete()

        # Verify entire workflow
        result = workflow.verify()

        assert result.is_valid == True
        assert result.chain_result.is_valid == True
        assert result.chain_result.verified_handoffs == 2
        assert result.policy_result.passed == True
        assert workflow.status == "completed"

    def test_tampered_chain_detection(self):
        """
        Simulate tampering: someone modifies intermediate capsule.

        The chain verification should detect the hash mismatch.
        """
        workflow = WorkflowAttestation(workflow_id="wf_tampered")

        # Step 1: Original inference
        step1 = LinkAttestation(name="inference")
        step1.add_capsule_product("caps_mid", "sha256:original_hash")
        workflow.add_step(step1)

        # Step 2: Claims to consume caps_mid, but with different hash
        # (simulating that caps_mid was modified after step 1)
        step2 = LinkAttestation(name="review")
        step2.add_capsule_material("caps_mid", "sha256:TAMPERED_hash")
        step2.add_capsule_product("caps_final", "sha256:final_hash")
        workflow.add_step(step2)

        result = workflow.verify()

        # Should detect the tampering
        assert result.is_valid == False
        assert result.chain_result.is_valid == False
        assert len(result.chain_result.breaks) == 1
        assert "inference" in result.chain_result.breaks[0]["fromStep"]
        assert "review" in result.chain_result.breaks[0]["toStep"]


class TestAttestationValidity:
    """Tests for AttestationValidity time-bounded trust."""

    def test_create_validity(self):
        validity = AttestationValidity()
        assert validity.issued_at is not None
        assert validity.not_before is None
        assert validity.not_after is None

    def test_create_with_ttl(self):
        validity = AttestationValidity.create_with_ttl(3600)  # 1 hour
        assert validity.not_before is not None
        assert validity.not_after is not None
        assert validity.is_valid_at() == True

    def test_is_valid_at_current_time(self):
        validity = AttestationValidity.create_with_ttl(3600)
        assert validity.is_valid_at() == True

    def test_not_yet_valid(self):
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        future = now + timedelta(hours=1)

        validity = AttestationValidity(
            issued_at=now,
            not_before=future,
        )
        assert validity.is_valid_at(now) == False
        assert validity.is_valid_at(future + timedelta(seconds=1)) == True

    def test_expired(self):
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        past = now - timedelta(hours=1)

        validity = AttestationValidity(
            issued_at=past,
            not_before=past,
            not_after=past + timedelta(minutes=30),  # Expired 30 min ago
        )
        assert validity.is_expired() == True
        assert validity.is_valid_at() == False

    def test_remaining_validity_seconds(self):
        validity = AttestationValidity.create_with_ttl(3600)
        remaining = validity.remaining_validity_seconds()
        assert remaining is not None
        assert 3500 < remaining <= 3600

    def test_remaining_validity_no_expiry(self):
        validity = AttestationValidity()
        assert validity.remaining_validity_seconds() is None

    def test_to_dict_from_dict(self):
        original = AttestationValidity.create_with_ttl(3600)
        d = original.to_dict()

        assert "issuedAt" in d
        assert "notBefore" in d
        assert "notAfter" in d

        restored = AttestationValidity.from_dict(d)
        assert restored.issued_at == original.issued_at
        assert restored.not_before == original.not_before
        assert restored.not_after == original.not_after


class TestLinkVerificationResult:
    """Tests for LinkVerificationResult serialization."""

    def test_to_dict_basic(self):
        from src.attestation.verification import LinkVerificationResult

        result = LinkVerificationResult(
            link_name="test_step",
            step_id="s1",
            is_valid=True,
        )
        d = result.to_dict()

        assert d["linkName"] == "test_step"
        assert d["stepId"] == "s1"
        assert d["isValid"] == True
        assert d["errors"] == []
        assert d["warnings"] == []
        # signature_valid and content_hash_valid should be omitted when None
        assert "signatureValid" not in d
        assert "contentHashValid" not in d

    def test_to_dict_with_signature_info(self):
        from src.attestation.verification import LinkVerificationResult

        result = LinkVerificationResult(
            link_name="signed_step",
            step_id="s2",
            is_valid=True,
            signature_valid=True,
            content_hash_valid=True,
        )
        d = result.to_dict()

        assert d["signatureValid"] == True
        assert d["contentHashValid"] == True

    def test_to_dict_with_errors(self):
        from src.attestation.verification import LinkVerificationResult

        result = LinkVerificationResult(
            link_name="failed_step",
            step_id="s3",
            is_valid=False,
            signature_valid=False,
            errors=["Signature verification failed"],
            warnings=["Missing digest for material 'input.txt'"],
        )
        d = result.to_dict()

        assert d["isValid"] == False
        assert "Signature verification failed" in d["errors"]
        assert len(d["warnings"]) == 1


class TestVerifierEdgeCases:
    """Edge case tests for AttestationVerifier."""

    def test_verify_chain_empty_list(self):
        verifier = AttestationVerifier()
        result = verifier.verify_chain([])

        assert result.is_valid == True
        assert result.verified_handoffs == 0
        assert result.total_handoffs == 0

    def test_verify_chain_single_link(self):
        verifier = AttestationVerifier()

        link = LinkAttestation(name="only_step")
        link.add_product("output", digest={"sha256": "abc123"})

        result = verifier.verify_chain([link])

        assert result.is_valid == True
        assert result.verified_handoffs == 0
        assert result.total_handoffs == 0

    def test_verify_workflow_combines_chain_and_policy(self):
        verifier = AttestationVerifier()

        workflow = WorkflowAttestation(
            workflow_id="wf_verify_test",
            policy=PERMISSIVE_POLICY,
        )

        link1 = LinkAttestation(name="capture")
        link1.add_product("data", digest={"sha256": "h1"})

        link2 = LinkAttestation(name="process")
        link2.add_material("input", digest={"sha256": "h1"})
        link2.add_product("result", digest={"sha256": "h2"})

        workflow.add_step(link1)
        workflow.add_step(link2)

        result = verifier.verify_workflow(workflow)

        assert result.workflow_id == "wf_verify_test"
        assert result.is_valid == True
        assert result.step_count == 2
        assert result.chain_result.is_valid == True
        assert result.policy_result.passed == True


class TestHelperFunctionEdgeCases:
    """Edge case tests for helper functions."""

    def test_create_link_from_capsules_empty_inputs(self):
        link = create_link_from_capsules(
            step_name="no_inputs",
            input_capsules=[],
            output_capsules=[("caps_out", "sha256:def")],
        )

        assert len(link.materials) == 0
        assert len(link.products) == 1

    def test_create_link_from_capsules_with_byproducts(self):
        link = create_link_from_capsules(
            step_name="with_byproducts",
            input_capsules=[("caps_in", "sha256:abc")],
            output_capsules=[("caps_out", "sha256:def")],
            byproducts={"log": "processing took 100ms", "exit_code": 0},
        )

        assert link.byproducts["log"] == "processing took 100ms"
        assert link.byproducts["exit_code"] == 0

    def test_build_workflow_default_step_names(self):
        chain = [
            {"capsule_id": "caps_1", "content_hash": "sha256:h1"},
            {"capsule_id": "caps_2", "content_hash": "sha256:h2"},
        ]

        workflow = build_workflow_from_capsule_chain("wf_default", chain)

        assert workflow.steps[0].name == "step_0"
        assert workflow.steps[1].name == "step_1"

    def test_build_workflow_with_custom_policy(self):
        chain = [{"capsule_id": "caps_1", "content_hash": "sha256:h1"}]

        workflow = build_workflow_from_capsule_chain(
            "wf_strict",
            chain,
            policy=STRICT_POLICY,
        )

        assert workflow.policy == STRICT_POLICY
