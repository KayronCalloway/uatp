import asyncio

import pytest
from engine.capsule_engine import CapsuleEngine
from engine.cqss import build_chain_graph, compute_cqss


@pytest.mark.asyncio
async def test_basic_cqss_metrics(setup_database, monkeypatch):
    monkeypatch.setenv(
        "UATP_SIGNING_KEY",
        "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
    )
    monkeypatch.setenv("UATP_AGENT_ID", "test-agent")
    engine = CapsuleEngine(db=setup_database)

    # Create a small chain
    c1 = await engine.create_capsule_async(
        "Introspective",
        "test input",
        "test output",
        "test reasoning",
        "1.0",
        metadata={"confidence": 0.9, "reasoning_trace": ["r1"], "test": 1},
    )
    c2 = await engine.create_capsule_async(
        "Joint",
        "test input",
        "test output",
        "test reasoning",
        "1.0",
        parent_capsule=c1.capsule_id,
        metadata={"confidence": 0.95, "reasoning_trace": ["r2"], "test": 2},
    )
    c3 = await engine.create_capsule_async(
        "Refusal",
        "test input",
        "test output",
        "test reasoning",
        "1.0",
        parent_capsule=c2.capsule_id,
        metadata={"confidence": 1.0, "reasoning_trace": ["r3"], "test": 3},
    )

    chain = await engine.load_chain_async()

    # Compute CQSS
    result = await compute_cqss(chain, engine.verify_capsule_async)
    d = result.as_dict()

    # Test basic metrics
    assert d["chain_length"] == 3
    assert d["valid_signatures"] == 3
    assert d["unique_agents"] == 1

    # Test there are no forks yet
    assert d["fork_count"] == 0

    # Test we have 1 root and 1 leaf
    assert d["root_count"] == 1
    assert d["leaf_count"] == 1


@pytest.mark.asyncio
async def test_advanced_cqss_metrics(setup_database, monkeypatch):
    monkeypatch.setenv(
        "UATP_SIGNING_KEY",
        "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
    )
    monkeypatch.setenv("UATP_AGENT_ID", "test-agent")
    engine = CapsuleEngine(db=setup_database)

    # Create a chain with a fork
    c1 = await engine.create_capsule_async(
        "Introspective",
        "test input",
        "test output",
        "test reasoning",
        "1.0",
        metadata={"confidence": 0.9, "reasoning_trace": ["Step 1"], "test": 1},
    )

    # Sleep briefly to ensure different timestamps
    await asyncio.sleep(0.01)

    # Create fork 1
    c2a = await engine.create_capsule_async(
        "Joint",
        "test input",
        "test output",
        "test reasoning",
        "1.0",
        parent_capsule=c1.capsule_id,
        metadata={"confidence": 0.95, "reasoning_trace": ["Fork A"], "fork": "A"},
    )
    c3a = await engine.create_capsule_async(
        "Introspective",
        "test input",
        "test output",
        "test reasoning",
        "1.0",
        parent_capsule=c2a.capsule_id,
        metadata={"confidence": 0.85, "reasoning_trace": ["Fork A continued"]},
    )

    # Create fork 2
    c2b = await engine.create_capsule_async(
        "Refusal",
        "test input",
        "test output",
        "test reasoning",
        "1.0",
        parent_capsule=c1.capsule_id,
        metadata={"confidence": 1.0, "reasoning_trace": ["Fork B"], "fork": "B"},
    )

    chain = await engine.load_chain_async()

    # Compute CQSS
    result = await compute_cqss(chain, engine.verify_capsule_async)
    d = result.as_dict()

    # Test fork structure
    assert d["chain_length"] == 4
    assert d["fork_count"] == 1  # c1 has two children
    assert d["root_count"] == 1
    assert d["leaf_count"] == 2  # c3a and c2b are leaves

    # Test advanced metrics
    assert d["integrity_score"] > 0
    assert d["verification_ratio"] > 0
    assert d["trust_score"] > 0
    assert d["complexity_score"] > 0
    assert d["diversity_score"] > 0

    # Test path metrics
    assert d["longest_path"] == 3  # c1 -> c2a -> c3a
    assert d["avg_path_length"] > 0

    # Test capsule type metrics
    assert d["joint_capsule_ratio"] == 0.25  # 1 out of 4
    assert d["introspective_ratio"] == 0.5  # 2 out of 4

    # Test overall score computation
    overall = result.get_overall_score()
    assert overall is not None
    assert 0 <= overall <= 100


@pytest.mark.asyncio
async def test_chain_graph_building(setup_database, monkeypatch):
    monkeypatch.setenv(
        "UATP_SIGNING_KEY",
        "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
    )
    monkeypatch.setenv("UATP_AGENT_ID", "test-agent")
    engine = CapsuleEngine(db=setup_database)

    # Create a simple forked chain
    c1 = await engine.create_capsule_async(
        "Introspective",
        "test input",
        "test output",
        "test reasoning",
        "1.0",
        metadata={"confidence": 0.9, "reasoning_trace": ["root"]},
    )

    c2a = await engine.create_capsule_async(
        "Joint",
        "test input",
        "test output",
        "test reasoning",
        "1.0",
        parent_capsule=c1.capsule_id,
        metadata={"confidence": 0.8, "reasoning_trace": ["branch 1"]},
    )

    c2b = await engine.create_capsule_async(
        "Refusal",
        "test input",
        "test output",
        "test reasoning",
        "1.0",
        parent_capsule=c1.capsule_id,
        metadata={"confidence": 0.7, "reasoning_trace": ["branch 2"]},
    )

    chain = await engine.load_chain_async()

    # Build graph
    G = build_chain_graph(chain)

    # Test graph structure
    assert len(G.nodes) == 3
    assert len(G.edges) == 2
    assert G.has_edge(c1.capsule_id, c2a.capsule_id)
    assert G.has_edge(c1.capsule_id, c2b.capsule_id)

    # Test out-degree of fork point
    assert G.out_degree(c1.capsule_id) == 2
