"""
hermes_capture.py — Converts a Hermes session into a signed UATP capsule.

Routes through the full RichCaptureEnhancer pipeline so Hermes capsules
get the same quality as Claude Code capsules: critical path analysis,
uncertainty quantification, quality assessment, confidence explanations,
trust posture, etc.

Reads messages from ~/.hermes/state.db, converts them to UATP's
ConversationMessage/ConversationSession objects, runs them through
RichCaptureEnhancer, signs with Ed25519 via UATPCryptoV7, writes
to ~/uatp-capsule-engine/uatp_dev.db.

Usage:
    python3 hermes_capture.py <session_id>
    python3 hermes_capture.py --latest
    python3 hermes_capture.py --list
"""

import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
STATE_DB = HERMES_HOME / "state.db"
UATP_ROOT = Path.home() / "uatp-capsule-engine"
UATP_DB = UATP_ROOT / "uatp_dev.db"

MIN_MESSAGES = 4


# ---------------------------------------------------------------------------
# UATP imports (lazy, from the UATP codebase)
# ---------------------------------------------------------------------------

_uatp_loaded = False


def _ensure_uatp_imports():
    """Add UATP to sys.path and import what we need. Cached after first call."""
    global _uatp_loaded
    if _uatp_loaded:
        return
    if str(UATP_ROOT) not in sys.path:
        sys.path.insert(0, str(UATP_ROOT))
    _uatp_loaded = True


def _get_capture_classes():
    """Import ConversationMessage, ConversationSession from UATP."""
    _ensure_uatp_imports()
    from src.live_capture.claude_code_capture import (
        ConversationMessage,
        ConversationSession,
    )

    return ConversationMessage, ConversationSession


def _get_rich_enhancer():
    """Import RichCaptureEnhancer."""
    _ensure_uatp_imports()
    from src.live_capture.rich_capture_integration import RichCaptureEnhancer

    return RichCaptureEnhancer


def _get_signal_detector():
    """Import SignalDetector."""
    _ensure_uatp_imports()
    from src.live_capture.signal_detector import SignalDetector

    return SignalDetector()


def _get_crypto():
    """Import UATPCryptoV7."""
    _ensure_uatp_imports()
    from src.security.uatp_crypto_v7 import UATPCryptoV7

    return UATPCryptoV7(
        key_dir=str(UATP_ROOT / ".uatp_keys"),
        signer_id="hermes_capture",
    )


# ---------------------------------------------------------------------------
# Read Hermes session
# ---------------------------------------------------------------------------


