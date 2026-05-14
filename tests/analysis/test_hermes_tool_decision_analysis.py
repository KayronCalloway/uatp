from scripts.analysis.hermes_failure_taxonomy import CorrectionChain
from scripts.analysis.hermes_tool_decision_analysis import analyze_tool_decisions


def test_flags_local_visibility_question_as_file_tool_miss():
    chain = CorrectionChain(
        prompt="Can you work on UATP?",
        rejected_response="UATP is a protocol concept. I can discuss it generally.",
        correction="n can you see uatp?",
        chosen_response="I checked ~/uatp-capsule-engine and found the repo.",
    )

    result = analyze_tool_decisions(chain)

    assert "should_have_used_file_tool" in result.labels
    assert "should_have_used_terminal" in result.labels


def test_flags_unverified_config_claim():
    chain = CorrectionChain(
        prompt="Update config.",
        rejected_response="The config should take effect next session.",
        correction="can you verify it works?",
        chosen_response="I ran hermes status and verified it loaded.",
    )

    result = analyze_tool_decisions(chain)

    assert "should_have_verified_after_config_change" in result.labels


def test_flags_asking_when_obvious_default_existed():
    chain = CorrectionChain(
        prompt="Is port 443 open?",
        rejected_response="Which machine do you want me to check?",
        correction="this one",
        chosen_response="I checked this machine with lsof.",
    )

    result = analyze_tool_decisions(chain)

    assert "asked_when_obvious_default_existed" in result.labels
