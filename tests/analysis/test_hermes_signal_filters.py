from scripts.analysis.hermes_signal_filters import (
    classify_hermes_meta_message,
    is_hermes_meta_message,
)


def test_detects_context_compaction_meta_message():
    text = "[CONTEXT COMPACTION — REFERENCE ONLY] Earlier turns were compacted"

    assert is_hermes_meta_message(text)
    assert classify_hermes_meta_message(text) == "context_compaction"


def test_detects_preserved_task_list_meta_message():
    text = (
        "[Your active task list was preserved across context compression]\n- [ ] task"
    )

    assert is_hermes_meta_message(text)
    assert classify_hermes_meta_message(text) == "preserved_task_list"


def test_detects_model_switch_meta_message():
    text = "[Note: model was just switched from claude to gpt]\n\nok"

    assert is_hermes_meta_message(text)
    assert classify_hermes_meta_message(text) == "model_switch"


def test_detects_background_process_notification_meta_message():
    text = (
        '[IMPORTANT: Background process proc_123 matched watch pattern "Serving HTTP".'
    )

    assert is_hermes_meta_message(text)
    assert classify_hermes_meta_message(text) == "background_process_notification"


def test_detects_tool_iteration_limit_meta_message():
    text = (
        "You've reached the maximum number of tool-calling iterations allowed. "
        "Please provide a final response summarizing what you've found."
    )

    assert is_hermes_meta_message(text)
    assert classify_hermes_meta_message(text) == "tool_iteration_limit"


def test_does_not_treat_real_user_feedback_as_meta():
    assert not is_hermes_meta_message("fix that")
    assert not is_hermes_meta_message("no ai slop")
    assert not is_hermes_meta_message("can you see uatp locally?")
    assert classify_hermes_meta_message("fix that") is None
