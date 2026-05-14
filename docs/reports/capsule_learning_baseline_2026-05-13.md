# Capsule Learning Baseline - 2026-05-13

## Git Status
?? docs/reports/

## Analysis Tests
...................................                                      [100%]
35 passed in 0.11s

## Capsule Learning Audit
{
  "capsule_types": {
    "claude-code-capture": 1,
    "hermes-capture": 128,
    "mcp-gateway": 10,
    "measured_outcome": 4,
    "model_self_assessment": 68,
    "ollama_conversation": 7,
    "ollama_proxy_capture": 66,
    "reasoning_trace": 1608,
    "test": 341
  },
  "capsules_total": 2233,
  "db_path": "uatp_dev.db",
  "hermes": {
    "all_signal_counts": {
      "acceptance": 53,
      "correction": 19,
      "neutral": 1061,
      "refinement": 2,
      "requery": 9,
      "soft_rejection": 2
    },
    "approx_negative_chains": 20,
    "capsules": 128,
    "meta_signal_counts": {
      "acceptance": 11,
      "correction": 4,
      "neutral": 51,
      "requery": 9,
      "soft_rejection": 1
    },
    "models_top": {
      "assistant:anthropic/claude-opus-4.7": 1,
      "assistant:anthropic/claude-sonnet-4.6": 5,
      "assistant:claude-opus-4-5-20251101": 3,
      "assistant:claude-opus-4-6": 4,
      "assistant:claude-opus-4-7": 2,
      "assistant:claude-sonnet-4-20250514": 1,
      "assistant:claude-sonnet-4-5-20250929": 2,
      "assistant:deepseek/deepseek-v4-pro": 3,
      "assistant:gpt-5.5": 60,
      "assistant:moonshotai/kimi-k2.6": 45,
      "user:deepseek/deepseek-v4-pro": 1,
      "user:moonshotai/kimi-k2.6": 1
    },
    "noisy_meta_examples": {
      "acceptance": [
        "[CONTEXT COMPACTION \u2014 REFERENCE ONLY] Earlier turns were compacted into the summary below. This is a handoff from a previous context window \u2014 treat it as background reference, NOT ",
        "[CONTEXT COMPACTION \u2014 REFERENCE ONLY] Earlier turns were compacted into the summary below. This is a handoff from a previous context window \u2014 treat it as background reference, NOT ",
        "[CONTEXT COMPACTION \u2014 REFERENCE ONLY] Earlier turns were compacted into the summary below. This is a handoff from a previous context window \u2014 treat it as background reference, NOT "
      ],
      "correction": [
        "[CONTEXT COMPACTION \u2014 REFERENCE ONLY] Earlier turns were compacted into the summary below. This is a handoff from a previous context window \u2014 treat it as background reference, NOT ",
        "[CONTEXT COMPACTION \u2014 REFERENCE ONLY] Earlier turns were compacted into the summary below. This is a handoff from a previous context window \u2014 treat it as background reference, NOT ",
        "[CONTEXT COMPACTION \u2014 REFERENCE ONLY] Earlier turns were compacted into the summary below. This is a handoff from a previous context window \u2014 treat it as background reference, NOT "
      ],
      "requery": [
        "[Your active task list was preserved across context compression]\n- [ ] h31. H3.1: verifier CLI base (pending)\n- [ ] h32. H3.2: verifier strict mode (pending)\n- [ ] h41. H4.1: safe ",
        "[Your active task list was preserved across context compression]\n- [ ] h32. H3.2: verifier strict mode (pending)\n- [ ] h41. H4.1: safe Hermes backfill (pending)\n- [ ] h5. H5: final",
        "[Your active task list was preserved across context compression]\n- [ ] h22. H2.2: verification command tagging (pending)\n- [ ] h31. H3.1: verifier CLI base (pending)\n- [ ] h32. H3."
      ],
      "soft_rejection": [
        "[Note: model was just switched from claude-opus-4-7 to gpt-5.5 via OpenAI Codex. Adjust your self-identification accordingly.]\n\nok"
      ]
    },
    "role_counts": {
      "assistant": 815,
      "user": 331
    },
    "steps_per_capsule": {
      "max": 121,
      "median": 4,
      "min": 1
    },
    "steps_total": 1146,
    "text_fields": {
      "reasoning": 1146
    },
    "user_non_neutral_rate": 0.2568,
    "user_signal_counts": {
      "acceptance": 53,
      "correction": 19,
      "neutral": 246,
      "refinement": 2,
      "requery": 9,
      "soft_rejection": 2
    }
  },
  "recommendation": {
    "next_gate": "Use cleaned correction chains and held-out evals before promotion.",
    "safe_to_finetune_raw": false,
    "safe_to_use_for_behavioral_rules": true
  }
}

## Build Learning Eval Set
{
  "models": {
    "assistant:claude-opus-4-5-20251101": 1,
    "assistant:claude-opus-4-6": 3,
    "assistant:gpt-5.5": 3,
    "assistant:moonshotai/kimi-k2.6": 2
  },
  "records": 9,
  "safe_for_behavior_eval": true,
  "safe_to_finetune_raw": false,
  "signals": {
    "correction": 8,
    "soft_rejection": 1
  }
}

