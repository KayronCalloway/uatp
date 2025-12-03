#!/usr/bin/env python3
"""
UATP Automatic Capture Setup
Creates browser extension and iOS shortcuts for seamless conversation capture
"""

import os
import json
from pathlib import Path


def create_safari_extension():
    """Create Safari extension for automatic web capture."""

    # Create extension directory
    ext_dir = Path("safari_extension/UATP_Capture.safariextension")
    ext_dir.mkdir(parents=True, exist_ok=True)

    # Extension manifest
    manifest = {
        "CFBundleDisplayName": "UATP Capture",
        "CFBundleIdentifier": "com.uatp.capture",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "UATP Capture",
        "CFBundleShortVersionString": "1.0",
        "CFBundleVersion": "1.0",
        "Content_Scripts": [
            {
                "matches": ["https://chat.openai.com/*", "https://claude.ai/*"],
                "js": ["content.js"],
                "run_at": "document_end",
            }
        ],
        "Permissions": ["https://chat.openai.com/*", "https://claude.ai/*"],
    }

    # Content script for automatic capture
    content_script = """
// UATP Automatic Conversation Capture
(function() {
    const UATP_API = 'http://192.168.1.79:9090';
    const API_KEY = 'dev-key-001';
    
    let lastCapturedConversation = '';
    let sessionId = 'web-' + Date.now();
    
    function detectPlatform() {
        if (window.location.hostname.includes('openai.com')) return 'chatgpt';
        if (window.location.hostname.includes('claude.ai')) return 'claude';
        return 'unknown';
    }
    
    function extractConversations() {
        const platform = detectPlatform();
        let conversations = [];
        
        if (platform === 'chatgpt') {
            // ChatGPT conversation extraction
            const messages = document.querySelectorAll('[data-message-author-role]');
            messages.forEach(msg => {
                const role = msg.getAttribute('data-message-author-role');
                const content = msg.querySelector('.markdown, .whitespace-pre-wrap')?.textContent?.trim();
                if (content && content !== lastCapturedConversation) {
                    conversations.push({ role, content });
                }
            });
        } else if (platform === 'claude') {
            // Claude conversation extraction
            const messages = document.querySelectorAll('[data-is-streaming], .font-claude-message');
            messages.forEach(msg => {
                const isUser = msg.closest('[data-testid="user-message"]') !== null;
                const role = isUser ? 'user' : 'assistant';
                const content = msg.textContent?.trim();
                if (content && content !== lastCapturedConversation) {
                    conversations.push({ role, content });
                }
            });
        }
        
        return conversations;
    }
    
    async function captureMessage(role, content, platform) {
        try {
            const response = await fetch(`${UATP_API}/api/v1/live/capture/message`, {
                method: 'POST',
                headers: {
                    'X-API-Key': API_KEY,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    user_id: role === 'user' ? 'web-user' : 'ai-assistant',
                    platform: platform,
                    role: role,
                    content: content,
                    metadata: { 
                        source: 'safari_extension', 
                        url: window.location.href,
                        automatic: true 
                    }
                })
            });
            
            if (response.ok) {
                console.log('✅ UATP: Captured', role, 'message');
                showCaptureNotification();
            }
        } catch (error) {
            console.log('❌ UATP: Capture failed', error);
        }
    }
    
    function showCaptureNotification() {
        // Create subtle notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 10000;
            background: #10b981; color: white; padding: 8px 16px;
            border-radius: 8px; font-size: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            animation: fadeInOut 3s ease-in-out forwards;
        `;
        notification.textContent = '📦 UATP Captured';
        
        // Add fade animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeInOut {
                0% { opacity: 0; transform: translateY(-10px); }
                20% { opacity: 1; transform: translateY(0); }
                80% { opacity: 1; transform: translateY(0); }
                100% { opacity: 0; transform: translateY(-10px); }
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(notification);
        
        setTimeout(() => notification.remove(), 3000);
    }
    
    function monitorConversations() {
        const conversations = extractConversations();
        const platform = detectPlatform();
        
        conversations.forEach(async (conv, index) => {
            if (conv.content && conv.content.length > 10) {
                // Add small delay to avoid overwhelming the API
                setTimeout(() => {
                    captureMessage(conv.role, conv.content, platform);
                    lastCapturedConversation = conv.content;
                }, index * 500);
            }
        });
    }
    
    // Monitor for new messages
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.addedNodes.length > 0) {
                // Debounce to avoid excessive calls
                clearTimeout(window.uatpTimeout);
                window.uatpTimeout = setTimeout(monitorConversations, 1000);
            }
        });
    });
    
    // Start monitoring
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Initial capture of existing conversation
    setTimeout(monitorConversations, 2000);
    
    console.log('🚀 UATP Auto-Capture enabled for', detectPlatform());
})();
"""

    # Write files
    with open(ext_dir / "Info.plist", "w") as f:
        # Convert manifest to plist format (simplified)
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>UATP Capture</string>
    <key>CFBundleIdentifier</key>
    <string>com.uatp.capture</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>Content_Scripts</key>
    <array>
        <dict>
            <key>matches</key>
            <array>
                <string>https://chat.openai.com/*</string>
                <string>https://claude.ai/*</string>
            </array>
            <key>js</key>
            <array>
                <string>content.js</string>
            </array>
        </dict>
    </array>
