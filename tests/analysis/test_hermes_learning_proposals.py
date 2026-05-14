from scripts.analysis.hermes_failure_taxonomy import CorrectionChain
from scripts.analysis.hermes_learning_proposals import generate_learning_proposals


def make_chain(capsule_id, correction="fix that"):
    return CorrectionChain(
        prompt="Please inspect UATP.",
        rejected_response="Long explanation. " * 120,
        correction=correction,
        chosen_response="Fixed and verified.",
        source_capsule_id=capsule_id,
        step_indices={
            "prompt": 0,
            "rejected_response": 1,
            "correction": 2,
            "chosen_response": 3,
        },
    )


def test_generates_memory_proposal_only_with_three_evidence_chains():
    proposals = generate_learning_proposals(
        [make_chain("cap-1"), make_chain("cap-2"), make_chain("cap-3")]
    )

    memory = [p for p in proposals if p["type"] == "memory"]
    assert memory
    assert memory[0]["safe_to_apply"] is False
    assert len(memory[0]["evidence"]) == 3
    assert "Kay's" in memory[0]["content"]


def test_does_not_generate_memory_proposal_with_insufficient_evidence():
    proposals = generate_learning_proposals([make_chain("cap-1"), make_chain("cap-2")])

    assert [p for p in proposals if p["type"] == "memory"] == []


def test_generates_skill_patch_for_repeated_local_file_blindness():
    proposals = generate_learning_proposals(
        [
            make_chain("cap-1", "n can you see uatp?"),
            make_chain("cap-2", "its a file locally"),
        ]
    )

    patches = [p for p in proposals if p["type"] == "skill_patch"]
    assert patches
    assert patches[0]["safe_to_apply"] is False
    assert patches[0]["skill"] == "uatp-capsule-mining"
