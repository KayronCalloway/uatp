#!/usr/bin/env bash
set -e

echo "Updating UATP..."

git pull origin main

pip install -r requirements.txt -q

# Run key migration if needed
if [ -d ".uatp_keys" ]; then
  python3 -c "from src.security.uatp_crypto_v7 import UATPCryptoV7; UATPCryptoV7()" 2>/dev/null || {
    echo "Running key migration..."
    python3 scripts/migrate_keys.py
  }
fi

if [ -d "frontend" ]; then
  cd frontend && npm install --silent && npm run build && cd ..
fi

echo "Done."
