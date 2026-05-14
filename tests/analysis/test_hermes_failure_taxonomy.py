from scripts.analysis.hermes_failure_taxonomy import (
    CorrectionChain,
    classify_failure_modes,
)


def chain(correction, rejected="Long explanation " * 140, chosen="Fixed and verified."):
    return CorrectionChain(
        prompt="Please work on UATP.",
        rejected_response=rejected,
        correction=correction,
        chosen_response=chosen,
        source_capsule_id="cap-1",
    )


def test_classifies_context_drift():
    assert "context_drift" in classify_failure_modes(chain("i asked about uatp"))


def test_classifies_local_file_blindness_and_tool_omission():
    modes = classify_failure_modes(
        chain(
            "n can you see uatp?",
            rejected="UATP is a concept. I can explain it generally.",
        )
    )
    assert "local_file_blindness" in modes
    assert "tool_omission" in modes


def test_classifies_over_formatting_ai_slop():
    assert "over_formatting_ai_slop" in classify_failure_modes(chain("no ai slop"))


def test_classifies_explanation_instead_of_action_from_short_imperative_after_long_response():
    assert "explanation_instead_of_action" in classify_failure_modes(chain("fix that"))


def test_returns_unknown_when_no_rule_matches():
    assert classify_failure_modes(
        chain("what does that mean?", rejected="Answer.")
    ) == ["unknown"]
