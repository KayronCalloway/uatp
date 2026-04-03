#!/usr/bin/env python3
"""
UATP Ollama Integration
=======================

Captures local LLM conversations (Gemma, Llama, etc.) via Ollama
and creates signed UATP capsules in the gold standard layered format.

Usage:
    python -m src.integrations.ollama_capture "Your prompt here"

    # Or interactive mode:
    python -m src.integrations.ollama_capture --interactive

    # Specify model:
    python -m src.integrations.ollama_capture --model gemma4 "Explain provenance"
"""

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# UATP imports
try:
    from src.core.layered_capsule_builder import LayeredCapsuleBuilder
    from src.core.provenance import EpistemicClass, Event, Evidence, ProofLevel
    from src.security.uatp_crypto_v7 import UATPCryptoV7

    _UATP_AVAILABLE = True
except ImportError as e:
    logger.warning(f"UATP modules not available: {e}")
    _UATP_AVAILABLE = False
    EpistemicClass = None  # Fallback


# Self-assessment prompt - structured to get honest, testable claims
SELF_ASSESSMENT_PROMPT = """
Review your previous response and provide a structured self-assessment.

IMPORTANT: DO NOT defend your answer. BE HONEST about limitations.
This assessment will be compared against actual outcomes to measure your calibration.

Respond in this exact JSON format (no other text):
{
    "confidence_estimate": <float 0.0-1.0>,
    "grounding_sources": ["<list what you based this on>"],
    "assumptions_made": ["<list assumptions that might be wrong>"],
    "uncertainty_areas": ["<where you're least sure>"],
    "potential_errors": ["<what could be wrong>"],
    "would_change_if": ["<conditions that would change your answer>"],
    "verification_needed": ["<what should be checked>"]
}
"""

# Database imports for storage
try:
    import sqlite3

    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False


