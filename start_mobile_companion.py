#!/usr/bin/env python3
import http.server
import socketserver
import os

os.chdir("mobile_companion")

PORT = 3001
Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"🚀 UATP Mobile Companion running at:")
    print(f"📱 iPhone: http://YOUR_MAC_IP:3001")
    print(f"💻 Desktop: http://localhost:3001")
    print(f"")
    print(f"📋 Instructions:")
    print(f"1. Open the URL on your iPhone")
    print(f"2. Tap 'Share' → 'Add to Home Screen'")
    print(f"3. Now it works like a native app!")
    httpd.serve_forever()