</dict>
</plist>"""
        f.write(plist_content)

    with open(ext_dir / "content.js", "w") as f:
        f.write(content_script)

    return ext_dir


def create_ios_shortcut():
    """Create iOS Shortcut for automatic capture from mobile apps."""

    shortcut_dir = Path("ios_shortcuts")
    shortcut_dir.mkdir(exist_ok=True)

    # iOS Shortcut configuration
    shortcut_config = {
        "name": "UATP Auto Capture",
        "icon": "doc.text.below.ecg",
        "color": "blue",
        "actions": [
            {"type": "get_clipboard", "description": "Get conversation from clipboard"},
            {
                "type": "text_processing",
                "description": "Parse user message and AI response",
            },
            {
                "type": "http_request",
                "url": "http://192.168.1.79:9090/api/v1/live/capture/message",
                "method": "POST",
                "headers": {
                    "X-API-Key": "dev-key-001",
                    "Content-Type": "application/json",
                },
            },
        ],
    }

    # Create shortcut instructions
    instructions = """
📱 iOS Shortcut Setup Instructions

1. Open Shortcuts app on iPhone
2. Tap "+" to create new shortcut
3. Name it "UATP Auto Capture"
4. Add these actions in order:

   Action 1: "Get Clipboard"
   Action 2: "Get Text from Input" 
   Action 3: "Make HTTP Request"
      - URL: http://192.168.1.79:9090/api/v1/live/capture/message
      - Method: POST
      - Headers: 
        * X-API-Key: dev-key-001
        * Content-Type: application/json
      - Body: [Dynamic based on clipboard content]

5. Add to Share Sheet for easy access

Usage:
- In ChatGPT/Claude app: Long press conversation → Share → "UATP Auto Capture"
- Conversations automatically captured to your UATP backend
"""

    with open(shortcut_dir / "setup_instructions.txt", "w") as f:
        f.write(instructions)

    with open(shortcut_dir / "shortcut_config.json", "w") as f:
        json.dump(shortcut_config, f, indent=2)

    return shortcut_dir


def main():
    print("🚀 Setting up UATP Automatic Capture")
    print("=" * 50)

    # Create Safari extension
    print("📄 Creating Safari extension...")
    ext_dir = create_safari_extension()
    print(f"✅ Safari extension created: {ext_dir}")

    # Create iOS shortcut
    print("📱 Creating iOS shortcut...")
    shortcut_dir = create_ios_shortcut()
    print(f"✅ iOS shortcut created: {shortcut_dir}")

    print("\n🎯 Setup Complete! Next steps:")
    print("\n📄 Safari Extension (Web ChatGPT/Claude):")
    print("1. Open Safari → Develop → Web Extension Converter")
    print("2. Convert safari_extension folder to .app")
    print("3. Install on iPhone via Xcode or TestFlight")
    print("4. Enable in Safari → Extensions")

    print("\n📱 iOS Shortcut (Mobile Apps):")
    print("1. Follow instructions in ios_shortcuts/setup_instructions.txt")
    print("2. Add shortcut to Share Sheet")
    print("3. Use: Share conversation → 'UATP Auto Capture'")

    print("\n✨ Result:")
    print("• ChatGPT web: 100% automatic capture")
    print("• Claude web: 100% automatic capture")
    print("• ChatGPT app: 1-tap capture via Share")
    print("• Claude app: 1-tap capture via Share")
    print("• All data flows to your UATP backend automatically")

    print(f"\n🔗 Monitor captures at: http://localhost:3000")


if __name__ == "__main__":
    main()
