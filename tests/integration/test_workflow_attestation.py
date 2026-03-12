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
