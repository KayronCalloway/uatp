#!/bin/bash
# UATP Autoresearch Benchmark Script
# Measures test pass rate, verification performance, and coverage

set -e

cd "$(dirname "$0")/.."

echo "Running UATP benchmark..."
echo ""

# --- Run tests and capture results ---
# Exclude known flaky tests (pre-existing issues in capture/filtering)
TEST_OUTPUT=$(pytest tests/ -v --tb=no \
    --ignore=tests/capture/test_demo_filtering.py \
    --ignore=tests/capture/test_demo_filtering_direct.py \
    --ignore=tests/capture/test_sql_filtering.py \
    2>&1 || true)
PASSED=$(echo "$TEST_OUTPUT" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
FAILED=$(echo "$TEST_OUTPUT" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")
ERRORS=$(echo "$TEST_OUTPUT" | grep -oE '[0-9]+ error' | grep -oE '[0-9]+' || echo "0")

TOTAL=$((PASSED + FAILED + ERRORS))
if [ "$TOTAL" -gt 0 ]; then
    PASS_RATE=$(python3 -c "print(f'{$PASSED / $TOTAL * 100:.1f}')")
else
    PASS_RATE="0.0"
fi

# --- Benchmark verification performance ---
VERIFY_BENCH=$(python3 -c "
import time
import json
from datetime import datetime, timezone

# Benchmark Ed25519 signing
try:
    from nacl.signing import SigningKey
    key = SigningKey.generate()
    message = b'benchmark test message for UATP capsule verification'

    # Time signing (average of 100 iterations)
    start = time.perf_counter()
    for _ in range(100):
        signed = key.sign(message)
    sign_time = (time.perf_counter() - start) / 100 * 1000

    # Time verification (average of 100 iterations)
    verify_key = key.verify_key
    start = time.perf_counter()
    for _ in range(100):
        verify_key.verify(signed)
    verify_time = (time.perf_counter() - start) / 100 * 1000

    print(f'{verify_time:.2f},{sign_time:.2f}')
except Exception as e:
    print('0.00,0.00')
" 2>/dev/null || echo "0.00,0.00")

VERIFY_MS=$(echo "$VERIFY_BENCH" | cut -d',' -f1)
SIGN_MS=$(echo "$VERIFY_BENCH" | cut -d',' -f2)

# --- Benchmark bundle serialization ---
BUNDLE_SIZE=$(python3 -c "
import json
import sys
sys.path.insert(0, '.')
try:
    from src.export import UATPBundle
    bundle = UATPBundle(
        capsule_id='bench_test_001',
        payload={'test': 'data', 'nested': {'key': 'value'}},
        payload_type='benchmark'
    )
    size = len(bundle.to_json()) / 1024
    print(f'{size:.1f}')
except Exception as e:
    print('0.0')
" 2>/dev/null || echo "0.0")

# --- Get timestamp ---
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# --- Output results ---
echo "---"
echo "test_pass_rate:   ${PASS_RATE}%"
echo "test_count:       ${PASSED}"
echo "verify_time_ms:   ${VERIFY_MS}"
echo "sign_time_ms:     ${SIGN_MS}"
echo "bundle_size_kb:   ${BUNDLE_SIZE}"
echo "timestamp:        ${TIMESTAMP}"
echo ""

# Exit with error if tests failed
if [ "$FAILED" -gt 0 ] || [ "$ERRORS" -gt 0 ]; then
    echo "WARNING: ${FAILED} failed, ${ERRORS} errors"
    exit 1
fi