## Behavior Policy Candidates
{
  "promotion_gate": {
    "baseline_pass_rate": 0.0,
    "beats_baseline": true,
    "safe_to_promote_live": false,
    "winner": "oracle_chosen",
    "winner_pass_rate": 1.0
  },
  "ranking": [
    {
      "failed": 0,
      "pass_rate": 1.0,
      "passed": 5,
      "variant": "oracle_chosen"
    },
    {
      "failed": 0,
      "pass_rate": 1.0,
      "passed": 5,
      "variant": "concise_action_bias"
    },
    {
      "failed": 1,
      "pass_rate": 0.8,
      "passed": 4,
      "variant": "overexplainer_negative_control"
    },
    {
      "failed": 5,
      "pass_rate": 0.0,
      "passed": 0,
      "variant": "baseline_rejected"
    }
  ],
  "variants": {
    "baseline_rejected": {
      "results": [
        {
          "failures": [
            "candidate_repeats_rejected_response"
          ],
          "passed": false,
          "record_id": "caps_2026_04_08_032823_20260407:12-13-15-16"
        },
        {
          "failures": [
            "candidate_repeats_rejected_response"
          ],
          "passed": false,
          "record_id": "caps_2026_04_08_032823_20260407:31-32-48-49"
        },
        {
          "failures": [
            "candidate_repeats_rejected_response"
          ],
          "passed": false,
          "record_id": "caps_2026_04_08_032823_20260407:7-8-12-13"
        },
        {
          "failures": [
            "candidate_repeats_rejected_response"
          ],
          "passed": false,
          "record_id": "caps_2026_04_10_044732_20260409:24-25-34-35"
        },
        {
          "failures": [
            "candidate_repeats_rejected_response"
          ],
          "passed": false,
          "record_id": "caps_2026_04_27_190156_20260427:21-22-23-24"
        }
      ],
      "summary": {
        "failed": 5,
        "pass_rate": 0.0,
        "passed": 0,
        "total": 5,
        "unknown_candidates": 0
      },
      "unknown_candidates": []
    },
    "concise_action_bias": {
      "results": [
        {
          "failures": [],
          "passed": true,
          "record_id": "caps_2026_04_08_032823_20260407:12-13-15-16"
        },
        {
          "failures": [],
          "passed": true,
          "record_id": "caps_2026_04_08_032823_20260407:31-32-48-49"
        },
        {
          "failures": [],
          "passed": true,
          "record_id": "caps_2026_04_08_032823_20260407:7-8-12-13"
        },
        {
          "failures": [],
          "passed": true,
          "record_id": "caps_2026_04_10_044732_20260409:24-25-34-35"
        },
        {
          "failures": [],
          "passed": true,
          "record_id": "caps_2026_04_27_190156_20260427:21-22-23-24"
        }
      ],
      "summary": {
        "failed": 0,
        "pass_rate": 1.0,
        "passed": 5,
        "total": 5,
        "unknown_candidates": 0
      },
      "unknown_candidates": []
    },
    "oracle_chosen": {
      "results": [
        {
          "failures": [],
          "passed": true,
          "record_id": "caps_2026_04_08_032823_20260407:12-13-15-16"
        },
        {
          "failures": [],
          "passed": true,
          "record_id": "caps_2026_04_08_032823_20260407:31-32-48-49"
        },
        {
          "failures": [],
          "passed": true,
          "record_id": "caps_2026_04_08_032823_20260407:7-8-12-13"
        },
        {
          "failures": [],
          "passed": true,
          "record_id": "caps_2026_04_10_044732_20260409:24-25-34-35"
        },
        {
          "failures": [],
          "passed": true,
          "record_id": "caps_2026_04_27_190156_20260427:21-22-23-24"
        }
      ],
      "summary": {
        "failed": 0,
        "pass_rate": 1.0,
        "passed": 5,
        "total": 5,
        "unknown_candidates": 0
      },
      "unknown_candidates": []
    },
    "overexplainer_negative_control": {
      "results": [
        {
          "failures": [],
          "passed": true,
          "record_id": "caps_2026_04_08_032823_20260407:12-13-15-16"
        },
        {
          "failures": [],
          "passed": true,
          "record_id": "caps_2026_04_08_032823_20260407:31-32-48-49"
        },
        {
          "failures": [],
          "passed": true,
          "record_id": "caps_2026_04_08_032823_20260407:7-8-12-13"
        },
        {
          "failures": [],
          "passed": true,
          "record_id": "caps_2026_04_10_044732_20260409:24-25-34-35"
        },
        {
          "failures": [
            "deflects_when_chosen_response_acted"
          ],
          "passed": false,
          "record_id": "caps_2026_04_27_190156_20260427:21-22-23-24"
        }
      ],
      "summary": {
        "failed": 1,
        "pass_rate": 0.8,
        "passed": 4,
        "total": 5,
        "unknown_candidates": 0
      },
      "unknown_candidates": []
    }
  }
}
