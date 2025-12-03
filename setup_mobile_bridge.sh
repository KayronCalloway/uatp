#!/bin/bash

# UATP Mobile Bridge Setup
# Configures network access for iPhone/iPad connections

echo "🚀 Setting up UATP Mobile Bridge..."

# 1. Find Mac IP address
MAC_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
echo "📱 Mac IP Address: $MAC_IP"

# 2. Update server configuration to accept external connections
echo "🔧 Updating server configuration..."

# Backup original run.py
cp run.py run.py.backup

# Update run.py to bind to all interfaces
sed -i '' 's/host="127.0.0.1"/host="0.0.0.0"/' run.py

# 3. Install and setup ngrok (alternative option)
if ! command -v ngrok &> /dev/null; then
    echo "📦 Installing ngrok..."
    if command -v brew &> /dev/null; then
        brew install ngrok
    else
        echo "❌ Please install Homebrew first: https://brew.sh/"
        exit 1
    fi
fi

# 4. Create start script for mobile access
cat > start_mobile_server.sh << EOF
#!/bin/bash

echo "🌐 Starting UATP server for mobile access..."

# Option 1: Direct IP access
echo "📱 Server will be available at: http://$MAC_IP:9090"
echo "🔗 Update your iOS app to use this URL"

# Start server on all interfaces
python run.py --host 0.0.0.0 --port 9090

EOF

chmod +x start_mobile_server.sh

# 5. Create ngrok tunnel script (alternative)
cat > start_ngrok_tunnel.sh << EOF
#!/bin/bash

echo "🌐 Starting ngrok tunnel for UATP..."

# Kill any existing ngrok processes
pkill ngrok

# Start ngrok tunnel
ngrok http 9090 &

# Wait for tunnel to start
sleep 3

# Get ngrok URL
NGROK_URL=\$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
tunnels = json.load(sys.stdin).get('tunnels', [])
for tunnel in tunnels:
    if tunnel.get('proto') == 'https':
        print(tunnel['public_url'])
        break
")

echo "🔗 Ngrok URL: \$NGROK_URL"
echo "📱 Use this URL in your iOS app: \$NGROK_URL"

# Keep tunnel alive
wait

EOF

chmod +x start_ngrok_tunnel.sh

# 6. Test server accessibility
echo "🧪 Testing server setup..."

# Start server in background for testing
python run.py --host 0.0.0.0 --port 9090 &
SERVER_PID=$!

# Wait for server to start
sleep 5

# Test local access
if curl -s "http://localhost:9090/api/v1/health" > /dev/null; then
    echo "✅ Local server access: OK"
else
    echo "❌ Local server access: FAILED"
fi

# Test network access
if curl -s "http://$MAC_IP:9090/api/v1/health" > /dev/null; then
    echo "✅ Network server access: OK"
else
    echo "❌ Network server access: FAILED"
    echo "🔧 Check firewall settings"
fi

# Cleanup test server
kill $SERVER_PID

# 7. Firewall instructions
echo ""
echo "🔥 FIREWALL SETUP REQUIRED:"
echo "1. Go to System Preferences > Security & Privacy > Firewall"
echo "2. Click 'Firewall Options'"
echo "3. Add Python and allow incoming connections"
echo "4. Or run: sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3"

# 8. iOS Setup Instructions
echo ""
echo "📱 iOS APP SETUP:"
echo "1. Update CaptureService baseURL to: http://$MAC_IP:9090"
echo "2. OR use ngrok: ./start_ngrok_tunnel.sh"
echo "3. Add API key to iOS app configuration"
echo "4. Test connection from iPhone Safari: http://$MAC_IP:9090/api/v1/health"

echo ""
echo "🎉 Mobile bridge setup complete!"
echo "📄 Run './start_mobile_server.sh' to start with mobile access"
echo "🌐 Run './start_ngrok_tunnel.sh' for tunnel access"