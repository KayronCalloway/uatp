"""
Tool Calls Capture - Gap 3 Implementation
Extracts and captures tool calls from Claude Code transcripts.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def find_transcript_file(cwd: str = None) -> Optional[Path]:
    """
    Find the most recent Claude Code transcript file.

    Args:
        cwd: Current working directory (for project name)

    Returns:
        Path to transcript file or None
    """
    working_dir = cwd or os.getcwd()
    project_name = working_dir.replace("/", "-")
    project_dir = Path.home() / ".claude" / "projects" / project_name

    if not project_dir.exists():
        return None

    transcript_files = sorted(
        project_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
    )

    return transcript_files[0] if transcript_files else None


def extract_tool_calls_from_transcript(
    transcript_path: Path,
    max_lines: int = 100,
    since_timestamp: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """
    Extract tool calls from a Claude Code transcript.

    Args:
        transcript_path: Path to the .jsonl transcript
        max_lines: Maximum lines to read from end
        since_timestamp: Only include calls after this time

    Returns:
        List of tool call dicts
    """
    tool_calls = []

    try:
        with open(transcript_path) as f:
            lines = f.readlines()

        # Process last N lines
        for line in lines[-max_lines:]:
            try:
                entry = json.loads(line)

                # Look for assistant messages with tool_use
                if entry.get("type") == "assistant":
                    message = entry.get("message", {})
                    content = message.get("content", [])

                    if isinstance(content, list):
                        for item in content:
                            if (
                                isinstance(item, dict)
                                and item.get("type") == "tool_use"
                            ):
                                tool_call = extract_tool_call_info(item, entry)
                                if tool_call:
                                    # Filter by timestamp if specified
                                    if since_timestamp:
                                        call_time = tool_call.get("timestamp")
                                        if (
                                            call_time
                                            and datetime.fromisoformat(
                                                call_time.replace("Z", "+00:00")
                                            )
                                            < since_timestamp
                                        ):
                                            continue
                                    tool_calls.append(tool_call)

                # Also check for tool_result entries
                if entry.get("type") == "user":
                    message = entry.get("message", {})
                    content = message.get("content", [])

                    if isinstance(content, list):
                        for item in content:
                            if (
                                isinstance(item, dict)
                                and item.get("type") == "tool_result"
                            ):
                                # Find matching tool call and update with result
                                tool_use_id = item.get("tool_use_id")
                                result_content = item.get("content", "")

                                # Update matching tool call with result
                                for tc in tool_calls:
                                    if tc.get("tool_use_id") == tool_use_id:
                                        tc["result"] = summarize_result(result_content)
                                        tc["has_result"] = True
                                        break

            except json.JSONDecodeError:
                continue
            except Exception:
                continue

    except Exception as e:
        print(f"Error reading transcript: {e}")

    return tool_calls


def extract_tool_call_info(
    tool_use: Dict[str, Any], entry: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Extract relevant info from a tool_use block.

    Args:
        tool_use: The tool_use content block
        entry: The full transcript entry

    Returns:
        Cleaned tool call dict
    """
    tool_name = tool_use.get("name", "unknown")
    tool_input = tool_use.get("input", {})
    tool_use_id = tool_use.get("id", "")

    # Extract timestamp from entry if available
    timestamp = entry.get("timestamp") or datetime.now(timezone.utc).isoformat()

    tool_call = {
        "tool": tool_name,
        "tool_use_id": tool_use_id,
        "timestamp": timestamp,
        "has_result": False,
    }

    # Extract relevant params based on tool type
    if tool_name == "Read":
        tool_call["params"] = {
            "file_path": tool_input.get("file_path", ""),
            "offset": tool_input.get("offset"),
            "limit": tool_input.get("limit"),
        }
        tool_call["summary"] = f"Read {tool_input.get('file_path', 'file')}"

    elif tool_name == "Write":
        file_path = tool_input.get("file_path", "")
        content = tool_input.get("content", "")
        tool_call["params"] = {
            "file_path": file_path,
            "content_length": len(content),
        }
        tool_call["summary"] = f"Write {file_path} ({len(content)} chars)"

    elif tool_name == "Edit":
        file_path = tool_input.get("file_path", "")
        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")
        tool_call["params"] = {
            "file_path": file_path,
            "old_length": len(old_string),
            "new_length": len(new_string),
            "replace_all": tool_input.get("replace_all", False),
        }
        # Create a mini-diff summary
        tool_call["summary"] = f"Edit {file_path}"
        tool_call["diff_preview"] = create_diff_preview(old_string, new_string)

    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        tool_call["params"] = {
            "command": command[:200],  # Truncate long commands
            "timeout": tool_input.get("timeout"),
            "run_in_background": tool_input.get("run_in_background", False),
        }
        tool_call["summary"] = (
            f"Bash: {command[:50]}..." if len(command) > 50 else f"Bash: {command}"
        )

    elif tool_name == "Glob":
        tool_call["params"] = {
            "pattern": tool_input.get("pattern", ""),
            "path": tool_input.get("path", ""),
        }
        tool_call["summary"] = f"Glob: {tool_input.get('pattern', '')}"

    elif tool_name == "Grep":
        tool_call["params"] = {
            "pattern": tool_input.get("pattern", ""),
            "path": tool_input.get("path", ""),
            "glob": tool_input.get("glob"),
        }
        tool_call["summary"] = f"Grep: {tool_input.get('pattern', '')}"

    elif tool_name == "WebFetch":
        tool_call["params"] = {
            "url": tool_input.get("url", ""),
            "prompt": tool_input.get("prompt", "")[:100],
        }
        tool_call["summary"] = f"WebFetch: {tool_input.get('url', '')[:50]}"

    elif tool_name == "WebSearch":
        tool_call["params"] = {
            "query": tool_input.get("query", ""),
        }
        tool_call["summary"] = f"WebSearch: {tool_input.get('query', '')}"

    elif tool_name == "Task":
        tool_call["params"] = {
            "description": tool_input.get("description", ""),
            "subagent_type": tool_input.get("subagent_type", ""),
        }
        tool_call["summary"] = f"Task: {tool_input.get('description', '')}"

    else:
        # Generic handling for unknown tools
        tool_call["params"] = {k: str(v)[:100] for k, v in list(tool_input.items())[:5]}
        tool_call["summary"] = f"{tool_name} call"

    return tool_call


