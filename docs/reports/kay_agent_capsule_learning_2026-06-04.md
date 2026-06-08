# Kay / agent learning from UATP capsules

Date: 2026-06-04
Database inspected: `uatp_dev.db`
Mode: read-only analysis. No capsule rows were modified.

## Dataset snapshot

Current capsule count: 2,540

Capsule types:

- `reasoning_trace`: 1,662
- `test`: 485
- `hermes-capture`: 237
- `model_self_assessment`: 68
- `ollama_proxy_capture`: 66
- `mcp-gateway`: 10
- `ollama_conversation`: 7
- `measured_outcome`: 4
- `claude-code-capture`: 1

Hermes-specific audit:

- Hermes capsules: 237
- Hermes steps: 2,090
- Hermes user steps: 730
- Hermes assistant steps: 1,360
- User signal counts: neutral 611, acceptance 47, correction 44, refinement 12, soft_rejection 9, code_execution 3, abandonment 4
- Approx negative Hermes chains: 49
- Clean behavior-eval records from Hermes chains: 36
- Meta/system handoff rows detected: context_compaction 67, preserved_task_list 44, model_switch 40, tool_iteration_limit 12, background_process_notification 6
- Raw fine-tuning safety: false
- Behavioral-rule mining safety: useful, but only after meta filtering and correction-chain cleaning

All-capsule text scan:

- Text items scanned from payloads and reasoning steps: 23,232
- User-like steps/messages found across all capsule types: 12,384
- Non-meta user-like messages: 12,215
- Top theme hits: local execution 10,824; UATP/capsules 7,230; memory/learning 3,827; Hermes/agent tooling 2,908; quality/slop 2,111; portfolio/creative 1,708; residuals/entertainment 1,708

Recent delta since the older 2026-05-27 report:

- Total capsules rose from 2,410 to 2,540
- Hermes capsules rose from 217 to 237
- New post-2026-05-27 examples reinforce the same pattern: `ok continue` means keep executing, and `commit and push` is an action directive, not a topic to explain.

## What I can learn about Kay

1. Kay communicates in compressed operator shorthand.

The data does not show a user who wants long explanations by default. It shows a user who often gives short, context-heavy directives and expects the agent to reconstruct the target from the working thread.

Examples/patterns:

- `ok continue`
- `fix that`
- `ok fix it`
- `commit and push`
- `no ai slop`
- `gold standard`

Working rule: short does not mean low-information. Short usually means the context is already established.

2. Kay treats quality as a system of touchpoints, not a polish pass.

The new 2026-05-28 refinement is especially important:

> what about the examining everytouchpoint and applying expert level knowledgde individually and then an experet collectively at the end

That clarifies `gold standard`: inspect each touchpoint with the relevant expert lens, then synthesize the whole artifact. It is not just “make it nicer.” It means material, structure, fit, implementation, narrative, verification, regression risk, and final user experience all count.

Working rule: when Kay invokes the standard, I need to inspect dependencies and adjacent surfaces before declaring done.

3. Kay values execution with evidence more than confidence-language.

Across the corpus, high-signal terms cluster around run/test/verify/fix/check/local/file/repo. The work style is empirical: inspect the real artifact, change it, test it, show evidence.

Working rule: avoid `should`, `probably`, `I would`, and `you can` when a tool can answer.

4. Kay’s `ok` is overloaded.

Across all scanned user messages, `ok` appears heavily and is often not acceptance.

Decoder:

- `ok` alone can mean accepted.
- `ok + continue/fix/apply/remove/run/commit/push` means act.
- `ok + what/how/can/but` means pivot or refine.

Working rule: parse the verb after `ok`, not the word `ok` by itself.

5. Kay is building a layered public/professional system, not isolated artifacts.

Theme hits show repeated overlap among UATP/capsules, Hermes/agent tooling, portfolio/creative, and residuals/entertainment. These are not separate silos. They are parts of one larger strategy: provenance infrastructure, agent learning, creative legibility, and entertainment-domain expertise.

