"""Content-addressed artifact storage tests for agent receipts."""

from __future__ import annotations

import json

import pytest

from src.agent_receipts.artifacts import (
    ArtifactStore,
    sha256_bytes_digest,
    verify_artifact_ref,
)


def test_store_bytes_writes_content_addressed_artifact_and_ref(tmp_path) -> None:
    store = ArtifactStore(tmp_path)
    content = b"tool output\n"

    ref = store.store_bytes(
        content, media_type="text/plain", redaction={"status": "none"}
    )

    expected_digest = sha256_bytes_digest(content)
    assert ref.digest == expected_digest
    assert ref.size == len(content)
    assert ref.media_type == "text/plain"
    assert ref.redaction == {"status": "none"}
    assert (
        ref.path
        == f"sha256/{expected_digest.removeprefix('sha256:')[:2]}/{expected_digest.removeprefix('sha256:')}"
    )
    assert (tmp_path / ref.path).read_bytes() == content
    assert verify_artifact_ref(tmp_path, ref) is True


def test_store_json_uses_canonical_json_bytes_for_stable_digest(tmp_path) -> None:
    store = ArtifactStore(tmp_path)

    first = store.store_json({"b": 2, "a": 1}, media_type="application/json")
    second = store.store_json({"a": 1, "b": 2}, media_type="application/json")

    assert first.digest == second.digest
    assert first.path == second.path
    assert json.loads((tmp_path / first.path).read_text()) == {"a": 1, "b": 2}


def test_store_bytes_deduplicates_identical_content_without_rewriting(tmp_path) -> None:
    store = ArtifactStore(tmp_path)
    ref = store.store_bytes(b"same", media_type="text/plain")
    artifact_path = tmp_path / ref.path
    first_mtime_ns = artifact_path.stat().st_mtime_ns

    ref_again = store.store_bytes(b"same", media_type="text/plain")

    assert ref_again.digest == ref.digest
    assert artifact_path.stat().st_mtime_ns == first_mtime_ns


def test_verify_artifact_ref_rejects_tampered_or_missing_artifacts(tmp_path) -> None:
    store = ArtifactStore(tmp_path)
    ref = store.store_bytes(b"original", media_type="text/plain")
    (tmp_path / ref.path).write_bytes(b"changed")

    assert verify_artifact_ref(tmp_path, ref) is False

    (tmp_path / ref.path).unlink()
    assert verify_artifact_ref(tmp_path, ref) is False


def test_store_rejects_artifacts_outside_store_root(tmp_path) -> None:
    store = ArtifactStore(tmp_path)
    ref = store.store_bytes(b"safe", media_type="text/plain")
    malicious_ref = type(ref)(
        digest=ref.digest,
        path="../escape",
        size=ref.size,
        media_type=ref.media_type,
        redaction=ref.redaction,
    )

    with pytest.raises(ValueError, match="artifact path escapes store root"):
        verify_artifact_ref(tmp_path, malicious_ref)
