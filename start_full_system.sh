#!/bin/bash

echo "🚀 UATP Capsule Engine - Complete System Startup"
echo "================================================="

# Kill existing processes
pkill -f streamlit 2>/dev/null || true
sleep 2

echo "📊 Starting Full UATP Visualizer..."
streamlit run robust_visualizer.py --server.port 8500 --server.headless true > visualizer.log 2>&1 &
VISUALIZER_PID=$!

sleep 3

echo ""
echo "🎉 UATP Complete System Ready!"
echo "==============================="
echo ""
echo "🔗 **Full UATP Visualizer**: http://localhost:8500"
echo ""
echo "📋 Available Features:"
echo "   🏠 System Overview      - Key metrics and system status"
echo "   🔗 Capsule Network     - Interactive relationship graphs"
echo "   🔒 Trust Monitoring    - Runtime trust enforcement data"
echo "   💰 Economic Analysis   - Fair Creator Dividend tracking"
echo "   🔍 Capsule Explorer    - Detailed capsule inspection"
echo ""
echo "🔧 System Components:"
echo "   ✅ UATP 7.0 Capsule Engine"
echo "   ✅ Runtime Trust Enforcer"
echo "   ✅ Ethics Circuit Breaker"
echo "   ✅ Economic Attribution Engine"
echo "   ✅ Governance & Voting System"
echo "   ✅ Post-Quantum Cryptography"
echo "   ✅ Zero-Knowledge Proofs"
echo "   ✅ Advanced Analytics"
echo ""
echo "💡 Navigate between views using the sidebar dropdown"
echo "📊 Sample data is pre-loaded for demonstration"
echo ""
echo "Press Ctrl+C to stop the system"

# Store PID for cleanup
echo $VISUALIZER_PID > .visualizer.pid

# Keep script running and handle cleanup
trap 'echo ""; echo "🛑 Stopping UATP system..."; kill $VISUALIZER_PID 2>/dev/null || true; rm -f .visualizer.pid; exit 0' INT
wait
