# ChatGPT Auto-Capture Proxy - Setup Guide

This guide shows you how to automatically capture ChatGPT desktop app conversations to UATP in real-time using a network proxy.

## Quick Start

### Step 1: Start the Proxy

```bash
./start_chatgpt_capture.sh
```

You should see:
```
======================================================================
  ChatGPT Auto-Capture Proxy
======================================================================

✅ Proxy server running on http://localhost:8888

📋 Configure ChatGPT Desktop App:
   ...

🎯 Listening for ChatGPT traffic...

✅ Database connected - ready to capture!
```

Keep this terminal open while using ChatGPT.

### Step 2: Configure ChatGPT Desktop App

**Option A: App Proxy Settings (if available)**

1. Open ChatGPT desktop app
2. Look for Settings → Network or Settings → Advanced
3. Set HTTP Proxy: `localhost:8888`
4. Apply settings

**Option B: System-Wide Proxy (macOS)**

If the app doesn't have proxy settings:

1. **System Preferences** → **Network**
2. Select your active connection (Wi-Fi or Ethernet)
3. Click **Advanced**
4. Go to **Proxies** tab
5. Check these boxes:
   - ☑️ Web Proxy (HTTP)
   - ☑️ Secure Web Proxy (HTTPS)
6. For both, set:
   - **Web Proxy Server**: `localhost`
   - **Port**: `8888`
7. Click **OK**, then **Apply**

**Note:** This routes ALL your system traffic through the proxy. You can disable it when not using ChatGPT.

### Step 3: Install SSL Certificate (One-Time Setup)

The ChatGPT app will likely reject the proxy's SSL certificate. You need to trust it:

1. **Generate the certificate** (run mitmproxy once):
   ```bash
   /Users/kay/Library/Python/3.12/bin/mitmproxy
   ```
   Press `q` to quit immediately

2. **Find the certificate**:
   ```bash
   open ~/.mitmproxy/
   ```
   You'll see `mitmproxy-ca-cert.pem`

3. **Install on macOS**:
   - Double-click `mitmproxy-ca-cert.pem`
   - Keychain Access will open
   - Add to "login" or "System" keychain
   - Double-click the certificate in Keychain Access
   - Expand "Trust" section
   - Set "Secure Sockets Layer (SSL)" to **Always Trust**
   - Close window (will ask for password)

4. **Restart ChatGPT app** for changes to take effect

### Step 4: Test It

1. Make sure proxy is running: `./start_chatgpt_capture.sh`
2. Open ChatGPT app
3. Send a message
4. Watch the proxy terminal - you should see:
   ```
   🔍 Intercepted chat request → gpt-4
   ✅ Captured exchange (gpt-4)
      User: What is quantum computing...
      AI: Quantum computing is...
   💾 Saved to UATP! (Conversation has 2 messages)
   ```

5. View in frontend: http://localhost:3000

## Troubleshooting

### "No traffic appearing"

**Problem:** Proxy is running but not seeing any ChatGPT requests

**Solutions:**
1. Check if app is using the proxy:
   - System-wide proxy set correctly?
   - App has proxy settings configured?
2. Check if app is actually making network requests:
   - Open Activity Monitor
   - Find ChatGPT process
   - Check Network tab
3. The app might be using a different endpoint:
   - Look at proxy logs for ANY traffic
   - Search for "openai" or "chatgpt" in URLs

### "SSL Certificate Error"

**Problem:** App shows SSL/certificate error

**Solutions:**
1. Install the certificate (see Step 3 above)
2. Make sure you set it to "Always Trust" for SSL
3. Restart the ChatGPT app
4. If still failing, the app might use certificate pinning (can't intercept)

### "Database not connected"

**Problem:** Proxy shows database connection error

**Solutions:**
```bash
# Check if PostgreSQL is running
psql -U uatp_user -d uatp_capsule_engine -c "SELECT 1;"

# If not, start it (depends on your setup)
brew services start postgresql@14
# or
pg_ctl -D /usr/local/var/postgres start
```

### "Cannot import DatabaseManager"

**Problem:** Python module errors

**Solutions:**
```bash
# Make sure you're in the project directory
cd /Users/kay/uatp-capsule-engine

# Check .env file exists
ls -la .env

# Test database connection
python3 -c "from src.database.connection import DatabaseManager; print('OK')"
```

### "mitmdump: command not found"

**Problem:** mitmproxy not in PATH

**Solutions:**
```bash
# Add to PATH permanently (add to ~/.zshrc or ~/.bash_profile)
echo 'export PATH="/Users/kay/Library/Python/3.12/bin:$PATH"' >> ~/.zshrc

# Or run with full path
/Users/kay/Library/Python/3.12/bin/mitmdump -s chatgpt_proxy_addon.py -p 8888
```

## How It Works

```
ChatGPT App → localhost:8888 (proxy) → api.openai.com
                     ↓
              Intercepts request/response
                     ↓
              Extracts conversation
                     ↓
            Saves to UATP database
```

The proxy sits between the ChatGPT app and OpenAI's servers, capturing all conversations automatically.

## What Gets Captured

Every ChatGPT exchange captures:
- **User message**
- **AI response**
- **Model used** (gpt-4, gpt-3.5-turbo, etc.)
- **Timestamp**
- **Full conversation context**
- **Conversation ID** (groups messages together)

All saved as UATP capsules with cryptographic signatures.

## Stopping the Proxy

Press `Ctrl+C` in the terminal where proxy is running.

**Don't forget to disable system proxy** if you enabled it:
- System Preferences → Network → Advanced → Proxies
- Uncheck Web Proxy and Secure Web Proxy

## Alternative: OpenAI API Method

If the proxy doesn't work (app might use certificate pinning), use the OpenAI API method instead:

See: `OPENAI_CAPTURE_GUIDE.md`

Build your own ChatGPT interface that routes through UATP - you'll have full control and automatic capture.

## Next Steps

1. Start proxy: `./start_chatgpt_capture.sh`
2. Configure app or system proxy
3. Install SSL certificate
4. Start using ChatGPT
5. View captures at http://localhost:3000

All conversations will automatically save to UATP!
