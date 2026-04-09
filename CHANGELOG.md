# Changelog

## [1.1.0] - 2026-04-08

### Added
- **Signal detection**: 7 signal types (correction, acceptance, refinement, soft_rejection, abandonment, requery, code_execution) with regex patterns, word-boundary matching, terse correction detection
- **Confidence calibration**: Autoresearch loop using local Gemma to tune confidence weights against 1042 DPO pair outcomes. MAE reduced from 0.567 to 0.176
- **Extended thinking capture**: Chain-of-thought extraction from Claude Code transcripts (thinking blocks) and Hermes sessions (reasoning column)
- **Tool call graphs**: Structured tool invocation sequences with reasoning-before-action and result previews
- **Economics capture**: Token usage, cache hit rates, cost data, eval duration/tokens-per-second for Ollama
- **DPO pair extraction**: 1987 training pairs (720 correction chains + 1267 labeled singles) from 79 capsules
- **Cross-model comparison**: Analysis tool comparing correction rates, acceptance rates, confidence across models
- **Tool pattern analysis**: Bigram/trigram tool sequences correlated with quality outcomes
- **Hermes Agent plugin**: Auto-captures CLI and gateway sessions on end, fires via on_session_end hook
- **Gateway capture hooks**: Telegram/Discord/Slack sessions now captured at reset, /new, /resume, /branch
- **Standalone Ollama proxy**: 345-line proxy at scripts/proxy/ with zero UATP dependencies, Ed25519 signing via PyNaCl
- **Model backfill**: Script to recover model names from Claude Code JSONL transcripts (985 capsules updated)
- **Capsule rescore**: Re-runs improved signal detector on all existing capsules (14 → 5638 signals)
- **Knowledge engine**: Gold standard knowledge system with capsule-backed retrieval and autoresearch optimization
- **Quality grade from signals**: Grades now derived from actual correction/acceptance rates, not step count heuristics

### Changed
- Confidence weights calibrated: assistant_base 0.85→0.55, user_base 0.70→0.52
- ConfidenceExplainer reads from single _CONFIDENCE_WEIGHTS source of truth
- Session deduplication prevents duplicate capsules for same session
- Plugin timeout increased to 30s with graceful fallback
- Thinking stored as separate field, not concatenated into content

### Fixed
- Hardcoded user_id="kay" in rich_hook_capture.py → os.getenv("USER")
- Empty assistant messages (pure tool dispatch) filtered from reasoning steps
- Signal detector false positives on short words ("yes" in "yesterday")

## [1.0.1] - 2026-03-15

### Added
- Ed25519 local signing (Python + TypeScript SDKs)
- ML-DSA-65 post-quantum dual signing (beta)
- RFC 3161 timestamping via DigiCert TSA
- DSSE bundle export (Sigstore-compatible)
- FastAPI capsule backend with FTS5 search
- Next.js dashboard (beta)
- Claude Code hook capture (basic)
- Layered capsule structure (Events/Evidence/Interpretation/Judgment)
- Self-inspection (semantic drift, confidence-evidence alignment)
- Court-admissible enrichment framework

## [0.2.1] - 2026-03-01

- Initial PyPI release
- Basic SDK: create, sign, verify capsules
- Local key management

[Unreleased]: https://github.com/KayronCalloway/uatp/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/KayronCalloway/uatp/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/KayronCalloway/uatp/compare/v0.2.1...v1.0.1
[0.2.1]: https://github.com/KayronCalloway/uatp/releases/tag/v0.2.1
