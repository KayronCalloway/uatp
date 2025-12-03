import os
import uuid
from datetime import datetime, timedelta

from capsule_schema import Capsule
from crypto_utils import hash_capsule_dict

CAPSULES_DIR = "capsules"
os.makedirs(CAPSULES_DIR, exist_ok=True)


# Mock data for a simple capsule chain (3 capsules: refusal -> introspective -> joint)
def make_mock_capsule(
    capsule_type,
    input_data,
    output,
    reasoning,
    model_version,
    parent_capsule=None,
    dt=None,
):
    capsule_id = str(uuid.uuid4())
    timestamp = (dt or datetime.utcnow()).isoformat() + "Z"
    capsule = Capsule(
        capsule_id=capsule_id,
        capsule_type=capsule_type,
        timestamp=timestamp,
        input_data=input_data,
        output=output,
        reasoning=reasoning,
        model_version=model_version,
        parent_capsule=parent_capsule,
    )
    capsule_dict = capsule.to_dict()
    capsule.hash = hash_capsule_dict(capsule_dict)
    return capsule


def create_mock_chain():
    base_time = datetime.utcnow()
    # Capsule 1: Refusal
    cap1 = make_mock_capsule(
        capsule_type="refusal",
        input_data="Should I approve this transaction?",
        output="No, it violates rule X.",
        reasoning="Confidence 0.82. Prior similar case triggered risk rule 3b.",
        model_version="gpt-4-2024-06",
        parent_capsule=None,
        dt=base_time,
    )
    # Capsule 2: Introspective
    cap2 = make_mock_capsule(
        capsule_type="introspective",
        input_data="Why did you refuse?",
        output="Refusal due to risk rule 3b.",
        reasoning="Confidence 0.90. Historical data supports this.",
        model_version="gpt-4-2024-06",
        parent_capsule=cap1.capsule_id,
        dt=base_time + timedelta(seconds=5),
    )
    # Capsule 3: Joint
    cap3 = make_mock_capsule(
        capsule_type="joint",
        input_data="Human review: agree with refusal?",
        output="Human: Yes, confirmed.",
        reasoning="Human-AI consensus. No override.",
        model_version="gpt-4-2024-06",
        parent_capsule=cap2.capsule_id,
        dt=base_time + timedelta(seconds=10),
    )
    # Write capsules to files
    for cap in [cap1, cap2, cap3]:
        fname = os.path.join(CAPSULES_DIR, f"{cap.capsule_id}.json")
        with open(fname, "w") as f:
            f.write(cap.to_json())
        print(f"Wrote {cap.type} capsule: {fname}")
    print("Mock capsule chain created!")


if __name__ == "__main__":
    create_mock_chain()
