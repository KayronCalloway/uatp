# UATP Capsule Engine - Quick Start (ARM64)

## System Status
🟢 **FULLY OPERATIONAL** on Apple M5 Mac (ARM64)

## What Was Fixed
- ✅ Post-quantum crypto graceful fallback in development
- ✅ All Python packages reinstalled for ARM64 (numpy, scipy, sklearn, pandas, pyarrow, psutil)
- ✅ API server verified working
- ✅ Test suite passing (3/3 basic tests)

## Quick Commands

### Start the API Server
```bash
python3 run.py
```
Access at: http://localhost:8000

### Run Tests
```bash
# Basic functionality tests
python3 -m pytest tests/test_basic_functionality.py -v

# Using the test runner (with library paths)
./run_tests.sh tests/test_basic_functionality.py -v
```

### Verify System
```bash
# Check CapsuleEngine import
python3 -c "from src.engine.capsule_engine import CapsuleEngine; print('✓ Working')"

# Check API server import
python3 -c "from src.api.server import app; print('✓ Working')"
```

## Current Configuration

**Environment**: Development
**Database**: PostgreSQL (localhost:5432)
**API Port**: 8000
**Post-Quantum Crypto**: Graceful fallback (enforced in production)

## ARM64 Package Versions
- numpy 2.3.5
- scipy 1.16.3
- scikit-learn 1.7.2
- pandas 2.3.3
- pyarrow 22.0.0
- psutil 7.1.3

## Key Files Modified
- `src/crypto/post_quantum.py` - Added graceful PQ crypto fallback
- `.env` - Documented PQ crypto status

## Development Mode
The system uses **graceful degradation** for post-quantum cryptography in development:
- Ed25519 signatures still provide cryptographic verification
- System skips PQ crypto initialization when liboqs unavailable
- Real PQ crypto (Dilithium, Kyber) is enforced in production

## Optional: Full PQ Crypto
To enable full post-quantum cryptography in development, compile liboqs for ARM64:
```bash
cd /tmp && rm -rf liboqs
git clone --depth 1 --branch 0.14.0 https://github.com/open-quantum-safe/liboqs
cd liboqs && mkdir build && cd build
CFLAGS="-arch arm64" LDFLAGS="-arch arm64" cmake -S .. -B . \
  -DCMAKE_INSTALL_PREFIX=$HOME/_oqs \
  -DCMAKE_OSX_ARCHITECTURES=arm64 \
  -DBUILD_SHARED_LIBS=ON \
  -DOQS_BUILD_ONLY_LIB=ON \
  -DOQS_MINIMAL_BUILD="KEM_kyber_512;SIG_dilithium_2"
cmake --build . --parallel 4
cmake --install .
```
Note: Takes 10-15 minutes to compile.

## Documentation
See `ARM64_MIGRATION_COMPLETE.md` for full migration details.

---
**Status**: ✅ Ready to Use
**Updated**: 2025-12-03