def create_diff_preview(old_string: str, new_string: str, max_length: int = 100) -> str:
    """Create a compact diff preview for Edit operations."""
    old_preview = old_string[:max_length] + (
        "..." if len(old_string) > max_length else ""
    )
    new_preview = new_string[:max_length] + (
        "..." if len(new_string) > max_length else ""
    )

    return f"- {old_preview}\n+ {new_preview}"


def summarize_result(result_content: Any, max_length: int = 200) -> str:
    """Summarize a tool result for storage."""
    if isinstance(result_content, str):
        if len(result_content) > max_length:
            return (
                result_content[:max_length] + f"... ({len(result_content)} chars total)"
            )
        return result_content
    elif isinstance(result_content, list):
        # Handle array of content blocks
        text_parts = []
        for item in result_content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
            elif isinstance(item, str):
                text_parts.append(item)
        combined = " ".join(text_parts)
        if len(combined) > max_length:
            return combined[:max_length] + f"... ({len(combined)} chars total)"
        return combined
    else:
        return str(result_content)[:max_length]


def capture_tool_calls(
    cwd: str = None, session_start: Optional[datetime] = None, max_calls: int = 50
) -> Dict[str, Any]:
    """
    Capture tool calls for a capsule.

    Args:
        cwd: Working directory
        session_start: Only capture calls after this time
        max_calls: Maximum number of calls to capture

    Returns:
        Dict with tool calls and summary statistics
    """
    transcript = find_transcript_file(cwd)
    if not transcript:
        return {
            "tool_calls": [],
            "summary": {"total_calls": 0, "note": "No transcript found"},
        }

    tool_calls = extract_tool_calls_from_transcript(
        transcript,
        max_lines=200,  # Look at more lines to capture full session
        since_timestamp=session_start,
    )

    # Limit to max_calls
    tool_calls = tool_calls[-max_calls:]

    # Calculate summary statistics
    tool_counts = {}
    files_accessed = set()
    commands_run = []

    for tc in tool_calls:
        tool_name = tc.get("tool", "unknown")
        tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1

        params = tc.get("params", {})
        if "file_path" in params:
            files_accessed.add(params["file_path"])
        if "command" in params:
            commands_run.append(params["command"][:50])

    return {
        "tool_calls": tool_calls,
        "summary": {
            "total_calls": len(tool_calls),
            "by_tool": tool_counts,
            "unique_files": len(files_accessed),
            "files_accessed": list(files_accessed)[:20],  # Limit list
            "commands_run": commands_run[:10],  # Limit list
            "captured_at": datetime.now(timezone.utc).isoformat(),
        },
    }


if __name__ == "__main__":
    print("Tool Calls Capture Test")
    print("=" * 50)

    result = capture_tool_calls()
    print(f"\nFound {result['summary']['total_calls']} tool calls")
    print(f"By tool: {result['summary']['by_tool']}")
    print(f"\nFiles accessed: {result['summary']['unique_files']}")

    if result["tool_calls"]:
        print("\nLast 3 tool calls:")
        for tc in result["tool_calls"][-3:]:
            print(f"  - {tc['summary']}")
