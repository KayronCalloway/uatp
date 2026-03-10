import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.capsule_engine import CapsuleEngine

AGENT_ID = "demo-agent"
CHAIN_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "capsule_chain.jsonl")
)
engine = CapsuleEngine(agent_id=AGENT_ID, storage_path=CHAIN_PATH)


# Reset chain file for demo
def reset_chain():
    import os

    try:
        os.remove(CHAIN_PATH)
    except FileNotFoundError:
        pass


reset_chain()

# Create root capsule (Introspective)
root_capsule = engine.create_capsule(
    capsule_type="Introspective",
    confidence=0.91,
    reasoning_trace=[
        "Asked: Should I approve this loan?",
        "Model: No, applicant flagged in credit rule B2.",
    ],
    metadata={"epistemic_frame": "Stoicism", "jurisdiction": "EU"},
)
engine.log_capsule(root_capsule)

# Add Refusal capsule (child)
refusal_capsule = engine.create_capsule(
    capsule_type="Refusal",
    confidence=1.0,
    reasoning_trace=[
        "Request: Delete all patient records.",
        "Model: Request denied due to violation of HIPAA.",
    ],
    metadata={"epistemic_frame": "Legalism", "jurisdiction": "US"},
    reason_for_rejection="HIPAA compliance violation",
    ethical_policy_id="HIPAA-001",
)
engine.log_capsule(refusal_capsule)

# Fork: Perspective capsule (child of root)
perspective_capsule = engine.create_capsule(
    capsule_type="Perspective",
    confidence=0.75,
    reasoning_trace=["Alternative: Consider applicant's appeal."],
    metadata={"epistemic_frame": "Empathy", "jurisdiction": "EU"},
    previous_capsule_id=root_capsule.capsule_id,
)
engine.log_capsule(perspective_capsule)

# Joint capsule (human+AI)
joint_capsule = engine.create_capsule(
    capsule_type="Joint",
    confidence=0.98,
    reasoning_trace=["AI: Recommends approval.", "Human: Agrees, signs."],
    metadata={"epistemic_frame": "Pragmatism", "jurisdiction": "EU"},
    human_signature="human-xyz",
    agreement_terms="Loan approved with conditions.",
    previous_capsule_id=perspective_capsule.capsule_id,
)
engine.log_capsule(joint_capsule)

print("Mock UATP capsule chain with fork and joint capsule created.")
