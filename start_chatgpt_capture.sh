#!/bin/bash
# Start ChatGPT Auto-Capture Proxy

export PATH="/Users/kay/Library/Python/3.12/bin:$PATH"

echo "🚀 Starting ChatGPT Auto-Capture Proxy..."
echo ""

# Check if PostgreSQL is running
if ! psql -U uatp_user -d uatp_capsule_engine -c "SELECT 1;" > /dev/null 2>&1; then
    echo "⚠️  Warning: PostgreSQL database not responding"
    echo "   Make sure database is running before using ChatGPT"
    echo ""
fi

# Start mitmdump with our addon
cd /Users/kay/uatp-capsule-engine
mitmdump -s chatgpt_proxy_addon.py -p 8888 --set block_global=false
