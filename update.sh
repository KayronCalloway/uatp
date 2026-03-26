#!/usr/bin/env bash
set -e

echo "=== UATP Update ==="

# Store current version before pull
OLD_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "none")

# Pull latest
echo "Pulling latest changes..."
git pull origin main

NEW_COMMIT=$(git rev-parse HEAD)

# Show what changed
if [ "$OLD_COMMIT" != "$NEW_COMMIT" ] && [ "$OLD_COMMIT" != "none" ]; then
  echo ""
  echo "=== Changes ==="
  git log --oneline "$OLD_COMMIT".."$NEW_COMMIT"
  echo ""
fi

# Check for breaking changes in CHANGELOG
if git diff "$OLD_COMMIT".."$NEW_COMMIT" --name-only 2>/dev/null | grep -q "CHANGELOG.md"; then
  if grep -q "Breaking Changes" CHANGELOG.md 2>/dev/null; then
    echo ""
    echo "⚠️  BREAKING CHANGES DETECTED"
    echo "================================"
    sed -n '/### Breaking Changes/,/^### /p' CHANGELOG.md | head -20
    echo ""
    read -p "Continue with update? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "Update cancelled. Review CHANGELOG.md before proceeding."
      exit 1
    fi
  fi
fi

# Run migrations if they exist
if [ -f "scripts/migrate_keys.py" ] && [ -d ".uatp_keys" ]; then
  echo ""
  echo "Checking if key migration is needed..."
  python3 -c "
from src.security.uatp_crypto_v7 import UATPCryptoV7
try:
    UATPCryptoV7()
    print('Keys OK')
except Exception as e:
    print(f'Key migration needed: {e}')
    exit(1)
" 2>/dev/null || {
    echo ""
    echo "⚠️  Key migration required"
    read -p "Run migration script? (Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
      python3 scripts/migrate_keys.py
    fi
  }
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt -q

# Frontend build
if [ -d "frontend" ]; then
  echo "Building frontend..."
  cd frontend
  npm install --silent
  npm run build
  cd ..
fi

# Docker (optional)
if [ -f "docker-compose.yml" ] && command -v docker &> /dev/null; then
  echo ""
  read -p "Restart Docker containers? (y/N) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker compose down --remove-orphans || true
    docker compose build --no-cache
    docker compose up -d
  fi
fi

echo ""
echo "=== Update complete ==="
