#!/usr/bin/env python3
"""
Agent Self-Capture Script
=========================

Allows AI agents (Antigravity, Claude Code, etc.) to create their own capsules
with full conversation content that would otherwise be encrypted/inaccessible.

Usage by agents:
    python create_agent_capsule.py --platform antigravity --task "Task description" --content "Full conversation or reasoning"

Or programmatically:
    from create_agent_capsule import create_capsule
    capsule_id = create_capsule(
        platform="antigravity",
        task="What I was asked to do",
        reasoning_steps=[...],
        content="Full conversation text"
    )
"""

import argparse
import hashlib
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import UATP v7 crypto for real Ed25519 signing
try:
    from src.security.uatp_crypto_v7 import UATPCryptoV7

    _crypto: Optional[UATPCryptoV7] = None

    def get_crypto() -> Optional[UATPCryptoV7]:
        """Get or initialize the crypto singleton."""
        global _crypto
        if _crypto is None:
            try:
                _crypto = UATPCryptoV7(
                    key_dir=".uatp_keys", signer_id="agent_self_capture"
                )
            except Exception as e:
                print(f"⚠️ Crypto initialization failed: {e}")
                return None
        return _crypto

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    _crypto = None

    def get_crypto():
        return None


# API configuration
API_BASE = os.getenv("UATP_API_URL", "http://localhost:8000")
API_KEY = os.getenv("UATP_API_KEY", "test-api-key")


