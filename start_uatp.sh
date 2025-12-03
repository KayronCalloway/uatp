#!/bin/bash

# UATP Capsule Engine Quick Start Script

echo "🚀 Starting UATP Capsule Engine Services"
echo "========================================"

# Change to project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if visualizer is running
if pgrep -f "streamlit.*visualizer/app.py" > /dev/null; then
    echo "✅ Visualizer already running at http://localhost:8501"
else
    echo "📊 Starting Visualizer..."
    streamlit run visualizer/app.py --server.headless true --server.port 8501 > /dev/null 2>&1 &
    echo "✅ Visualizer started at http://localhost:8501"
fi

# For now, let's focus on the visualizer since the API has dependency issues
echo ""
echo "🎉 UATP Services Status:"
echo "   📊 Visualizer: http://localhost:8501"
echo "   ⚠️  API Server: Dependency issues - run 'pip install --upgrade redis' to fix"
echo ""
echo "📋 Available Features in Visualizer:"
echo "   • Capsule Chain Visualization"
echo "   • Trust and Security Monitoring"
echo "   • Economic Attribution Analysis"
echo "   • Interactive Capsule Explorer"
echo ""
echo "Press Ctrl+C to stop services"

# Keep script running
trap 'echo ""; echo "🛑 Stopping services..."; pkill -f "streamlit.*visualizer"; exit 0' INT
wait
