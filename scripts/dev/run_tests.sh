#!/bin/bash
# UATP Test Runner - Sets up environment for ARM64 tests

# Set library path for post-quantum cryptography
export DYLD_LIBRARY_PATH=/Users/kay/_oqs/lib:$DYLD_LIBRARY_PATH

# Run pytest with all arguments passed through
python3 -m pytest "$@"
