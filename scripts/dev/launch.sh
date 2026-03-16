#!/bin/bash
# UATP Capsule Engine Quick Launcher

echo " UATP Capsule Engine Launcher"
echo "================================"
echo ""
echo "Select launch option:"
echo "1) Full System API (port 8000)"
echo "2) Full System + Visualizer (ports 8000 + 8500)"
echo "3) Initialize DB + Start Server (port 9090)"
echo "4) Simple Mock Server (port 9090)"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo "Launching Full System API..."
        python3 launch_full_system.py
        ;;
    2)
        echo "Launching Full System + Visualizer..."
        ./start_full_system.sh
        ;;
    3)
        echo "Initializing and starting server..."
        python3 init_and_start.py
        ;;
    4)
        echo "Starting simple mock server..."
        python3 simple_api_server.py
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac
