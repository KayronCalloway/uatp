# UATP Capture Guide

## 🚨 For Life-Defining Moments

### Option 1: Use Critical Keywords (INSTANT)
Just include these words in your message for **immediate capture**:
- "life defining"
- "critical"
- "emergency"
- "important decision"
- "breakthrough"
- "capture now"
- "save this"
- "urgent"

**Example:**
```
"This is a critical decision - we need to..."
```
→ Captures **immediately**, no delay!

### Option 2: Slash Command (INSTANT)
Type in Claude Code:
```
/capture
```
→ Triggers immediate capture

### Option 3: Run Script (INSTANT)
In terminal:
```bash
cd /Users/kay/uatp-capsule-engine
./capture_now.sh
```
→ Captures immediately

### Option 4: Keyboard Shortcut (Setup)
Create macOS Quick Action:
1. Open Automator → New Quick Action
2. Add "Run Shell Script"
3. Paste:
   ```bash
   cd /Users/kay/uatp-capsule-engine && ./capture_now.sh
   ```
4. Save as "UATP Instant Capture"
5. System Settings → Keyboard → Shortcuts → Services
6. Assign hotkey (e.g., ⌘⌥C)

---

## 🔄 Normal Auto-Capture

**Throttled Capture** (every 5 interactions):
- Regular conversations
- Non-critical work
- Reduces API calls
- Still captures everything eventually

---

## 📊 Check Status

```bash
./check_capture_status.sh
```

Shows:
- Active services
- Next auto-capture countdown
- Recent capsules
- Log file locations

---

## 🎯 Best Practice

**For critical moments:**
1. Include "critical" or "capture now" in your message, OR
2. Type `/capture` immediately after, OR
3. Run `./capture_now.sh` right away

**For regular work:**
- Let auto-capture handle it (every 5 interactions)
- Everything gets captured, just slightly delayed

---

## 🔍 Verify Capture

```bash
# See recent capsules
curl -s "http://localhost:8000/capsules?limit=5" | python3 -m json.tool

# Check logs
tail -f hook_capture.log      # Auto-capture log
tail -f instant_capture.log   # Instant capture log
```

---

## 🚀 All Active Systems

1. **Antigravity** → Captures immediately when files change
2. **Claude Code Keywords** → Captures immediately on critical words
3. **Claude Code Throttled** → Captures every 5 interactions
4. **Manual Capture** → `/capture` or `./capture_now.sh`

**You're fully protected!** 🛡️
