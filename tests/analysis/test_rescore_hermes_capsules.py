import importlib.util
import sys
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "analysis"
    / "rescore_hermes_capsules.py"
)
spec = importlib.util.spec_from_file_location("rescore_hermes_capsules", SCRIPT_PATH)
rescore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rescore)


def user_step(text, signal_type):
    return {
        "role": "user",
        "reasoning": text,
        "measurements": {"signal_type": signal_type},
    }


def assistant_step(text):
    return {"role": "assistant", "reasoning": text, "measurements": {}}


def test_context_compaction_signal_is_neutralized():
    new_sig = rescore.apply_guards_to_existing(
        "correction",
        "[CONTEXT COMPACTION — REFERENCE ONLY] Earlier turns were compacted.",
        1200,
    )

    assert new_sig == "neutral"


def test_model_switch_note_signal_is_neutralized():
    new_sig = rescore.apply_guards_to_existing(
        "requery",
        "[Note: model was just switched from deepseek to claude.] ok back to uatp",
        900,
    )

    assert new_sig == "neutral"


def test_preserved_task_list_signal_is_neutralized():
    new_sig = rescore.apply_guards_to_existing(
        "correction",
        "[Your active task list was preserved across context compression] - [>] Audit MCP gateway",
        900,
    )

    assert new_sig == "neutral"


def test_preserved_task_list_suffix_signal_is_neutralized():
    new_sig = rescore.apply_guards_to_existing(
        "refinement",
        "show the sparkle on hover\n\n[Your active task list was preserved across context compression]\n- [>] Visual polish",
        900,
    )

    assert new_sig == "neutral"


def test_background_process_notification_signal_is_neutralized():
    new_sig = rescore.apply_guards_to_existing(
        "refinement",
        '[IMPORTANT: Background process proc_123 matched watch pattern "Serving HTTP".]',
        900,
    )

    assert new_sig == "neutral"


def test_tool_iteration_limit_signal_is_neutralized():
    new_sig = rescore.apply_guards_to_existing(
        "correction",
        "You've reached the maximum number of tool-calling iterations allowed. "
        "Please provide a final response summarizing what you've found.",
        900,
    )

    assert new_sig == "neutral"


def test_short_fix_after_long_assistant_promotes_to_correction():
    new_sig = rescore.apply_guards_to_existing("neutral", "ok fix it", 1200)

    assert new_sig == "correction"


def test_cli_defaults_to_dry_run_and_requires_explicit_apply(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["rescore_hermes_capsules.py"])
    args = rescore.parse_args()
    assert args.apply is False

    monkeypatch.setattr(sys, "argv", ["rescore_hermes_capsules.py", "--apply"])
    args = rescore.parse_args()
    assert args.apply is True


def test_rescore_capsule_rebuilds_feedback_summary_after_signal_changes():
    payload = {
        "reasoning_steps": [
            assistant_step("x" * 1200),
            user_step("[CONTEXT COMPACTION — REFERENCE ONLY] summary", "correction"),
            assistant_step("y" * 1200),
            user_step("ok fix it", "neutral"),
        ],
        "feedback_signals": {"correction_count": 99},
    }

    new_payload, changed = rescore.rescore_capsule(payload)

    assert changed is True
    signals = [
        step["measurements"].get("signal_type")
        for step in new_payload["reasoning_steps"]
        if step["role"] == "user"
    ]
    assert signals == ["neutral", "correction"]
    assert new_payload["feedback_signals"]["correction_count"] == 1
    assert new_payload["feedback_signals"]["total_non_neutral"] == 1
