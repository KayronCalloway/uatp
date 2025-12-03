"""
recorder.py - Capsule recording utility for agent wrappers.
Provides a simple function to record agent interactions as UATP capsules.
"""

import os

from dotenv import load_dotenv
from engine.capsule_engine import CapsuleEngine

# Load environment variables from .env file
load_dotenv()

# Fetch settings from environment variables
AGENT_ID = os.getenv("UATP_AGENT_ID", "demo-agent-fallback")
CHAIN_PATH = os.getenv("UATP_CHAIN_PATH", "capsule_chain.jsonl")

# Initialize the engine
# The engine will now correctly load the signing key from the environment.
engine = CapsuleEngine(agent_id=AGENT_ID, storage_path=CHAIN_PATH)


def record_capsule(capsule_type, confidence, reasoning_trace, metadata=None, **kwargs):
    """
    Record an agent interaction as a UATP capsule and log it to the chain.
    Args:
        capsule_type (str): Capsule type (e.g., Introspective, Refusal, Joint).
        confidence (float): Confidence value.
        reasoning_trace (list): Reasoning trace steps.
        metadata (dict, optional): Additional metadata.
        **kwargs: Specialized capsule fields.
    Returns:
        str: Capsule ID of the recorded capsule.
    """
    capsule = engine.create_capsule(
        capsule_type=capsule_type,
        confidence=confidence,
        reasoning_trace=reasoning_trace,
        metadata=metadata,
        **kwargs,
    )
    engine.log_capsule(capsule)
    return capsule.capsule_id
