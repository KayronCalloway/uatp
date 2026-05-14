from scripts.analysis.hermes_failure_taxonomy import CorrectionChain
from scripts.analysis.hermes_token_waste import analyze_token_waste


def test_flags_long_answer_followed_by_short_correction():
    chain = CorrectionChain(
        prompt="Please inspect this.",
        rejected_response="This is a long explanation. " * 120,
        correction="fix that",
        chosen_response="Fixed and verified.",
    )

    result = analyze_token_waste(chain)

    assert "long_answer_short_correction" in result.flags
    assert result.estimated_wasted_tokens > 0


def test_flags_deflection_phrase_when_chosen_response_acted():
    chain = CorrectionChain(
        prompt="Please update the file.",
        rejected_response="I would update the file like this. Let me know if you want me to.",
        correction="ok fix everything",
        chosen_response="Updated the file and ran tests.",
    )

    result = analyze_token_waste(chain)

    assert "deflection_tokens" in result.flags
    assert "I would" in result.repeated_or_deflection_phrases


def test_does_not_flag_discussion_of_removed_placeholder_as_shipped_slop():
    chain = CorrectionChain(
        prompt="Review slop.",
        rejected_response="I removed the old placeholder implementation from the file.",
        correction="ok",
        chosen_response="Verified.",
    )

    result = analyze_token_waste(chain)

    assert "shipped_slop_tokens" not in result.flags
