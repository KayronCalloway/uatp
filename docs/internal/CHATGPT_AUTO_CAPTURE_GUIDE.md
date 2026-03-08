# ChatGPT Desktop App - Auto-Capture Guide

This guide shows you how to automatically capture ChatGPT desktop app conversations to UATP in real-time.

## Quick Start (Easiest Method)

### Option 1: Use Chrome Extension (Recommended)

**Status:** Needs to be built (30 minutes of work)

A Chrome extension that:
- Monitors chat.openai.com (or desktop app if it uses web view)
- Captures conversations in real-time
- POSTs them to UATP API endpoint
- Works automatically in background

**To build this:**
1. Create a Chrome extension with content script
2. Inject into ChatGPT page
3. Monitor DOM for new messages
4. POST to UATP API endpoint when messages appear

This is the cleanest approach and requires no proxy setup.

### Option 2: Network Proxy (Available Now)

**What this does:**
- Runs a proxy server on your machine
- Intercepts ChatGPT app's API calls to OpenAI
- Automatically captures all conversations
- Saves to UATP database in real-time

**Setup:**

1. Install mitmproxy:
```bash
pip install mitmproxy
```

2. Run the capture proxy:
```bash
python3 chatgpt_network_capture.py
```

3. Configure ChatGPT app to use proxy:
   - Open ChatGPT desktop app
   - Go to Settings → Advanced (or Network)
   - Set HTTP Proxy: `localhost:8888`
   - Start chatting!

4. Install SSL certificate (one-time setup):
```bash
# Run mitmproxy once to generate cert
mitmproxy
# Press 'q' to quit

# Install the certificate
# macOS: Open ~/.mitmproxy/mitmproxy-ca-cert.pem and add to Keychain
# Trust it for SSL
```

**Note:** The desktop app might not have proxy settings. If not, use Option 3.

### Option 3: System-Wide Proxy

Configure your entire system to route through the proxy:

**macOS:**
1. System Preferences → Network
2. Advanced → Proxies
3. Check "Web Proxy (HTTP)"
4. Server: `localhost`, Port: `8888`
5. Apply

**Note:** This routes ALL your traffic through the proxy, which you might not want.

### Option 4: OpenAI API Wrapper (Already Built)

If you're willing to build your own ChatGPT interface instead of using the desktop app:

```python
# Use this instead of desktop app
from src.live_capture.openai_hook import CaptureEnabledOpenAI

client = CaptureEnabledOpenAI(user_id="kay")
result = await client.chat_completion(
    messages=[{"role": "user", "content": "Your message"}],
    model="gpt-4"
)
# Automatically captured!
```

See: `OPENAI_CAPTURE_GUIDE.md`

## Comparison

| Method | Ease of Setup | Real-time | Works with Desktop App |
|--------|---------------|-----------|------------------------|
| Chrome Extension |  Easy (once built) | [OK] Yes |  Maybe (if web-based) |
| Network Proxy |  Moderate | [OK] Yes | [OK] Yes |
| System Proxy |  Complex | [OK] Yes | [OK] Yes |
| API Wrapper |  Easy | [OK] Yes | [ERROR] No (new interface) |
| Web Export |  Easy | [ERROR] No (historical) | [OK] Yes |

## What I Recommend

**Best option:** Build the Chrome extension (Option 1)
- Clean, no proxy needed
- Works automatically
- Only monitors ChatGPT, not all traffic

**Available now:** Network proxy (Option 2)
- Works immediately
- Requires some setup
- Might need SSL certificate trust

**For historical data:** Web export (already set up)
- See: `CHATGPT_EXPORT_IMPORT_GUIDE.md`

## Status of Each Method

[OK] **Web Export Import** - Ready to use now
[OK] **OpenAI API Wrapper** - Ready to use now
[OK] **Network Proxy** - Ready to use now (needs mitmproxy)
[WARN] **Chrome Extension** - Need to build (30 min)
[WARN] **System Proxy** - Works but affects all traffic

## Next Steps

**To use network proxy now:**
```bash
pip install mitmproxy
python3 chatgpt_network_capture.py
```

**To build Chrome extension:**
Let me know and I'll create it - it's the cleanest solution.

**For historical import:**
```bash
# Export from chat.openai.com first
python3 capture_chatgpt_conversations.py ~/Downloads/conversations.json
```
