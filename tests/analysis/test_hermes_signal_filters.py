from scripts.analysis.hermes_signal_filters import is_hermes_meta_message


def test_detects_context_compaction_meta_message():
    assert is_hermes_meta_message(
        "[CONTEXT COMPACTION — REFERENCE ONLY] Earlier turns were compacted"
    )


def test_detects_preserved_task_list_meta_message():
    assert is_hermes_meta_message(
        "[Your active task list was preserved across context compression]\n- [ ] task"
    )


def test_detects_model_switch_meta_message():
    assert is_hermes_meta_message(
        "[Note: model was just switched from claude to gpt]\n\nok"
    )


def test_does_not_treat_real_user_feedback_as_meta():
    assert not is_hermes_meta_message("fix that")
    assert not is_hermes_meta_message("no ai slop")
    assert not is_hermes_meta_message("can you see uatp locally?")
