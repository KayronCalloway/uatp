"""
Tests for fork simulation and chain merging functionality in the UATP Capsule Engine.
"""

import pytest
from crud import capsule as capsule_crud
from engine.capsule_engine import CapsuleEngine


@pytest.mark.asyncio
async def test_fork_and_merge(setup_database, monkeypatch):
    """Test creating a fork, developing two branches, and merging them."""
    # 1. Setup engine
    monkeypatch.setenv("UATP_AGENT_ID", "test-fork-agent")
    monkeypatch.setenv(
        "UATP_SIGNING_KEY",
        "d6f0f8e9c9a2a5b3d8d1f4e0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
    )
    engine = CapsuleEngine(db=setup_database)

    # 2. Create a base chain
    capsule1 = await engine.create_capsule_async("Base", "in1", "out1", "r1", "v1")
    capsule2 = await engine.create_capsule_async(
        "Base", "in2", "out2", "r2", "v1", parent_capsule=capsule1.capsule_id
    )

    # 3. Create two divergent branches from capsule2
    branch1_head = await engine.create_capsule_async(
        "Branch1", "in3a", "out3a", "r3a", "v1", parent_capsule=capsule2.capsule_id
    )

    branch2_head = await engine.create_capsule_async(
        "Branch2", "in3b", "out3b", "r3b", "v1", parent_capsule=capsule2.capsule_id
    )

    # 4. Merge the two branches
    merge_capsule = await engine.merge_chains_async(
        head1_id=branch1_head.capsule_id, head2_id=branch2_head.capsule_id
    )

    # 5. Verify the merge
    assert merge_capsule is not None
    assert merge_capsule.capsule_type == "Merge"
    assert branch1_head.capsule_id in merge_capsule.metadata["merged_from_ids"]
    assert branch2_head.capsule_id in merge_capsule.metadata["merged_from_ids"]

    # Verify the final chain structure in the database
    db_capsules = await capsule_crud.get_capsules_async(setup_database, limit=-1)
    assert len(db_capsules) == 5  # base1, base2, branch1, branch2, merge

    merge_db_entry = await capsule_crud.get_capsule_async(
        setup_database, merge_capsule.capsule_id
    )
    assert merge_db_entry is not None

    # The parent of the merge capsule should be the winner of the conflict resolution
    # which is based on timestamp in the current simplified implementation.
    # We expect branch2_head to be the winner as it was created later.
    assert merge_db_entry.parent_capsule == branch2_head.capsule_id
