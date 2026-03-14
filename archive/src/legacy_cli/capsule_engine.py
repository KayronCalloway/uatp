import os
import uuid

from dateutil import parser

from crypto_utils import hash_capsule_dict, sign_capsule, verify_capsule
from src.capsule_schema import Capsule

CAPSULES_DIR = "capsules"
os.makedirs(CAPSULES_DIR, exist_ok=True)

SIGNING_KEY_HEX = os.environ.get("UATP_SIGNING_KEY")  # Set this in your env
VERIFY_KEY_HEX = os.environ.get("UATP_VERIFY_KEY")  # Set this in your env

CAPSULE_TYPES = ["refusal", "introspective", "joint"]


def create_capsule():
    capsule_id = str(uuid.uuid4())
    capsule_type = input(f"Capsule type {CAPSULE_TYPES}: ").strip().lower()
    assert capsule_type in CAPSULE_TYPES, f"Type must be one of {CAPSULE_TYPES}"
    timestamp = Capsule.now_iso()
    input_data = input("Input: ")
    output = input("Output: ")
    reasoning = input("Reasoning: ")
    model_version = input("Model version: ")
    parent_capsule = input("Parent capsule ID (optional): ") or None

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
    capsule_hash = hash_capsule_dict(capsule_dict)
    capsule.hash = capsule_hash
    if SIGNING_KEY_HEX:
        capsule.signature = sign_capsule(capsule_hash, SIGNING_KEY_HEX)
    else:
        capsule.signature = None
    filename = os.path.join(CAPSULES_DIR, f"{capsule_id}.json")
    with open(filename, "w") as f:
        f.write(capsule.to_json())
    print(f"Capsule written to {filename}\n{capsule.to_json()}")


def verify_capsule_file(filename):
    with open(filename) as f:
        capsule = Capsule.from_json(f.read())
    capsule_dict = capsule.to_dict()
    capsule_hash = hash_capsule_dict(capsule_dict)
    valid_hash = capsule.hash == capsule_hash
    valid_sig = None
    if capsule.signature and VERIFY_KEY_HEX:
        valid_sig = verify_capsule(capsule.hash, capsule.signature, VERIFY_KEY_HEX)
    print(
        f"Capsule ID: {capsule.capsule_id}\nHash valid: {valid_hash}\nSignature valid: {valid_sig}"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="UATP Capsule Engine CLI")
    parser.add_argument("--create", action="store_true", help="Create a new capsule")
    parser.add_argument("--verify", type=str, help="Verify a capsule file")
    args = parser.parse_args()

    if args.create:
        create_capsule()
    elif args.verify:
        verify_capsule_file(args.verify)
    else:
        parser.print_help()
