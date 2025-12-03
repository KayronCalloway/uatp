#!/bin/bash
# UATP Auto-Capture Service Manager
# Manages the background auto-capture service using launchd

PLIST_FILE="$HOME/uatp-capsule-engine/com.uatp.auto-capture.plist"
LAUNCHD_DIR="$HOME/Library/LaunchAgents"
SERVICE_NAME="com.uatp.auto-capture"

show_status() {
    echo "================================================"
    echo "UATP Auto-Capture Service Status"
    echo "================================================"

    if launchctl list | grep -q "$SERVICE_NAME"; then
        echo "✅ Service is LOADED"

        # Check if it's actually running
        PID=$(launchctl list | grep "$SERVICE_NAME" | awk '{print $1}')
        if [ "$PID" != "-" ]; then
            echo "✅ Service is RUNNING (PID: $PID)"
        else
            echo "⚠️  Service is loaded but NOT running"
        fi
    else
        echo "❌ Service is NOT loaded"
    fi

    echo ""
    echo "Log files:"
    echo "  Output: $HOME/uatp-capsule-engine/auto-capture-out.log"
    echo "  Errors: $HOME/uatp-capsule-engine/auto-capture-err.log"
    echo "  Claude:  $HOME/uatp-capsule-engine/claude_capture.log"
}

install_service() {
    echo "📦 Installing UATP Auto-Capture Service..."

    # Create LaunchAgents directory if it doesn't exist
    mkdir -p "$LAUNCHD_DIR"

    # Copy plist file
    cp "$PLIST_FILE" "$LAUNCHD_DIR/"

    if [ $? -eq 0 ]; then
        echo "✅ Service files copied to $LAUNCHD_DIR"
        echo ""
        echo "To start the service, run:"
        echo "  ./manage-auto-capture.sh start"
    else
        echo "❌ Failed to install service"
        exit 1
    fi
}

uninstall_service() {
    echo "🗑️  Uninstalling UATP Auto-Capture Service..."

    # Stop the service first
    stop_service

    # Remove plist file
    rm -f "$LAUNCHD_DIR/$SERVICE_NAME.plist"

    if [ $? -eq 0 ]; then
        echo "✅ Service uninstalled"
    else
        echo "❌ Failed to uninstall service"
        exit 1
    fi
}

start_service() {
    echo "🚀 Starting UATP Auto-Capture Service..."

    # Check if plist exists in LaunchAgents
    if [ ! -f "$LAUNCHD_DIR/$SERVICE_NAME.plist" ]; then
        echo "⚠️  Service not installed. Installing now..."
        install_service
    fi

    # Load and start the service
    launchctl load "$LAUNCHD_DIR/$SERVICE_NAME.plist" 2>/dev/null
    launchctl start "$SERVICE_NAME" 2>/dev/null

    sleep 2
    show_status
}

stop_service() {
    echo "⏹️  Stopping UATP Auto-Capture Service..."

    launchctl stop "$SERVICE_NAME" 2>/dev/null
    launchctl unload "$LAUNCHD_DIR/$SERVICE_NAME.plist" 2>/dev/null

    echo "✅ Service stopped"
}

restart_service() {
    echo "🔄 Restarting UATP Auto-Capture Service..."
    stop_service
    sleep 2
    start_service
}

view_logs() {
    echo "📋 Viewing Auto-Capture Logs (Ctrl+C to exit)"
    echo "================================================"
    tail -f "$HOME/uatp-capsule-engine/claude_capture.log"
}

test_service() {
    echo "🧪 Testing Auto-Capture Service..."
    python3 "$HOME/uatp-capsule-engine/claude_code_auto_capture.py" &
    PID=$!
    echo "Started test process (PID: $PID)"
    echo "Waiting 10 seconds..."
    sleep 10

    if ps -p $PID > /dev/null; then
        echo "✅ Service is running successfully"
        kill $PID
        echo "Test complete (stopped test process)"
    else
        echo "❌ Service exited unexpectedly"
        echo "Check logs for errors"
    fi
}

# Main command handler
case "$1" in
    status)
        show_status
        ;;
    install)
        install_service
        ;;
    uninstall)
        uninstall_service
        ;;
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    logs)
        view_logs
        ;;
    test)
        test_service
        ;;
    *)
        echo "UATP Auto-Capture Service Manager"
        echo ""
        echo "Usage: $0 {status|install|start|stop|restart|uninstall|logs|test}"
        echo ""
        echo "Commands:"
        echo "  status     - Check if service is running"
        echo "  install    - Install service (run once)"
        echo "  start      - Start the service"
        echo "  stop       - Stop the service"
        echo "  restart    - Restart the service"
        echo "  uninstall  - Remove the service"
        echo "  logs       - View live logs"
        echo "  test       - Test if service works"
        echo ""
        echo "Example:"
        echo "  $0 install    # First time setup"
        echo "  $0 start      # Start capturing"
        echo "  $0 status     # Check if running"
        exit 1
        ;;
esac
