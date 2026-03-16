# autoresearch-uatp

Autonomous research loop for UATP Capsule Engine - adapted from Karpathy's autoresearch pattern. The goal is continuous improvement of cryptographic verification performance, test coverage, and code quality.

**Monorepo note:** This project is self-contained. Always stage specific paths, never blind `git add -A`.

## Setup

To set up a new experiment run:

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `mar12`). The branch `autoresearch/<tag>` must not already exist.
2. **Create the branch**: `git checkout -b autoresearch/<tag>` from current main.
3. **Read the in-scope files**: The core modules for optimization:
   - `src/security/uatp_crypto_v7.py` — Ed25519 + ML-DSA-65 cryptographic operations
   - `src/export/bundle.py` — DSSE bundle export and verification
   - `src/attestation/verification.py` — attestation verification logic
   - `src/cli/verify.py` — CLI verification commands
4. **Establish baseline**: Run `./scripts/benchmark.sh` to get baseline metrics.
5. **Initialize results.tsv**: Create with header and baseline entry.
6. **Confirm and go**: Confirm setup looks good, then begin experimentation.

## Metrics

Unlike ML training, UATP targets multiple quality metrics:

```
---
test_pass_rate:   100.0%
test_count:       74
verify_time_ms:   12.3
sign_time_ms:     8.1
bundle_size_kb:   2.4
coverage_pct:     78.5
```

**Primary metric**: `test_pass_rate` (must stay at 100%)
**Optimization targets** (improve any while maintaining tests):
- `verify_time_ms` — lower is better
- `sign_time_ms` — lower is better
- `test_count` — higher is better (more coverage)
- `coverage_pct` — higher is better

## Experimentation

**What you CAN modify:**
- `src/security/uatp_crypto_v7.py` — crypto optimizations
- `src/export/bundle.py` — bundle serialization/verification
- `src/export/dsse.py` — DSSE envelope operations
- `src/attestation/*.py` — attestation logic
- `src/cli/*.py` — CLI improvements
- `src/schema/*.py` — schema optimizations
- `tests/**/*.py` — add new tests for coverage

**What you CANNOT modify:**
- `alembic/` migrations (database changes need human review)
- `src/models/` — ORM models are sensitive (see CLAUDE.md)
- External API contracts
- Do NOT add new dependencies without approval

**The goal**: Improve verification performance, add test coverage, simplify code — while keeping all tests green.

**Simplicity criterion**: All else being equal, simpler is better. A small improvement that adds complexity is not worth it. Removing code while maintaining behavior is a win.

## Output format

Run the benchmark script which outputs:

```bash
./scripts/benchmark.sh
```

Output:
```
---
test_pass_rate:   100.0%
test_count:       74
verify_time_ms:   12.3
sign_time_ms:     8.1
bundle_size_kb:   2.4
timestamp:        2026-03-12T10:30:00Z
```

## Logging results

Log experiments to `results.tsv` (tab-separated):

```
commit	test_pass_rate	verify_ms	test_count	status	description
```

1. git commit hash (short, 7 chars)
2. test pass rate (100.0 or lower if failures)
3. verify_time_ms (0.0 if tests failed)
4. test_count (number of tests)
5. status: `keep`, `discard`, or `crash`
6. short description

Example:
```
commit	test_pass_rate	verify_ms	test_count	status	description
abc1234	100.0	12.3	74	keep	baseline
def5678	100.0	10.1	74	keep	optimize ed25519 verify path
ghi9012	100.0	10.0	82	keep	add attestation edge case tests
```

## The experiment loop

LOOP FOREVER:

1. Look at the git state: current branch/commit
2. Make an improvement to the target files
3. `git add <specific files> && git commit -m "experiment: <description>"`
4. Run benchmark: `./scripts/benchmark.sh > run.log 2>&1`
5. Check results: `grep "test_pass_rate:\|verify_time_ms:\|test_count:" run.log`
6. If tests fail or crash, check `tail -n 50 run.log` and attempt fix
7. Record in results.tsv
8. If improved (tests pass AND any metric better), amend commit with tsv
9. If equal or worse, record then `git reset --hard <previous kept commit>`

**Improvement criteria**:
- Tests MUST pass (100% test_pass_rate)
- Then: lower verify_time_ms OR higher test_count OR simpler code

**Timeout**: Each experiment should take ~2-3 minutes. If a run exceeds 10 minutes, kill and discard.

**Crashes**: If tests crash (import error, etc.), fix if trivial, otherwise discard.

**NEVER STOP**: Once the loop begins, do NOT pause to ask. Run indefinitely until manually stopped. If out of ideas:
- Read test files for uncovered edge cases
- Check TODO comments in code
- Look at error handling paths
- Profile for performance bottlenecks
- Simplify complex functions

## Experiment Ideas Queue

Starting ideas to explore:
1. Cache compiled regex patterns in PII detector
2. Lazy-load nacl/cryptography modules
3. Add batch verification for multiple bundles
4. Optimize canonical JSON serialization
5. Add property-based tests with hypothesis
6. Reduce memory copies in signature verification
7. Add async variants of sync verification functions
8. Profile and optimize hot paths in DSSE PAE encoding