Working rule: when changing one artifact, preserve its relationship to the broader narrative and system.

6. Kay dislikes regression more than slow progress.

A major class of corrections is not “do more”; it is “do not break the surrounding thing.” Visual and portfolio work especially shows this: Kay wants the approved idea preserved while fixing the defect.

Working rule: before editing, identify what must remain unchanged; after editing, verify those surfaces did not regress.

## What I can learn about myself as Kay’s agent

1. My biggest failure mode is explanation bias.

The report and eval both show that overexplaining loses. The behavior benchmark found:

- `concise_action_bias`: 36/36 pass
- `oracle_chosen`: 36/36 pass
- `overexplainer_negative_control`: 9/36 pass
- `baseline_rejected`: 0/36 pass

Working rule: after Kay asks to fix/apply/continue, stop explaining and execute.

2. My second biggest failure mode is not using tools soon enough.

The canonical miss was local UATP visibility: Kay asked about UATP, and the better behavior was filesystem inspection, not abstract explanation.

Working rule: local/project/file/status questions require immediate tool use.

3. My third biggest failure mode is treating visual work as code-only.

The capsule evidence around portfolio/OMA/radar corrections shows that visual work needs a render/screenshot/vision loop. Code intent is not enough.

Working rule: for visual edits, I should look at the page after each meaningful edit.

4. My fourth biggest failure mode is partial completion plus narration.

Kay’s corrections penalize doing one slice and describing the rest. If scope is clear, I should complete the whole requested slice or explicitly identify the blocker.

Working rule: do not substitute status narration for completion.

5. My fifth biggest failure mode is raw-label trust.

The capsules are useful, but raw labels still include meta/system contamination. The audit found operational messages such as context compaction and model-switch notes. Those cannot be treated as Kay feedback.

Working rule: learn from cleaned chains and verified patterns, not raw rows.

## Updated behavior policy for me

1. If Kay says `fix`, `apply`, `continue`, `do it`, `commit`, or `push`: act immediately, verify, summarize briefly.

2. If Kay says `gold standard`, `no AI slop`, `no regression`, or `my standard`: run a touchpoint-quality pass before finalizing.

3. If Kay asks whether I can see/find/access a local thing: inspect the filesystem or live system first.

4. If Kay gives visual spatial feedback: render, screenshot, inspect, then adjust geometry.

5. If Kay gives a short message after a long assistant response: treat it as a correction or next action unless it is clearly pure acceptance.

6. If a task touches UATP: use `/Users/kay/uatp-capsule-engine`, `./.venv/bin/python`, and focused tests before broad claims.

7. If a task touches portfolio/resume/public narrative: use understated, concrete, high-signal language; avoid self-promo gloss and generic AI copy.

8. If a task touches capsule learning itself: do not mutate live behavior from raw capsules. Use cleaned correction chains, held-out evals, and explicit promotion gates.

## What should become durable agent memory

Already-covered durable memories:

- Kay’s short corrections after long/tool-heavy responses are action signals.
- `gold standard/no AI slop/no regression` means preserve intent, verify, no placeholders/fake/generic work.
- UATP lives at `/Users/kay/uatp-capsule-engine`; use `./.venv/bin/python` for tests.
- Visual work needs render/screenshot/vision loops.

New or reinforced durable rule:

- Kay’s standard includes touchpoint excellence: examine each relevant touchpoint with the right expert lens individually, then synthesize collectively before deciding the final artifact is good.

## Bottom line

The capsules say the agent should be less like a commentator and more like a senior operator.

The right loop is:

1. Infer the target from context.
2. Inspect the real artifact/state.
3. Make the smallest complete fix.
4. Verify it.
5. Preserve surrounding intent.
6. Report evidence only.

Raw capsules should not be treated as training data yet, but they are strong enough to guide behavior. The strongest learned policy is concise action bias plus touchpoint-level quality control.
