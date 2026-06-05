#!/bin/bash
# UATP Test Runner - Sets up environment for ARM64 tests

# Set library path for post-quantum cryptography
if [ -n "${OQS_LIB_DIR:-}" ]; then
  export DYLD_LIBRARY_PATH="$OQS_LIB_DIR:${DYLD_LIBRARY_PATH:-}"
fi

# Run pytest with all arguments passed through
python3 -m pytest "$@"
