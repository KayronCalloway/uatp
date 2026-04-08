#!/usr/bin/env python3
"""
Rich Claude Code Hook Capture
Captures full conversation context with maximum metadata richness
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Load environment
from dotenv import load_dotenv

load_dotenv()

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from src.live_capture.claude_code_capture import ClaudeCodeCapture

# Optional outcome integration (archived)
try:
    from src.live_capture.outcome_integration import process_user_message_for_outcome

    _OUTCOME_AVAILABLE = True
except ImportError:
    process_user_message_for_outcome = None  # type: ignore
    _OUTCOME_AVAILABLE = False


async def capture_rich_session():
    """Capture current Claude Code session with RICH metadata."""

    capture = ClaudeCodeCapture()

    # Read user message from stdin (provided by hook)
    user_message = ""
    if not sys.stdin.isatty():
        try:
            user_message = sys.stdin.read().strip()
        except Exception:
            pass

    # Get or create persistent session
    session_file = Path("/tmp/claude_code_active_session.json")
    session_id = None

    try:
        if session_file.exists():
            with open(session_file) as f:
                session_data = json.load(f)
                session_id = session_data.get("session_id")
                _ = session_data.get("message_count", 0)  # Used for logging
        else:
            # Start new session
            _user = os.getenv("USER", "unknown")
            session_id = await capture.start_session(user_id=_user)
            session_data = {
                "session_id": session_id,
                "message_count": 0,
                "started": datetime.now(timezone.utc).isoformat(),
            }
    except Exception as e:
        print(f"[WARN]  Session file error: {e}, creating new session")
        _user = os.getenv("USER", "unknown")
        session_id = await capture.start_session(user_id=_user)
        session_data = {
            "session_id": session_id,
            "message_count": 0,
            "started": datetime.now(timezone.utc).isoformat(),
        }

    # Capture user message with rich metadata
    if user_message:
        try:
            # Analyze message complexity for token estimation
            estimated_tokens = len(user_message.split()) * 1.3  # Rough estimate

            await capture.capture_message(
                session_id=session_id,
                role="user",
                content=user_message,
                token_count=int(estimated_tokens),
                model_info="claude-sonnet-4.5",
            )

            session_data["message_count"] += 1
            session_data["last_user_message"] = user_message[:100]

            print(f"[OK] Captured user message (session: {session_id[:8]}...)")
            print(f"   Message #{session_data['message_count']}")
            print(f"   Tokens: ~{int(estimated_tokens)}")

            # OUTCOME TRACKING (Gap 1)
            # Check if this message indicates an outcome for a previous capsule
            if _OUTCOME_AVAILABLE and process_user_message_for_outcome:
                try:
                    outcome_result = process_user_message_for_outcome(user_message)
                    if outcome_result and outcome_result.get("updated_capsule"):
                        print(
                            f"    Outcome inferred: {outcome_result['status']} "
                            f"(confidence: {outcome_result['confidence']:.0%})"
                        )
                except Exception:
                    pass  # Outcome tracking is optional, don't fail capture

        except Exception as e:
            print(f"[ERROR] Failed to capture user message: {e}")

    # Capture recent assistant responses from Claude Code conversation transcript
    try:
        # Find the conversation transcript file
        # Convert current working directory to Claude project format

        cwd = os.getcwd()
        project_name = cwd.replace("/", "-")
        if project_name.startswith("-"):
            project_name = project_name  # Keep leading dash
        project_dir = Path.home() / ".claude" / "projects" / project_name
        transcript_files = sorted(
            project_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
        )

        if transcript_files:
            transcript_file = transcript_files[0]  # Most recent

            # Read last N lines to find recent assistant responses
            with open(transcript_file) as f:
                lines = f.readlines()

            # Get assistant responses from last 20 lines.
            # Extract thinking, text, tool_use, and usage from each.
            recent_assistant_responses = []
            for line in lines[-20:]:
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "assistant":
                        msg = entry.get("message", {})
                        content = msg.get("content", [])
                        usage = msg.get("usage", {})
                        model = msg.get("model", "")

                        thinking_parts = []
                        text_parts = []
                        tool_uses = []

                        if isinstance(content, list):
                            for part in content:
                                if isinstance(part, dict):
                                    if part.get("type") == "thinking":
                                        thinking_parts.append(
                                            part.get("thinking", "")
                                            or part.get("text", "")
                                        )
                                    elif part.get("type") == "text":
                                        text_parts.append(part.get("text", ""))
                                    elif part.get("type") == "tool_use":
                                        tool_uses.append(
                                            {
                                                "name": part.get("name"),
                                                "input": part.get("input", {}),
                                                "id": part.get("id"),
                                            }
                                        )
                                elif isinstance(part, str):
                                    text_parts.append(part)
                        elif isinstance(content, str):
                            text_parts.append(content)

                        combined_text = " ".join(text_parts)
                        combined_thinking = "\n".join(thinking_parts)

                        # Build the full content with thinking prepended
                        if combined_thinking and combined_text:
                            full_content = f"[THINKING]\n{combined_thinking}\n[/THINKING]\n\n{combined_text}"
                        elif combined_thinking:
                            full_content = (
                                f"[THINKING]\n{combined_thinking}\n[/THINKING]"
                            )
                        else:
                            full_content = combined_text

                        if full_content and len(full_content) > 50:
                            recent_assistant_responses.append(
                                {
                                    "content": full_content,
                                    "thinking": combined_thinking,
                                    "text": combined_text,
                                    "tool_uses": tool_uses,
                                    "usage": usage,
                                    "model": model,
                                }
                            )
                except Exception:
                    continue

            # Capture the most recent assistant response if not already captured
            if recent_assistant_responses:
                latest = recent_assistant_responses[-1]
                assistant_response = latest["content"]

                # Only capture if it's new (check against last captured)
                last_captured = session_data.get("last_assistant_response", "")[:100]
                if assistant_response[:100] != last_captured:
                    # Use actual token count from usage if available
                    usage = latest.get("usage", {})
                    token_count = usage.get("output_tokens") or int(
                        len(assistant_response.split()) * 1.3
                    )
                    actual_model = latest.get("model") or "claude-opus-4-5"

                    await capture.capture_message(
                        session_id=session_id,
                        role="assistant",
                        content=assistant_response[:10000],
                        token_count=token_count,
                        model_info=actual_model,
                    )
                    session_data["message_count"] += 1
                    session_data["last_assistant_response"] = assistant_response[:100]
                    print(
                        f"[OK] Captured assistant response ({len(assistant_response)} chars)"
                    )

                    # Store tool uses and thinking for enrichment
                    if latest.get("thinking"):
                        session_data.setdefault("thinking_turns", []).append(
                            {
                                "thinking": latest["thinking"][:5000],
                                "thinking_length": len(latest["thinking"]),
                                "response_length": len(latest["text"]),
                                "had_tool_calls": bool(latest["tool_uses"]),
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        )
                    if latest.get("tool_uses"):
                        for tu in latest["tool_uses"]:
                            input_str = json.dumps(tu.get("input", {}))
                            if len(input_str) > 2000:
                                input_str = input_str[:2000] + "..."
                            session_data.setdefault("tool_call_graph", []).append(
                                {
                                    "tool": tu["name"],
                                    "call_id": tu.get("id"),
                                    "arguments": input_str,
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                }
                            )
                    if usage:
                        # Accumulate token usage across the session
                        econ = session_data.setdefault(
                            "economics",
                            {
                                "input_tokens": 0,
                                "output_tokens": 0,
                                "cache_read_tokens": 0,
                                "cache_write_tokens": 0,
                            },
                        )
                        econ["input_tokens"] += usage.get("input_tokens", 0)
                        econ["output_tokens"] += usage.get("output_tokens", 0)
                        econ["cache_read_tokens"] += usage.get(
                            "cache_read_input_tokens", 0
                        )
                        econ["cache_write_tokens"] += usage.get(
                            "cache_creation_input_tokens", 0
                        )
                        econ["model"] = actual_model
                        econ["billing_provider"] = "anthropic"

    except Exception as e:
        print(f"[WARN] Assistant capture skipped: {e}")

    # Every 10 messages, create a checkpoint capsule
    if (
        session_data.get("message_count", 0) % 10 == 0
        and session_data.get("message_count", 0) > 0
    ):
        try:
            # Get the session from active sessions
            if session_id in capture.active_sessions:
                session = capture.active_sessions[session_id]

                # Create intermediate capsule with RICH metadata
                capsule_id = await capture.create_capsule_from_session(session)

                if capsule_id:
                    print(f" Created RICH checkpoint capsule: {capsule_id}")
                    print(f"   Messages: {len(session.messages)}")
                    print(f"   Significance: {session.significance_score:.2f}")
                    print(f"   Topics: {', '.join(session.topics)}")

                    # Inject accumulated enrichments into the capsule
                    _inject_enrichments_into_latest_capsule(session_data)

        except Exception as e:
            print(f"[WARN]  Checkpoint capsule creation skipped: {e}")

    # Update session file
    try:
        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)
    except Exception as e:
        print(f"[WARN]  Could not save session state: {e}")

    # Show session stats
    print(f" Session: {session_id[:16]}...")
    print(f"   Total messages: {session_data.get('message_count', 0)}")
    print(f"   Duration: Active since {session_data.get('started', 'unknown')[:19]}")


def _inject_enrichments_into_latest_capsule(session_data: dict):
    """Inject extended_thinking, tool_call_graph, and economics into the
    most recently created capsule in uatp_dev.db.

    The data was accumulated in session_data during the capture loop
    from the Claude Code transcript's thinking blocks, tool_use blocks,
    and usage fields.
    """
    import sqlite3
    from collections import Counter

    db_path = os.path.join(os.path.dirname(__file__), "..", "..", "uatp_dev.db")
    if not os.path.exists(db_path):
        return

    thinking_turns = session_data.get("thinking_turns", [])
    tool_graph_raw = session_data.get("tool_call_graph", [])
    economics = session_data.get("economics", {})

    if not thinking_turns and not tool_graph_raw and not economics:
        return

    try:
        conn = sqlite3.connect(db_path)
        # Get the most recent capsule
        row = conn.execute(
            "SELECT id, payload FROM capsules ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not row:
            conn.close()
            return

        capsule_id, payload_str = row
        payload = json.loads(payload_str)

        changed = False

        # Extended thinking
        if thinking_turns and "extended_thinking" not in payload:
            total_thinking = sum(t.get("thinking_length", 0) for t in thinking_turns)
            total_response = sum(t.get("response_length", 0) for t in thinking_turns)
            payload["extended_thinking"] = {
                "turns": thinking_turns,
                "total_thinking_chars": total_thinking,
                "total_response_chars": total_response,
                "thinking_to_response_ratio": round(
                    total_thinking / max(1, total_response), 2
                ),
                "turns_with_thinking": len(thinking_turns),
            }
            changed = True
            print(
                f"    Injected extended_thinking: {len(thinking_turns)} turns, {total_thinking} chars"
            )

        # Tool call graph
        if tool_graph_raw and "tool_call_graph" not in payload:
            tool_counts = Counter(
                t.get("tool") for t in tool_graph_raw if t.get("tool")
            )
            payload["tool_call_graph"] = {
                "invocations": tool_graph_raw,
                "tool_frequency": dict(tool_counts.most_common()),
                "total_tool_calls": len(tool_graph_raw),
                "unique_tools": len(tool_counts),
            }
            changed = True
            print(
                f"    Injected tool_call_graph: {len(tool_graph_raw)} calls, {len(tool_counts)} tools"
            )

        # Economics
        if economics and "economics" not in payload:
            total_input = economics.get("input_tokens", 0) + economics.get(
                "cache_read_tokens", 0
            )
            economics["total_tokens"] = (
                economics.get("input_tokens", 0)
                + economics.get("output_tokens", 0)
                + economics.get("cache_read_tokens", 0)
            )
            economics["cache_hit_rate"] = round(
                economics.get("cache_read_tokens", 0) / max(1, total_input), 4
            )
            payload["economics"] = economics
            changed = True
            print(
                f"    Injected economics: {economics.get('total_tokens', 0)} total tokens"
            )

        if changed:
            conn.execute(
                "UPDATE capsules SET payload = ? WHERE id = ?",
                (json.dumps(payload), capsule_id),
            )
            conn.commit()

        conn.close()
    except Exception as e:
        print(f"[WARN] Enrichment injection failed: {e}")


async def end_session_and_create_capsule():
    """Manually end session and create final capsule."""

    session_file = Path("/tmp/claude_code_active_session.json")

    if not session_file.exists():
        print("[WARN]  No active session found")
        return

    try:
        with open(session_file) as f:
            session_data = json.load(f)
            session_id = session_data.get("session_id")

        if not session_id:
            print("[ERROR] Invalid session data")
            return

        capture = ClaudeCodeCapture()

        # End the session
        session = await capture.end_session(session_id)

        if session:
            # Create final RICH capsule
            capsule_id = await capture.create_capsule_from_session(session)

            if capsule_id:
                print(f" Created final RICH capsule: {capsule_id}")
                print(f"   Messages: {len(session.messages)}")
                print(f"   Significance: {session.significance_score:.2f}")
                print(f"   Topics: {', '.join(session.topics)}")
                print(f"   Duration: {session.start_time} - {session.end_time}")

                # Inject accumulated enrichments
                _inject_enrichments_into_latest_capsule(session_data)
            else:
                print("ℹ️  Session didn't meet capsule criteria")
                print(f"   Messages: {len(session.messages)}")
                print(f"   Significance: {session.significance_score:.2f}")

        # Remove session file
        session_file.unlink()
        print(" Session ended and cleaned up")

    except Exception as e:
        print(f"[ERROR] Error ending session: {e}")
        import traceback

        traceback.print_exc()


def backfill_enrichments_from_transcript(transcript_path: str, capsule_id: str = None):
    """Retroactively extract thinking, tool_use, and usage from a full
    Claude Code JSONL transcript and inject into the specified capsule
    (or the most recent one).

    Usage:
        python3 rich_hook_capture.py --backfill /path/to/transcript.jsonl [capsule_id]
    """
    import sqlite3
    from collections import Counter

    db_path = os.path.join(os.path.dirname(__file__), "..", "..", "uatp_dev.db")
    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found: {db_path}")
        return

    transcript = Path(transcript_path)
    if not transcript.exists():
        print(f"[ERROR] Transcript not found: {transcript_path}")
        return

    thinking_turns = []
    tool_invocations = []
    economics = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
    }
    model_used = None

    with open(transcript) as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("type") != "assistant":
                    continue

                msg = entry.get("message", {})
                content = msg.get("content", [])
                usage = msg.get("usage", {})
                model = msg.get("model", "")
                if model:
                    model_used = model

                thinking_text = ""
                response_text = ""
                tools = []

                if isinstance(content, list):
                    for part in content:
                        if not isinstance(part, dict):
                            continue
                        if part.get("type") == "thinking":
                            thinking_text += (
                                part.get("thinking", "") or part.get("text", "")
                            ) + "\n"
                        elif part.get("type") == "text":
                            response_text += part.get("text", "")
                        elif part.get("type") == "tool_use":
                            input_str = json.dumps(part.get("input", {}))
                            if len(input_str) > 2000:
                                input_str = input_str[:2000] + "..."
                            tools.append(
                                {
                                    "tool": part.get("name"),
                                    "call_id": part.get("id"),
                                    "arguments": input_str,
                                    "timestamp": entry.get("timestamp"),
                                }
                            )

                if thinking_text.strip():
                    thinking_turns.append(
                        {
                            "timestamp": entry.get("timestamp"),
                            "thinking": thinking_text.strip()[:5000],
                            "thinking_length": len(thinking_text.strip()),
                            "response_length": len(response_text),
                            "had_tool_calls": bool(tools),
                        }
                    )
                tool_invocations.extend(tools)

                if usage:
                    economics["input_tokens"] += usage.get("input_tokens", 0)
                    economics["output_tokens"] += usage.get("output_tokens", 0)
                    economics["cache_read_tokens"] += usage.get(
                        "cache_read_input_tokens", 0
                    )
                    economics["cache_write_tokens"] += usage.get(
                        "cache_creation_input_tokens", 0
                    )

            except (json.JSONDecodeError, Exception):
                continue

    if model_used:
        economics["model"] = model_used
        economics["billing_provider"] = "anthropic"

    total_input = economics["input_tokens"] + economics["cache_read_tokens"]
    economics["total_tokens"] = (
        economics["input_tokens"]
        + economics["output_tokens"]
        + economics["cache_read_tokens"]
    )
    economics["cache_hit_rate"] = round(
        economics["cache_read_tokens"] / max(1, total_input), 4
    )

    print(
        f"Parsed transcript: {len(thinking_turns)} thinking turns, {len(tool_invocations)} tool calls"
    )
    print(
        f"  Tokens: {economics['total_tokens']} total, cache hit rate: {economics['cache_hit_rate']:.1%}"
    )

    # Inject into capsule
    conn = sqlite3.connect(db_path)
    if capsule_id:
        row = conn.execute(
            "SELECT id, payload FROM capsules WHERE capsule_id = ?", (capsule_id,)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT id, payload FROM capsules ORDER BY id DESC LIMIT 1"
        ).fetchone()

    if not row:
        print("[ERROR] No capsule found to enrich")
        conn.close()
        return

    db_id, payload_str = row
    payload = json.loads(payload_str)
    changed = False

    if thinking_turns:
        total_thinking = sum(t["thinking_length"] for t in thinking_turns)
        total_response = sum(t["response_length"] for t in thinking_turns)
        payload["extended_thinking"] = {
            "turns": thinking_turns,
            "total_thinking_chars": total_thinking,
            "total_response_chars": total_response,
            "thinking_to_response_ratio": round(
                total_thinking / max(1, total_response), 2
            ),
            "turns_with_thinking": len(thinking_turns),
        }
        changed = True

    if tool_invocations:
        tool_counts = Counter(t["tool"] for t in tool_invocations if t.get("tool"))
        payload["tool_call_graph"] = {
            "invocations": tool_invocations,
            "tool_frequency": dict(tool_counts.most_common()),
            "total_tool_calls": len(tool_invocations),
            "unique_tools": len(tool_counts),
        }
        changed = True

    if economics.get("total_tokens", 0) > 0:
        payload["economics"] = economics
        changed = True

    if changed:
        conn.execute(
            "UPDATE capsules SET payload = ? WHERE id = ?", (json.dumps(payload), db_id)
        )
        conn.commit()
        print(f"Enriched capsule (db id={db_id})")
    else:
        print("Nothing to inject")

    conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--end-session":
        asyncio.run(end_session_and_create_capsule())
    elif len(sys.argv) > 1 and sys.argv[1] == "--backfill":
        # Retroactive enrichment from a full transcript
        transcript = sys.argv[2] if len(sys.argv) > 2 else None
        cap_id = sys.argv[3] if len(sys.argv) > 3 else None
        if not transcript:
            print(
                "Usage: rich_hook_capture.py --backfill <transcript.jsonl> [capsule_id]"
            )
            sys.exit(1)
        backfill_enrichments_from_transcript(transcript, cap_id)
    else:
        # Normal capture
        asyncio.run(capture_rich_session())