def create_capsule(
    platform: str,
    task: str,
    content: str,
    reasoning_steps: Optional[List[Dict[str, Any]]] = None,
    model: str = "gemini-2.5-pro",
    user_id: str = "kay",
    confidence: float = 0.85,
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Create a capsule from agent-provided content.

    This is the key function that allows agents to self-capture their work
    when the raw conversation data is encrypted/inaccessible.

    Args:
        platform: Agent platform (antigravity, claude-code, cursor, etc.)
        task: Description of what was asked/accomplished
        content: Full conversation or reasoning content
        reasoning_steps: Optional list of structured reasoning steps
        model: Model used (default: gemini-2.5-pro for Antigravity)
        user_id: User identifier
        confidence: Confidence score (0.0-1.0)
        metadata: Additional metadata to include

    Returns:
        capsule_id if successful, None otherwise
    """
    timestamp = datetime.now(timezone.utc)

    # Generate capsule ID
    capsule_id = f"{platform}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{int(time.time())}"

    # Auto-generate reasoning steps if not provided
    if reasoning_steps is None:
        reasoning_steps = _extract_reasoning_from_content(content, task)

    # Compute content hash for verification
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:32]

    # Build capsule (without verification - added after)
    capsule_data = {
        "capsule_id": capsule_id,
        "type": "reasoning_trace",
        "version": "7.0",
        "timestamp": timestamp.isoformat(),
        "payload": {
            "prompt": task,
            "reasoning_steps": reasoning_steps,
            "final_answer": _extract_conclusion(content) or f"Completed: {task}",
            "confidence": confidence,
            "model_used": model,
            "created_by": user_id,
            "full_content": content[:50000],  # Cap at 50KB
            "session_metadata": {
                "platform": platform,
                "capture_method": "agent_self_capture",
                "content_length": len(content),
                "timestamp": timestamp.isoformat(),
                **(metadata or {}),
            },
        },
    }

    # Add cryptographic verification with Ed25519 signature
    crypto = get_crypto()
    if crypto and crypto.enabled:
        # Real Ed25519 signature
        verification = crypto.sign_capsule(capsule_data)
        capsule_data["verification"] = verification
        print("🔐 Capsule signed with Ed25519")
    else:
        # Fallback to hash-only verification
        capsule_data["verification"] = {
            "signer": f"{platform}_self_capture",
            "verify_key": None,
            "hash": f"sha256:{content_hash}",
            "signature": None,
            "merkle_root": None,
        }

    # Submit to API
    try:
        response = requests.post(
            f"{API_BASE}/capsules",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json=capsule_data,
            timeout=30,
        )

        if response.status_code in [200, 201]:
            result_id = response.json().get("capsule_id", capsule_id)
            print(f"✅ Capsule created: {result_id}")
            print(f"   Platform: {platform}")
            print(f"   Steps: {len(reasoning_steps)}")
            print(f"   Content: {len(content):,} chars")
            return result_id
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"   {response.text[:200]}")
            return None

    except Exception as e:
        print(f"❌ Failed to create capsule: {e}")
        return None


def _extract_reasoning_from_content(content: str, task: str) -> List[Dict[str, Any]]:
    """Extract reasoning steps from unstructured content."""
    steps = []
    step_num = 1

    # Add task as first step
    steps.append(
        {
            "step_id": step_num,
            "operation": "task_received",
            "reasoning": task,
            "confidence": 0.95,
        }
    )
    step_num += 1

    # Look for common reasoning patterns
    patterns = [
        ("let me", "analysis"),
        ("i'll", "action"),
        ("first", "step"),
        ("then", "step"),
        ("finally", "conclusion"),
        ("the issue", "problem_identification"),
        ("the solution", "solution"),
        ("i found", "discovery"),
        ("this means", "inference"),
        ("therefore", "conclusion"),
        ("because", "reasoning"),
        ("however", "consideration"),
        ("alternatively", "alternative"),
    ]

    lines = content.split("\n")
    for line in lines:
        line_lower = line.lower().strip()
        if len(line_lower) < 10:
            continue

        for pattern, operation in patterns:
            if pattern in line_lower:
                steps.append(
                    {
                        "step_id": step_num,
                        "operation": operation,
                        "reasoning": line.strip()[:500],
                        "confidence": 0.75,
                    }
                )
                step_num += 1
                break

        if step_num > 50:  # Cap at 50 steps
            break

    # Add completion step
    steps.append(
        {
            "step_id": step_num,
            "operation": "completion",
            "reasoning": f"Task completed: {task}",
            "confidence": 0.90,
        }
    )

    return steps


def _extract_conclusion(content: str) -> Optional[str]:
    """Try to extract a conclusion from the content."""
    # Look for conclusion markers
    markers = ["in conclusion", "to summarize", "the result", "finally", "in summary"]

    lines = content.split("\n")
    for i, line in enumerate(lines):
        for marker in markers:
            if marker in line.lower():
                # Return this line and next few
                conclusion_lines = lines[i : i + 3]
                return " ".join(conclusion_lines).strip()[:500]

    # Return last substantial paragraph
    for line in reversed(lines):
        if len(line.strip()) > 50:
            return line.strip()[:500]

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Create a UATP capsule from agent-provided content"
    )
    parser.add_argument(
        "--platform",
        "-p",
        required=True,
        help="Agent platform (antigravity, claude-code, cursor, etc.)",
    )
    parser.add_argument("--task", "-t", required=True, help="Task description")
    parser.add_argument("--content", "-c", help="Full content (or use --file)")
    parser.add_argument("--file", "-f", help="Read content from file")
    parser.add_argument("--model", "-m", default="gemini-2.5-pro", help="Model used")
    parser.add_argument(
        "--confidence", type=float, default=0.85, help="Confidence score (0.0-1.0)"
    )
    parser.add_argument("--user", default="kay", help="User ID")

    args = parser.parse_args()

    # Get content
    if args.file:
        with open(args.file) as f:
            content = f.read()
    elif args.content:
        content = args.content
    else:
        print("Reading content from stdin...")
        content = sys.stdin.read()

    if not content.strip():
        print("❌ No content provided")
        sys.exit(1)

    # Create capsule
    capsule_id = create_capsule(
        platform=args.platform,
        task=args.task,
        content=content,
        model=args.model,
        user_id=args.user,
        confidence=args.confidence,
    )

    if capsule_id:
        print(f"\n🎯 Capsule ID: {capsule_id}")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