class OllamaCapture:
    """Captures Ollama LLM interactions as UATP capsules."""

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model: str = "gemma4",
        db_path: str = "uatp_dev.db",
    ):
        self.ollama_url = ollama_url
        self.model = model
        self.db_path = db_path
        self.session_id = self._generate_session_id()
        self.messages: List[Dict] = []

        # Initialize crypto for signing
        self._crypto = None
        if _UATP_AVAILABLE:
            try:
                self._crypto = UATPCryptoV7(
                    key_dir=".uatp_keys",
                    signer_id="ollama_capture",
                    enable_pq=True,
                )
                logger.info("Crypto initialized for signing")
            except Exception as e:
                logger.warning(f"Crypto not available: {e}")

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"ollama_{self.model}_{timestamp}"

    def _sha256(self, text: str) -> str:
        """Hash text with SHA256."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def check_ollama(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = [m["name"] for m in response.json().get("models", [])]
                # Check for model (with or without :latest tag)
                model_available = any(
                    self.model in m or m.startswith(self.model) for m in models
                )
                if model_available:
                    logger.info(f"Ollama ready with model: {self.model}")
                    return True
                else:
                    logger.error(f"Model {self.model} not found. Available: {models}")
                    return False
        except Exception as e:
            logger.error(f"Cannot connect to Ollama: {e}")
            return False
        return False

    def call_model(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """
        Call the Ollama model and capture the interaction.

        Returns:
            Dict with response text and metadata
        """
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Store user message
        self.messages.append(
            {
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Call Ollama
        request_time = datetime.now(timezone.utc)
        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                },
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            return {"error": str(e)}

        response_time = datetime.now(timezone.utc)
        duration_ms = (response_time - request_time).total_seconds() * 1000

        # Extract response
        output_text = data.get("message", {}).get("content", "")

        # Store assistant message
        self.messages.append(
            {
                "role": "assistant",
                "content": output_text,
                "timestamp": response_time.isoformat(),
                "model": data.get("model", self.model),
                "duration_ms": duration_ms,
                "prompt_eval_count": data.get("prompt_eval_count"),
                "eval_count": data.get("eval_count"),
            }
        )

        return {
            "response": output_text,
            "model": data.get("model", self.model),
            "duration_ms": duration_ms,
            "prompt_tokens": data.get("prompt_eval_count"),
            "response_tokens": data.get("eval_count"),
            "done_reason": data.get("done_reason"),
        }

    def create_capsule(self) -> Dict[str, Any]:
        """
        Create a UATP capsule from the conversation.

        Returns the capsule in gold standard layered format.
        """
        capsule_id = f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d_%H%M%S')}_{self.model[:8]}"

        # Build events from messages
        events = []
        for msg in self.messages:
            events.append(
                {
                    "event_type": f"{msg['role']}_message",
                    "timestamp": msg["timestamp"],
                    "data": {
                        "role": msg["role"],
                        "content_length": len(msg["content"]),
                        "content_hash": self._sha256(msg["content"]),
                        "model": msg.get("model"),
                    },
                    "proof": ProofLevel.TOOL_VERIFIED.value
                    if _UATP_AVAILABLE
                    else "tool_verified",
                    "source": "ollama_capture",
                }
            )

        # Build evidence
        evidence = []

        # Get the last assistant response for summary
        last_response = ""
        for msg in reversed(self.messages):
            if msg["role"] == "assistant":
                last_response = msg["content"]
                break

        # Get the user prompt for context
        user_prompt = ""
        for msg in self.messages:
            if msg["role"] == "user":
                user_prompt = msg["content"]
                break

        # Build the capsule payload
        payload = {
            "prompt": user_prompt[:500] if user_prompt else "Ollama conversation",
            "model": self.model,
            "session_id": self.session_id,
            "message_count": len(self.messages),
            "messages": [
                {
                    "role": m["role"],
                    "content": m["content"][:2000] + "..."
                    if len(m["content"]) > 2000
                    else m["content"],
                    "timestamp": m["timestamp"],
                    "content_hash": self._sha256(m["content"]),
                }
                for m in self.messages
            ],
            "reasoning_steps": [
                {
                    "step": i + 1,
                    "role": m["role"],
                    "reasoning": m["content"][:1000] + "..."
                    if len(m["content"]) > 1000
                    else m["content"],
                    "timestamp": m["timestamp"],
                    "proof_level": "tool_verified"
                    if m["role"] == "user"
                    else "model_generated",
                }
                for i, m in enumerate(self.messages)
            ],
        }

        # Build layered structure
        layers = {
            "events": events,
            "evidence": evidence,
            "interpretation": {
                "summary": last_response[:500] if last_response else "No response",
                "claims": [],
                "status": "unverified",
                "semantic_drift_detected": False,
            },
            "judgment": {
                "gates_passed": [],
                "court_admissible": False,
                "insurance_ready": False,
                "blockers": ["Local model - no external verification"],
            },
        }

        # Trust posture for local model
        trust_posture = {
            "provenance_integrity": "medium",  # We captured it locally
            "artifact_verifiability": "low",  # Local model, no external audit
            "semantic_alignment": "unknown",
            "decision_completeness": "unknown",
            "risk_calibration": "low",
            "legal_reliance_readiness": "not_ready",
            "operational_utility": "high",  # It's useful for local work
        }

        # Assemble capsule
        capsule = {
            "capsule_id": capsule_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "ollama_conversation",
            "version": "1.1",
            "status": "verified",
            "payload": {
                **payload,
                "schema_version": "2.0_layered",
                "layers": layers,
                "trust_posture": trust_posture,
            },
            "verification": {},
        }

        # Sign if crypto available
        if self._crypto and self._crypto.enabled:
            try:
                verification = self._crypto.sign_capsule(
                    capsule, timestamp_mode="local"
                )
                capsule["verification"] = verification

                # Update evidence with signature
                capsule["payload"]["layers"]["evidence"].append(
                    {
                        "claim": "Capsule was signed",
                        "verified": True,
                        "proof": "crypto_verified",
                        "artifact": verification.get("signature", "")[:32] + "...",
                        "verification_method": "ed25519_signature",
                    }
                )
                capsule["payload"]["layers"]["judgment"]["gates_passed"].append(
                    "signature_verified"
                )

                logger.info("Capsule signed with Ed25519")
            except Exception as e:
                logger.warning(f"Signing failed: {e}")

        return capsule

    def save_capsule(self, capsule: Dict[str, Any]) -> bool:
        """Save capsule to the UATP database."""
        if not _DB_AVAILABLE:
            logger.warning("Database not available")
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Insert capsule with parent_capsule_id for linking
            cursor.execute(
                """
                INSERT INTO capsules (
                    capsule_id, capsule_type, version, timestamp, status,
                    verification, payload, parent_capsule_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    capsule["capsule_id"],
                    capsule.get(
                        "capsule_type", capsule.get("type", "ollama_conversation")
                    ),
                    capsule.get("version", "1.1"),
                    capsule["timestamp"],
                    capsule.get("status", "verified"),
                    json.dumps(capsule.get("verification", {})),
                    json.dumps(capsule.get("payload", {})),
                    capsule.get("parent_capsule_id"),  # For linking self-assessments
                ),
            )

            conn.commit()
            conn.close()

            logger.info(f"Capsule {capsule['capsule_id']} saved to database")
            return True

        except Exception as e:
            logger.error(f"Failed to save capsule: {e}")
            return False

    def request_self_assessment(
        self, original_response: str
    ) -> Optional[Dict[str, Any]]:
        """
        Request a self-assessment from the model about its previous response.

        This is MODEL_SELF_ASSESSMENT - testimony about itself, NOT evidence.
        The assessment will be compared against actual outcomes to measure calibration.

        Returns:
            Parsed self-assessment dict, or None if failed
        """
        # Build the prompt with the original response
        assessment_request = f"""
Your previous response was:
---
{original_response[:2000]}{"..." if len(original_response) > 2000 else ""}
---

{SELF_ASSESSMENT_PROMPT}
"""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": assessment_request}],
                    "stream": False,
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()

            assessment_text = data.get("message", {}).get("content", "")

            # Try to parse JSON from the response
            # Handle markdown code blocks
            if "```json" in assessment_text:
                assessment_text = assessment_text.split("```json")[1].split("```")[0]
            elif "```" in assessment_text:
                assessment_text = assessment_text.split("```")[1].split("```")[0]

            assessment = json.loads(assessment_text.strip())

            logger.info(
                f"Self-assessment received: confidence={assessment.get('confidence_estimate', 'N/A')}"
            )
            return assessment

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse self-assessment JSON: {e}")
            # Return a structured failure
            return {
                "confidence_estimate": None,
                "parse_error": str(e),
                "raw_response": assessment_text[:500]
                if "assessment_text" in dir()
                else None,
            }
        except Exception as e:
            logger.warning(f"Self-assessment request failed: {e}")
            return None

    def create_self_assessment_capsule(
        self,
        parent_capsule_id: str,
        assessment: Dict[str, Any],
        original_response: str,
    ) -> Dict[str, Any]:
        """
        Create a self-assessment capsule linked to the original response.

        IMPORTANT: This capsule has epistemic_class: model_self_assessment
        It is testimony, not proof. It will be compared against actual outcomes.
        """
        capsule_id = f"{parent_capsule_id}_self"
        now = datetime.now(timezone.utc)

        # Determine epistemic class value
        ec_value = (
            EpistemicClass.MODEL_SELF_ASSESSMENT.value
            if EpistemicClass
            else "model_self_assessment"
        )

        capsule = {
            "capsule_id": capsule_id,
            "capsule_type": "model_self_assessment",
            "parent_capsule_id": parent_capsule_id,  # Links to original
            "timestamp": now.isoformat(),
            "version": "1.1",
            "status": "captured",
            "payload": {
                "schema_version": "2.0_layered",
                "epistemic_class": ec_value,  # THE KEY FIELD
                "model": self.model,
                "assessment": assessment,
                "original_response_hash": self._sha256(original_response),
                "layers": {
                    "events": [
                        {
                            "event_type": "self_assessment_requested",
                            "timestamp": now.isoformat(),
                            "data": {
                                "parent_capsule": parent_capsule_id,
                                "model": self.model,
                            },
                            "proof": "tool_verified",
                            "epistemic_class": "tool_observed",
                            "source": "ollama_capture",
                        }
                    ],
                    "evidence": [],  # Empty - this is model output, no evidence
                    "interpretation": {
                        "summary": f"Model self-assessment with confidence: {assessment.get('confidence_estimate', 'unknown')}",
                        "claims": [],
                        "status": "unverified",  # ALWAYS unverified
                        "epistemic_class": ec_value,
                    },
                    "judgment": {
                        "gates_passed": [],
                        "court_admissible": False,
                        "insurance_ready": False,
                        "blockers": [
                            "Self-assessment cannot self-verify",
                            "Requires comparison with measured outcomes",
                        ],
                    },
                },
                "trust_posture": {
                    "provenance_integrity": "low",  # It's model output about itself
                    "artifact_verifiability": "low",  # Nothing to verify externally
                    "semantic_alignment": "unknown",
                    "decision_completeness": "unknown",
                    "risk_calibration": "untested",  # That's what we're measuring
                    "legal_reliance_readiness": "not_ready",
                    "operational_utility": "medium",  # Useful as hypothesis
                },
                # Calibration fields - to be filled in when outcomes are known
                "calibration": {
                    "outcome_recorded": False,
                    "outcome_capsule_id": None,
                    "deviation_score": None,  # Will be calculated later
                },
            },
            "verification": {},
        }

        # Sign if crypto available
        if self._crypto and self._crypto.enabled:
            try:
                verification = self._crypto.sign_capsule(
                    capsule, timestamp_mode="local"
                )
                capsule["verification"] = verification
                logger.info("Self-assessment capsule signed")
            except Exception as e:
                logger.warning(f"Signing self-assessment failed: {e}")

        return capsule

    def chat_with_assessment(
        self,
        prompt: str,
        save: bool = True,
    ) -> Dict[str, Any]:
        """
        Send a message, get a response, AND capture self-assessment.

        Returns dict with:
        - response: The model's response text
        - capsule_id: ID of the main capsule
        - self_assessment: The parsed self-assessment
        - self_assessment_capsule_id: ID of the self-assessment capsule
        """
        result = self.call_model(prompt)

        if "error" in result:
            return {"error": result["error"]}

        response = result["response"]
        main_capsule_id = None
        assessment = None
        assessment_capsule_id = None

        if save:
            # Create and save main capsule
            capsule = self.create_capsule()
            main_capsule_id = capsule["capsule_id"]
            self.save_capsule(capsule)
            logger.info(f"Created capsule: {main_capsule_id}")

            # Request and save self-assessment
            assessment = self.request_self_assessment(response)
            if assessment:
                assessment_capsule = self.create_self_assessment_capsule(
                    parent_capsule_id=main_capsule_id,
                    assessment=assessment,
                    original_response=response,
                )
                assessment_capsule_id = assessment_capsule["capsule_id"]
                self.save_capsule(assessment_capsule)
                logger.info(f"Created self-assessment capsule: {assessment_capsule_id}")

        return {
            "response": response,
            "capsule_id": main_capsule_id,
            "self_assessment": assessment,
            "self_assessment_capsule_id": assessment_capsule_id,
        }

    def chat(self, prompt: str, save: bool = True) -> str:
        """
        Send a message and get a response, optionally saving as capsule.

        Args:
            prompt: The user prompt
            save: Whether to save as a capsule after response

        Returns:
            The model's response text
        """
        result = self.call_model(prompt)

        if "error" in result:
            return f"Error: {result['error']}"

        response = result["response"]

        if save:
            capsule = self.create_capsule()
            self.save_capsule(capsule)
            logger.info(f"Created capsule: {capsule['capsule_id']}")

        return response

    def interactive(self):
        """Run an interactive chat session."""
        print(f"\nUATP Ollama Capture - Model: {self.model}")
        print(f"Session: {self.session_id}")
        print("Type 'quit' to exit, 'save' to save current conversation as capsule\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                break

            if not user_input:
                continue

            if user_input.lower() == "quit":
                # Save final capsule
                if self.messages:
                    capsule = self.create_capsule()
                    self.save_capsule(capsule)
                    print(f"\nFinal capsule saved: {capsule['capsule_id']}")
                break

            if user_input.lower() == "save":
                if self.messages:
                    capsule = self.create_capsule()
                    self.save_capsule(capsule)
                    print(f"Capsule saved: {capsule['capsule_id']}")
                else:
                    print("No messages to save yet")
                continue

            # Get response (don't auto-save each turn in interactive mode)
            response = self.chat(user_input, save=False)
            print(f"\n{self.model}: {response}\n")


def main():
    parser = argparse.ArgumentParser(
        description="UATP Ollama Integration - Capture local LLM conversations"
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="The prompt to send to the model",
    )
    parser.add_argument(
        "--model",
        "-m",
        default="gemma4",
        help="Ollama model name (default: gemma4)",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive chat mode",
    )
    parser.add_argument(
        "--url",
        default="http://localhost:11434",
        help="Ollama API URL (default: http://localhost:11434)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save capsule to database",
    )
    parser.add_argument(
        "--assess",
        "-a",
        action="store_true",
        help="Include self-assessment (captures model's confidence and uncertainty)",
    )

    args = parser.parse_args()

    # Initialize capture
    capture = OllamaCapture(
        ollama_url=args.url,
        model=args.model,
    )

    # Check Ollama is running
    if not capture.check_ollama():
        print("Error: Cannot connect to Ollama or model not available")
        print("Make sure Ollama is running: ollama serve")
        print(f"And model is pulled: ollama pull {args.model}")
        sys.exit(1)

    if args.interactive:
        capture.interactive()
    elif args.prompt:
        if args.assess:
            # Use chat_with_assessment for self-assessment mode
            result = capture.chat_with_assessment(args.prompt, save=not args.no_save)
            print(f"\n{capture.model}:\n{result['response']}\n")

            if result.get("self_assessment"):
                assessment = result["self_assessment"]
                print("=" * 50)
                print("SELF-ASSESSMENT (epistemic_class: model_self_assessment)")
                print("=" * 50)
                print(f"Confidence: {assessment.get('confidence_estimate', 'N/A')}")
                if assessment.get("grounding_sources"):
                    print(
                        f"Grounding: {', '.join(assessment['grounding_sources'][:3])}"
                    )
                if assessment.get("uncertainty_areas"):
                    print(
                        f"Uncertain about: {', '.join(assessment['uncertainty_areas'][:3])}"
                    )
                if assessment.get("verification_needed"):
                    print(
                        f"Should verify: {', '.join(assessment['verification_needed'][:3])}"
                    )
                print("=" * 50)
                print(f"Main capsule: {result.get('capsule_id')}")
                print(f"Assessment capsule: {result.get('self_assessment_capsule_id')}")
                print("\nNOTE: This is model testimony, NOT evidence.")
                print("Compare against actual outcomes to measure calibration.")
        else:
            response = capture.chat(args.prompt, save=not args.no_save)
            print(f"\n{capture.model}:\n{response}\n")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
