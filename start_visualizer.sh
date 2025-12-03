#!/bin/bash

echo "🚀 UATP Visualizer Startup"
echo "========================="

# Kill any existing streamlit processes
pkill -f streamlit 2>/dev/null || true
sleep 2

echo "📊 Starting UATP Visualizers..."

# Start simple visualizer (guaranteed to work)
echo "   • Simple Visualizer: http://localhost:8502"
streamlit run simple_visualizer.py --server.port 8502 --server.headless true > /dev/null 2>&1 &

# Try to start full visualizer
echo "   • Full Visualizer: http://localhost:8501"
streamlit run visualizer/app.py --server.port 8501 --server.headless true > visualizer.log 2>&1 &

sleep 5

echo ""
echo "🎉 Visualizers Started!"
echo ""
echo "📋 Access Options:"
echo "   🔸 Simple Visualizer:  http://localhost:8502 (guaranteed working)"
echo "   🔸 Full Visualizer:    http://localhost:8501 (may have issues)"
echo ""
echo "💡 If the full visualizer has issues, check visualizer.log for details"
echo "   Use the simple visualizer for basic UATP exploration"
echo ""
echo "Press Ctrl+C to stop all visualizers"

# Keep script running
trap 'echo ""; echo "🛑 Stopping visualizers..."; pkill -f streamlit; exit 0' INT
wait
