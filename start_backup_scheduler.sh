#!/bin/bash

# UATP Database Backup Scheduler Startup Script
# ==============================================

echo "🚀 Starting UATP Database Backup Scheduler"
echo "=========================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if backup directory exists
if [ ! -d "backups" ]; then
    echo "📁 Creating backup directory..."
    mkdir -p backups
fi

# Check if backup configuration exists
if [ ! -f "backup_config.json" ]; then
    echo "⚠️  Warning: backup_config.json not found, using defaults"
fi

# Start the backup scheduler
echo "⏰ Starting backup scheduler..."
echo "   Press Ctrl+C to stop"
echo ""

python3 scripts/scheduled_backup.py

echo ""
echo "⏹️  Backup scheduler stopped"