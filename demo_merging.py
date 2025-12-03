import json
import os

from dotenv import load_dotenv
from engine.capsule_engine import CapsuleEngine


def setup_environment():
    """Load environment variables for the demo."""
    load_dotenv()
    # Set dummy env vars if they don't exist, for demonstration purposes
    if not os.getenv("UATP_AGENT_ID"):
        os.environ["UATP_AGENT_ID"] = "demo-merge-agent"
    if not os.getenv("UATP_SIGNING_KEY"):
        # Use a dummy key for the demo
        from nacl.signing import SigningKey

        os.environ["UATP_SIGNING_KEY"] = (
            SigningKey.generate().encode(encoder=nacl.encoding.HexEncoder).decode()
        )


def main():
    """Demonstrate forking and merging capsule chains."""
    print("=== UATP CHAIN MERGING AND CONFLICT RESOLUTION DEMO ===")
    setup_environment()

    engine = CapsuleEngine()

    # 1. Create a base chain
    print("\n--- Creating Base Chain ---")
    base_capsule_1 = engine.create_capsule(
        capsule_type="Introspective",
        confidence=0.9,
        reasoning_trace=["Initial thought: The sky is blue."],
    )
    base_capsule_2 = engine.create_capsule(
        capsule_type="Introspective",
        confidence=0.95,
        reasoning_trace=["Further reflection: This is due to Rayleigh scattering."],
    )
    base_chain = [base_capsule_1, base_capsule_2]
    print(f"Base chain created with {len(base_chain)} capsules.")

    # 2. Create two divergent forks
    print("\n--- Creating Divergent Forks ---")

    # Fork A: A more confident, detailed reasoning path
    fork_a_capsule = engine.create_capsule(
        capsule_type="Introspective",
        confidence=0.98,
        reasoning_trace=[
            {
                "step_type": "observation",
                "content": "Atmospheric composition is mostly nitrogen and oxygen.",
                "confidence": 0.99,
            },
            {
                "step_type": "inference",
                "content": "Shorter wavelengths (blue/violet) scatter more effectively.",
                "confidence": 0.97,
            },
        ],
        previous_capsule_id=base_capsule_2.capsule_id,
    )
    chain_a = base_chain + [fork_a_capsule]

    # Fork B: A less confident, slightly different reasoning path
    fork_b_capsule = engine.create_capsule(
        capsule_type="Introspective",
        confidence=0.90,
        reasoning_trace=[
            {
                "step_type": "observation",
                "content": "The sky appears blue to the human eye.",
                "confidence": 0.95,
            },
            {
                "step_type": "hypothesis",
                "content": "Perhaps it's because the ocean is blue.",
                "confidence": 0.85,
            },  # Lower quality reasoning
        ],
        previous_capsule_id=base_capsule_2.capsule_id,
    )
    chain_b = base_chain + [fork_b_capsule]

    print("Fork A and Fork B created.")
    print(
        f"Fork A winner reasoning score: {fork_a_capsule.validate_reasoning()['score']}"
    )
    print(
        f"Fork B loser reasoning score: {fork_b_capsule.validate_reasoning()['score']}"
    )

    # 3. Merge the chains
    print("\n--- Merging Chains ---")
    merged_chain = engine.merge_chains(chain_a, chain_b, strategy="cqss_first")
    print("Chains merged successfully.")

    # 4. Display the result
    print("\n--- Final Merged Chain ---")
    for capsule in merged_chain:
        print(json.dumps(capsule.to_dict(), indent=2))

    print("\nDemonstration complete!")


if __name__ == "__main__":
    main()
