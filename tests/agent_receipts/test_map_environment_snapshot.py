from datetime import datetime, timezone

import pytest

from src.agent_receipts.events import EnvironmentSnapshotEvent
from src.agent_receipts.hashing import sha256_digest
from src.agent_receipts.mappers import (
    map_environment_snapshot_event_to_environment_snapshot_capsule,
)


def ts() -> datetime:
    return datetime(2026, 5, 8, 21, 14, 0, tzinfo=timezone.utc)


def env_event(**payload_overrides) -> EnvironmentSnapshotEvent:
    payload = {
        "snapshot_id": "env_001",
        "working_directory": "/Users/kay/uatp-capsule-engine",
        "env_vars": {"PATH": "/usr/bin", "ANTHROPIC_API_KEY": "secret"},
        "git_branch": "main",
        "git_commit_hash": "abc123",
        "git_dirty": True,
        "open_files": ["src/agent_receipts/mappers.py"],
        "system_load": 1.25,
        "memory_available_gb": 12.5,
        "agent_framework": {"name": "hermes", "version": "0.8.0"},
        "adapter": {"name": "hermes", "version": "0.1.0"},
        "model_provider": "anthropic",
        "model": "claude-sonnet-4",
        "enabled_tools": ["terminal", "file"],
        "enabled_toolsets": ["terminal", "file"],
        "loaded_skills": [
            {"name": "test-driven-development", "content_hash": "sha256:skill"}
        ],
        "memory_provider_state": {"backend": "sqlite", "entries": 4},
        "mcp_servers": [{"name": "filesystem", "transport": "stdio"}],
        "platform": "cli",
        "gateway_source": "local",
        "terminal_backend": "local",
        "config": {"model": "claude-sonnet-4", "api_key": "secret"},
    }
    payload.update(payload_overrides)
    return EnvironmentSnapshotEvent(
        event_id="evt_env_001",
        session_id="sess_001",
        adapter_name="hermes",
        agent_name="Hermes Agent",
        timestamp=ts(),
        parent_event_hash="sha256:parent",
        actor="assistant",
        payload=payload,
        redaction_summary={"secrets_removed": 2},
        trust_level="local",
    )


def test_environment_snapshot_maps_runtime_state_and_hashes_sensitive_state() -> None:
    event = env_event()

    capsule = map_environment_snapshot_event_to_environment_snapshot_capsule(event)

    assert capsule["capsule_type"] == "environment_snapshot"
    assert capsule["payload_key"] == "environment_snapshot"
    assert capsule["environment_snapshot"] == {
        "snapshot_id": "env_001",
        "session_id": "sess_001",
        "working_directory": "/Users/kay/uatp-capsule-engine",
        "env_vars_hash": sha256_digest(
            {"PATH": "/usr/bin", "ANTHROPIC_API_KEY": "[REDACTED]"}
        ),
        "git_branch": "main",
        "git_commit_hash": "abc123",
        "git_dirty": True,
        "open_files": ["src/agent_receipts/mappers.py"],
        "system_load": 1.25,
        "memory_available_gb": 12.5,
        "timestamp": "2026-05-08T21:14:00+00:00",
    }
    metadata = capsule["receipt_metadata"]
    assert metadata["agent_framework"] == {"name": "hermes", "version": "0.8.0"}
    assert metadata["adapter"] == {"name": "hermes", "version": "0.1.0"}
    assert metadata["model_provider"] == "anthropic"
    assert metadata["model"] == "claude-sonnet-4"
    assert metadata["enabled_tools"] == ["terminal", "file"]
    assert metadata["enabled_toolsets"] == ["terminal", "file"]
    assert metadata["loaded_skills"] == [
        {"name": "test-driven-development", "content_hash": "sha256:skill"}
    ]
    assert metadata["memory_provider_state_hash"] == sha256_digest(
        {"backend": "sqlite", "entries": 4}
    )
    assert metadata["mcp_servers"] == [{"name": "filesystem", "transport": "stdio"}]
    assert metadata["platform"] == "cli"
    assert metadata["gateway_source"] == "local"
    assert metadata["terminal_backend"] == "local"
    assert metadata["config_hash"] == sha256_digest(
        {"model": "claude-sonnet-4", "api_key": "[REDACTED]"}
    )
    assert metadata["parent_event_hash"] == "sha256:parent"


def test_environment_snapshot_uses_provided_hashes_without_raw_state() -> None:
    event = env_event(
        env_vars=None,
        env_vars_hash="sha256:" + "a" * 64,
        config=None,
        config_hash="sha256:" + "b" * 64,
    )

    capsule = map_environment_snapshot_event_to_environment_snapshot_capsule(event)

    assert capsule["environment_snapshot"]["env_vars_hash"] == "sha256:" + "a" * 64
    assert capsule["receipt_metadata"]["config_hash"] == "sha256:" + "b" * 64


def test_environment_snapshot_rejects_malformed_provided_hash() -> None:
    event = env_event(env_vars=None, env_vars_hash="not-a-digest")

    with pytest.raises(ValueError, match="sha256"):
        map_environment_snapshot_event_to_environment_snapshot_capsule(event)


def test_environment_snapshot_rejects_missing_env_state() -> None:
    event = env_event(env_vars=None, env_vars_hash=None)

    with pytest.raises(ValueError, match="env_vars"):
        map_environment_snapshot_event_to_environment_snapshot_capsule(event)


def test_environment_snapshot_omits_unavailable_memory_provider_state_hash() -> None:
    event = env_event(memory_provider_state=None, memory_provider_state_hash=None)

    capsule = map_environment_snapshot_event_to_environment_snapshot_capsule(event)

    assert capsule["receipt_metadata"]["memory_provider_state_hash"] is None


def test_environment_snapshot_rejects_loaded_skill_without_content_hash() -> None:
    event = env_event(loaded_skills=[{"name": "test-driven-development"}])

    with pytest.raises(ValueError, match="content_hash"):
        map_environment_snapshot_event_to_environment_snapshot_capsule(event)


def test_environment_snapshot_redacts_mcp_server_secret_metadata() -> None:
    event = env_event(
        mcp_servers=[
            {
                "name": "remote",
                "headers": {"Authorization": "Bearer secret"},
                "env": {"API_TOKEN": "secret"},
            }
        ]
    )

    capsule = map_environment_snapshot_event_to_environment_snapshot_capsule(event)

    assert capsule["receipt_metadata"]["mcp_servers"] == [
        {
            "name": "remote",
            "headers": {"Authorization": "[REDACTED]"},
            "env": {"API_TOKEN": "[REDACTED]"},
        }
    ]


def test_environment_snapshot_rejects_missing_snapshot_id() -> None:
    event = env_event(snapshot_id=None)

    with pytest.raises(ValueError, match="snapshot_id"):
        map_environment_snapshot_event_to_environment_snapshot_capsule(event)