def read_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Read a session and its messages from state.db."""
    if not STATE_DB.exists():
        logger.error("state.db not found at %s", STATE_DB)
        return None

    conn = sqlite3.connect(str(STATE_DB))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if not row:
            logger.error("Session %s not found", session_id)
            return None

        messages = conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()

        return {
            "session": dict(row),
            "messages": [dict(m) for m in messages],
        }
    finally:
        conn.close()


def list_recent_sessions(limit: int = 10) -> List[Dict]:
    """List recent sessions from state.db."""
    if not STATE_DB.exists():
        return []
    conn = sqlite3.connect(str(STATE_DB))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT id, model, message_count, title, started_at "
            "FROM sessions ORDER BY started_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Convert Hermes messages -> UATP dataclasses
# ---------------------------------------------------------------------------


def _ts_from_epoch(epoch) -> Optional[datetime]:
    """Convert epoch float to datetime."""
    if epoch is None:
        return None
    try:
        return datetime.fromtimestamp(float(epoch), tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return None


def _extract_topics(messages: List[Dict]) -> List[str]:
    """Pull rough topics from user messages."""
    user_text = " ".join(
        (m.get("content") or "")[:500] for m in messages if m["role"] == "user"
    ).lower()

    stop = {
        "the",
        "a",
        "an",
        "is",
        "it",
        "to",
        "and",
        "or",
        "of",
        "in",
        "for",
        "on",
        "with",
        "that",
        "this",
        "can",
        "you",
        "i",
        "my",
        "me",
        "do",
        "be",
        "have",
        "has",
        "had",
        "was",
        "were",
        "are",
        "not",
        "but",
        "so",
        "if",
        "at",
        "from",
        "by",
        "as",
        "up",
        "out",
        "about",
        "just",
        "what",
        "how",
        "all",
        "its",
        "let",
        "yes",
        "no",
        "ok",
        "make",
        "see",
        "get",
        "would",
        "could",
        "should",
        "will",
        "there",
        "here",
        "also",
        "then",
    }
    words = [w.strip(".,!?()[]{}\"'`") for w in user_text.split()]
    words = [w for w in words if len(w) > 2 and w not in stop and w.isalpha()]

    return [w for w, _ in Counter(words).most_common(8)]


def _convert_to_uatp_objects(
    session_id: str,
    session: Dict,
    messages: List[Dict],
    platform: str = "hermes-cli",
):
    """Convert Hermes session data into UATP ConversationMessage/Session objects."""
    ConversationMessage, ConversationSession = _get_capture_classes()
    detector = _get_signal_detector()

    now = datetime.now(timezone.utc)
    started = _ts_from_epoch(session.get("started_at")) or now

    # Run signal detection on user messages
    previous_user_msgs = []
    previous_assistant_response = None
    conv_messages = []

    for i, msg in enumerate(messages):
        role = msg["role"]
        content = msg.get("content") or ""
        ts = _ts_from_epoch(msg.get("timestamp")) or now

        # Only user and assistant messages map to ConversationMessage.
        # Tool messages get folded into the preceding assistant context.
        if role not in ("user", "assistant"):
            continue

        # For assistant messages, prepend the extended thinking if available.
        # This is the model's actual chain-of-thought — the most valuable
        # data for a reasoning trace capsule.
        reasoning = msg.get("reasoning") or ""

        # Skip empty assistant messages (pure tool dispatch with no text or thinking).
        # These are just "I'm going to call tool X" with no reasoning — noise.
        if role == "assistant" and not content.strip():
            continue

        signal_type = "neutral"
        references_previous = False
        sentiment_delta = 0.0

        if role == "user" and content.strip():
            signal = detector.detect_signal(
                content, previous_user_msgs, "user", previous_assistant_response
            )
            signal_type = signal.signal_type
            references_previous = signal.references_previous
            sentiment_delta = signal.sentiment_delta

            # Guard: "ok" at the start of a new topic or question is not acceptance.
            # The detector's ^ok\b pattern fires on "ok but..." and "ok how..."
            # which are actually topic pivots or corrections.
            if signal_type == "acceptance":
                lower = content.lower().strip()
                if lower.startswith("ok") or lower.startswith("okay"):
                    # Real "ok" acceptances are short ("ok", "ok thanks", "ok go ahead").
                    # Longer messages starting with "ok" are discourse markers ("ok, so...")
                    # and are almost always new questions or redirects, not acceptance.
                    word_count = len(lower.split())
                    pivot_words = ("but", "however", "actually", "wait", "no", "not")
                    has_pivot = any(w in lower[:50] for w in pivot_words)
                    has_question = "?" in lower
                    if word_count > 4 or has_pivot or has_question:
                        signal_type = "neutral"
                        references_previous = False

            # Guard: soft_rejection on follow-up questions is a false positive.
            # The detector sees zero shared content words and calls it rejection,
            # but "so what about..." / "how does..." are legitimate follow-ups.
            if signal_type == "soft_rejection":
                lower = content.lower().strip()
                question_starters = (
                    "so ",
                    "what ",
                    "how ",
                    "can ",
                    "could ",
                    "would ",
                    "will ",
                    "why ",
                    "when ",
                    "where ",
                    "who ",
                    "which ",
                    "is ",
                    "are ",
                    "do ",
                    "does ",
                    "did ",
                )
                if "?" in lower or any(lower.startswith(w) for w in question_starters):
                    signal_type = "neutral"
                    references_previous = True

            previous_user_msgs.append(content)
            # Reset after user message; next assistant will set this
            previous_assistant_response = None

        if role == "assistant" and content.strip():
            previous_assistant_response = content

        conv_msg = ConversationMessage(
            role=role,
            content=content,
            timestamp=ts,
            message_id=f"hermes_{session_id}_{i}",
            session_id=session_id,
            token_count=msg.get("token_count"),
            model_info=session.get("model"),
            signal_type=signal_type,
            references_previous=references_previous,
            sentiment_delta=sentiment_delta,
        )
        # Attach raw reasoning as custom attribute for downstream use
        conv_msg._hermes_thinking = (
            reasoning if (role == "assistant" and reasoning) else None
        )
        conv_messages.append(conv_msg)

    # Build session object
    total_tokens = (session.get("input_tokens") or 0) + (
        session.get("output_tokens") or 0
    )
    topics = _extract_topics(messages)

    # Aggregate non-neutral signals for downstream DPO/quality analysis
    sig_counts = Counter(
        m.signal_type
        for m in conv_messages
        if m.role == "user" and m.signal_type != "neutral"
    )
    total_user = len([m for m in conv_messages if m.role == "user"])
    feedback_signals = None
    if sig_counts:
        feedback_signals = {
            "correction_count": sig_counts.get("correction", 0),
            "requery_count": sig_counts.get("requery", 0),
            "refinement_count": sig_counts.get("refinement", 0),
            "acceptance_count": sig_counts.get("acceptance", 0),
            "abandonment_count": sig_counts.get("abandonment", 0),
            "soft_rejection_count": sig_counts.get("soft_rejection", 0),
            "code_execution_count": sig_counts.get("code_execution", 0),
            "total_non_neutral": sum(sig_counts.values()),
            "correction_rate": round(sig_counts.get("correction", 0) / total_user, 4)
            if total_user
            else 0.0,
            "acceptance_rate": round(sig_counts.get("acceptance", 0) / total_user, 4)
            if total_user
            else 0.0,
            "signal_breakdown": dict(sig_counts),
        }

    conv_session = ConversationSession(
        session_id=session_id,
        user_id="kay",
        start_time=started,
        platform=platform,
        end_time=now,
        messages=conv_messages,
        significance_score=0.0,  # will be recalculated by the enhancer
        total_tokens=total_tokens,
        topics=topics,
    )
    # Attach feedback summary for build_capsule to consume
    conv_session._hermes_feedback_signals = feedback_signals

    return conv_session


# ---------------------------------------------------------------------------
# Build capsule via RichCaptureEnhancer
# ---------------------------------------------------------------------------


def build_capsule(
    session_id: str,
    session: Dict,
    messages: List[Dict],
    model: Optional[str] = None,
    platform: str = "hermes-cli",
) -> Dict[str, Any]:
    """Build a full-quality UATP capsule through RichCaptureEnhancer."""

    conv_session = _convert_to_uatp_objects(session_id, session, messages, platform)

    RichCaptureEnhancer = _get_rich_enhancer()
    capsule = RichCaptureEnhancer.create_capsule_from_session_with_rich_metadata(
        conv_session, user_id="kay"
    )

    # Override type to distinguish from Claude Code captures
    capsule["type"] = "hermes-capture"
    capsule["payload"]["capsule_type"] = "hermes-capture"

    # --- Thinking field separation ---
    # Walk reasoning_steps and split out [THINKING] blocks into separate fields
    reasoning_steps = capsule.get("payload", {}).get("reasoning_steps", [])
    for step in reasoning_steps:
        content = step.get("content") or step.get("reasoning") or ""
        if "[THINKING]" in content:
            thinking_match = re.search(
                r"\[THINKING\]\s*(.*?)\s*\[/THINKING\]", content, re.DOTALL
            )
            if thinking_match:
                step["thinking"] = thinking_match.group(1).strip()
                cleaned = re.sub(
                    r"\[THINKING\].*?\[/THINKING\]\s*", "", content, flags=re.DOTALL
                ).strip()
                if "content" in step:
                    step["content"] = cleaned
                if "reasoning" in step:
                    step["reasoning"] = cleaned

    # Fix message counts — RichCaptureEnhancer doesn't populate these
    total_msgs = len(messages)
    user_msgs = [m for m in messages if m["role"] == "user"]
    asst_msgs = [m for m in messages if m["role"] == "assistant"]
    tool_msgs = [m for m in messages if m["role"] == "tool"]

    session_meta = capsule["payload"].setdefault("session_metadata", {})
    session_meta["message_count"] = total_msgs
    session_meta["user_message_count"] = len(user_msgs)
    session_meta["assistant_message_count"] = len(asst_msgs)
    session_meta["tool_message_count"] = len(tool_msgs)

    # Add Hermes-specific metadata that the Claude Code pipeline doesn't have
    session_meta["hermes_session_id"] = session_id
    session_meta["hermes_platform"] = session.get("source", platform)
    session_meta["hermes_model"] = model or session.get("model")
    session_meta["hermes_title"] = session.get("title")
    session_meta["input_tokens"] = session.get("input_tokens")
    session_meta["output_tokens"] = session.get("output_tokens")
    session_meta["cache_read_tokens"] = session.get("cache_read_tokens")
    session_meta["tool_call_count"] = session.get("tool_call_count")

    # --- Tool call graph ---
    # Extract structured tool invocations with arguments and results.
    # This maps the AI's decision-making: what it chose to do and what happened.
    tool_invocations = []
    pending_calls = {}  # tool_call_id -> call info

    for msg in messages:
        # Assistant messages with tool_calls = the AI deciding to invoke tools
        if msg["role"] == "assistant" and msg.get("tool_calls"):
            try:
                calls = (
                    json.loads(msg["tool_calls"])
                    if isinstance(msg["tool_calls"], str)
                    else msg["tool_calls"]
                )
                for call in calls or []:
                    fn = call.get("function", {})
                    call_id = call.get("call_id") or call.get("id")
                    args_str = fn.get("arguments", "")
                    # Truncate very large arguments
                    if len(args_str) > 2000:
                        args_str = args_str[:2000] + "..."
                    invocation = {
                        "tool": fn.get("name"),
                        "call_id": call_id,
                        "arguments": args_str,
                        "timestamp": _ts_from_epoch(msg.get("timestamp")).isoformat()
                        if msg.get("timestamp")
                        else None,
                        "reasoning_before": (msg.get("reasoning") or "")[:500] or None,
                    }
                    tool_invocations.append(invocation)
                    if call_id:
                        pending_calls[call_id] = invocation
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning("Failed to parse tool_calls in message: %s", e)

        # Tool messages = results, matched back to invocations
        if msg["role"] == "tool":
            call_id = msg.get("tool_call_id")
            content = msg.get("content") or ""
            result_summary = content[:500] + ("..." if len(content) > 500 else "")
            if call_id and call_id in pending_calls:
                pending_calls[call_id]["result_length"] = len(content)
                pending_calls[call_id]["result_preview"] = result_summary
            else:
                # Orphaned tool result
                tool_invocations.append(
                    {
                        "tool": msg.get("tool_name"),
                        "call_id": call_id,
                        "result_length": len(content),
                        "result_preview": result_summary,
                    }
                )

    if tool_invocations:
        # Tool usage summary
        tool_counts = Counter(t["tool"] for t in tool_invocations if t.get("tool"))
        capsule["payload"]["tool_call_graph"] = {
            "invocations": tool_invocations,
            "tool_frequency": dict(tool_counts.most_common()),
            "total_tool_calls": len(tool_invocations),
            "unique_tools": len(tool_counts),
        }

    # --- Cost economics ---
    # Real compute cost data: token usage, caching efficiency, billing.
    input_tokens = session.get("input_tokens") or 0
    output_tokens = session.get("output_tokens") or 0
    cache_read = session.get("cache_read_tokens") or 0
    cache_write = session.get("cache_write_tokens") or 0
    reasoning_tokens = session.get("reasoning_tokens") or 0
    estimated_cost = session.get("estimated_cost_usd") or 0.0
    actual_cost = session.get("actual_cost_usd")

    total_input = input_tokens + cache_read
    cache_hit_rate = round(cache_read / total_input, 4) if total_input > 0 else 0.0

    capsule["payload"]["economics"] = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_tokens": cache_read,
        "cache_write_tokens": cache_write,
        "reasoning_tokens": reasoning_tokens,
        "total_tokens": input_tokens + output_tokens + cache_read,
        "cache_hit_rate": cache_hit_rate,
        "estimated_cost_usd": estimated_cost,
        "actual_cost_usd": actual_cost,
        "billing_provider": session.get("billing_provider"),
        "billing_mode": session.get("billing_mode"),
    }

    # --- Extended thinking archive ---
    # Raw chain-of-thought from the model, separate from the content.
    # This is the unfiltered reasoning the model did before each response.
    thinking_turns = []
    for msg in messages:
        reasoning = msg.get("reasoning")
        if reasoning and msg["role"] == "assistant":
            thinking_turns.append(
                {
                    "timestamp": _ts_from_epoch(msg.get("timestamp")).isoformat()
                    if msg.get("timestamp")
                    else None,
                    "thinking": reasoning,
                    "thinking_length": len(reasoning),
                    "response_length": len(msg.get("content") or ""),
                    "had_tool_calls": bool(msg.get("tool_calls")),
                }
            )
    if thinking_turns:
        capsule["payload"]["extended_thinking"] = {
            "turns": thinking_turns,
            "total_thinking_chars": sum(t["thinking_length"] for t in thinking_turns),
            "total_response_chars": sum(t["response_length"] for t in thinking_turns),
            "thinking_to_response_ratio": round(
                sum(t["thinking_length"] for t in thinking_turns)
                / max(1, sum(t["response_length"] for t in thinking_turns)),
                2,
            ),
            "turns_with_thinking": len(thinking_turns),
            "turns_total": len([m for m in messages if m["role"] == "assistant"]),
        }

    # --- Session lineage ---
    parent = session.get("parent_session_id")
    if parent:
        session_meta = capsule["payload"].setdefault("session_metadata", {})
        session_meta["parent_session_id"] = parent
        session_meta["is_continuation"] = True

    # --- Tool result archive ---
    # Full tool results for context preservation.
    tool_archive = []
    for msg in messages:
        if msg["role"] == "tool":
            content = msg.get("content") or ""
            if len(content) > 3000:
                content = content[:3000] + f"... [{len(content)} chars total]"
            tool_archive.append(
                {
                    "role": "tool",
                    "tool_name": msg.get("tool_name"),
                    "tool_call_id": msg.get("tool_call_id"),
                    "content": content,
                    "timestamp": _ts_from_epoch(msg.get("timestamp")).isoformat()
                    if msg.get("timestamp")
                    else None,
                }
            )
    if tool_archive:
        session_meta = capsule["payload"].setdefault("session_metadata", {})
        prompt_ctx = session_meta.setdefault("prompt_context", {})
        prompt_ctx["tool_results"] = tool_archive

    # --- Feedback signal summary ---
    # Aggregate message-level signals for DPO extraction and quality analysis.
    # Purely additive — no existing code reads this field.
    feedback_signals = getattr(conv_session, "_hermes_feedback_signals", None)
    if feedback_signals:
        capsule["payload"]["feedback_signals"] = feedback_signals

    return capsule


# ---------------------------------------------------------------------------
# Sign + write
# ---------------------------------------------------------------------------


def sign_capsule(capsule: Dict) -> Dict:
    """Sign the capsule with UATPCryptoV7 (Ed25519 + optional PQ)."""
    try:
        crypto = _get_crypto()
        verification = crypto.sign_capsule(capsule)
        capsule["verification"] = verification
        logger.info("Capsule signed: hash=%s", verification.get("hash", "?")[:24])
    except Exception as e:
        logger.warning("Crypto signing failed (%s), using hash-only", e)
        content_str = json.dumps(
            {k: v for k, v in capsule.items() if k != "verification"},
            sort_keys=True,
            separators=(",", ":"),
        )
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()
        capsule["verification"] = {
            "signer": "hermes_capture",
            "hash": f"sha256:{content_hash}",
            "signature": None,
            "method": "hash_only",
            "note": f"Signing unavailable: {e}",
        }
    return capsule


def write_capsule(capsule: Dict) -> bool:
    """Write signed capsule to uatp_dev.db."""
    if not UATP_DB.exists():
        logger.error("uatp_dev.db not found at %s", UATP_DB)
        return False
    conn = sqlite3.connect(str(UATP_DB))
    try:
        # Session deduplication: check if capsule already exists for this session
        session_id = capsule.get("payload", {}).get("session_metadata", {}).get(
            "hermes_session_id"
        ) or capsule.get("payload", {}).get("session_metadata", {}).get("session_id")
        if session_id:
            existing = conn.execute(
                """SELECT capsule_id FROM capsules
                   WHERE json_extract(payload, '$.session_metadata.hermes_session_id') = ?
                      OR json_extract(payload, '$.session_metadata.session_id') = ?""",
                (session_id, session_id),
            ).fetchone()
            if existing:
                logger.info(
                    "Capsule already exists for session %s (capsule_id=%s), skipping",
                    session_id,
                    existing[0],
                )
                return True

        conn.execute(
            """
            INSERT INTO capsules (capsule_id, capsule_type, version, timestamp, status, verification, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (capsule_id) DO NOTHING
            """,
            (
                capsule["capsule_id"],
                capsule["type"],
                capsule["version"],
                capsule["timestamp"],
                capsule["status"],
                json.dumps(capsule["verification"]),
                json.dumps(capsule["payload"]),
            ),
        )
        conn.commit()
        rows = conn.total_changes
        logger.info(
            "Wrote capsule %s to uatp_dev.db (%d rows)", capsule["capsule_id"], rows
        )
        return rows > 0
    except (sqlite3.Error, OSError):
        logger.exception("Failed to write capsule to uatp_dev.db")
        return False
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def capture_session(
    session_id: str,
    model: str = None,
    platform: str = "hermes-cli",
) -> Optional[Dict]:
    """Full pipeline: read session -> RichCaptureEnhancer -> sign -> write."""
    data = read_session(session_id)
    if not data:
        return None

    session = data["session"]
    messages = data["messages"]

    if len(messages) < MIN_MESSAGES:
        logger.info(
            "Session %s has only %d messages, skipping", session_id, len(messages)
        )
        return None

    capsule = build_capsule(
        session_id, session, messages, model=model, platform=platform
    )
    capsule = sign_capsule(capsule)
    written = write_capsule(capsule)

    if written:
        return capsule
    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if len(sys.argv) < 2:
        print("Usage: python3 hermes_capture.py <session_id>")
        print("       python3 hermes_capture.py --latest")
        print("       python3 hermes_capture.py --list")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--list":
        sessions = list_recent_sessions(15)
        if not sessions:
            print("No sessions found.")
            return
        print(f"{'Session ID':<30} {'Messages':>8}  {'Model':<30} {'Title'}")
        print("-" * 100)
        for s in sessions:
            title = s.get("title") or ""
            print(
                f"{s['id']:<30} {s.get('message_count', 0):>8}  {(s.get('model') or '?'):<30} {title[:30]}"
            )
        return

    if arg == "--latest":
        sessions = list_recent_sessions(1)
        if not sessions:
            print("No sessions found.")
            sys.exit(1)
        session_id = sessions[0]["id"]
        print(f"Capturing latest session: {session_id}")
    else:
        session_id = arg

    result = capture_session(session_id)
    if result:
        payload = result["payload"]
        sig = result["verification"]
        meta = payload.get("session_metadata", {})
        feedback = payload.get("feedback_signals", {})

        print(f"\nCapsule created: {result['capsule_id']}")
        print(f"Type:            {result['type']}")
        print(f"Signed:          {sig.get('signature') is not None}")
        print(f"Hash:            {sig.get('hash', 'none')[:40]}...")
        print(f"Confidence:      {payload.get('confidence', '?')}")
        print(
            f"Quality grade:   {payload.get('quality_assessment', {}).get('quality_grade', 'n/a')}"
        )
        print(
            f"Trust posture:   {payload.get('trust_posture', {}).get('level', 'n/a')}"
        )
        print(f"Corrections:     {feedback.get('correction_count', 0)}")
        print(f"Acceptances:     {feedback.get('acceptance_count', 0)}")
        print(f"Topics:          {', '.join(meta.get('topics', [])[:5])}")

        # Show what rich fields are present
        rich_fields = [
            k
            for k in payload
            if k
            not in (
                "prompt",
                "reasoning_steps",
                "final_answer",
                "confidence",
                "model_used",
                "created_by",
                "session_metadata",
                "schema_version",
                "capsule_type",
            )
        ]
        if rich_fields:
            print(f"Rich metadata:   {', '.join(rich_fields)}")
    else:
        print("No capsule created (session too short or not found).")
        sys.exit(1)


if __name__ == "__main__":
    main()
