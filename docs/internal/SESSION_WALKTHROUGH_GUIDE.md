#  Session Walkthrough System - Token-Saving Guide

## Purpose
Automatically generate session documentation to avoid wasting tokens on "what did we do last time?" recaps.

## How It Works

###  Automatic Generation
When you end a session, a walkthrough is **automatically created** with:
- [OK] Key accomplishments
-  Important decisions made
-  Next steps / TODOs
-  Conversation summary
-  Topics covered
-  Token usage stats

###  Storage Location
```
~/.uatp/session_walkthroughs/
```

Each walkthrough is named: `session_YYYYMMDD_HHMMSS_<session_id>.md`

## Usage

### 1️⃣ End a Session (Auto-generates walkthrough)
```bash
./end_claude_session.sh
```

**Output:**
```
 Ending Claude Code session and creating final RICH capsule...
 Created RICH capsule caps_2025_12_06_...
 Generating session walkthrough documentation...
[OK] Walkthrough saved: ~/.uatp/session_walkthroughs/session_20251206_175501_0ae4f5a2.md
[OK] Session ended. You can start a new session on your next message.
 Tip: Run './show_last_session.sh' at next session start to avoid recap!
```

### 2️⃣ Start New Session (Show last walkthrough)
```bash
./show_last_session.sh
```

**This shows you:**
- What you accomplished last time
- Where you left off
- Next steps to continue
- **Saves hundreds of tokens on recap!**

### 3️⃣ Manual Walkthrough Generation
```bash
# For current session
python3 generate_session_walkthrough.py

# For specific session
python3 generate_session_walkthrough.py <session_id>

# Show latest walkthrough
python3 generate_session_walkthrough.py --latest
```

## Example Walkthrough

```markdown
# Session Walkthrough
**Session ID:** `603f93dde5c0c436...`
**Platform:** claude-code
**Date:** 2025-12-06
**Duration:** 45 minutes
**Messages:** 23
**Tokens Used:** ~5,234
**Significance:** 0.85
**Capsule Created:** [OK] Yes

---

##  Topics Covered
- Python Programming
- API Development
- UATP System Integration

---

## [OK] Key Accomplishments

- [OK] Implemented rich capture system for Claude Code
- [OK] Integrated Antigravity with uniform metadata
- [OK] Created automatic walkthrough generator
- [OK] Set up global hooks for all projects

---

##  Important Decisions

- Decided to use hook-based capture instead of background service
- Chose to store walkthroughs in ~/.uatp/session_walkthroughs/
- Opted for markdown format for easy reading

---

##  Next Steps / TODO

- [ ] Test walkthrough generation with longer sessions
- [ ] Add support for searching past walkthroughs
- [ ] Create weekly summary generator
- [ ] Integrate with frontend for viewing

---

##  Conversation Summary

Total exchanges: 12

### Flow:
1.  Can you create an automatic walkthrough system?
2.  Absolutely! I'll create a system that generates session docs...
3.  Make it extract key accomplishments and decisions
4.  Done! Here's the walkthrough generator with...
... and 19 more messages
```

## Token Savings

### Without Walkthroughs:
```
User: "Hey, what did we work on last session?"
Assistant: "Let me recall... we worked on X, Y, Z..." (200-500 tokens)
```

### With Walkthroughs:
```
User: (reads walkthrough first - 0 tokens to Claude)
User: "Continue from step 3 in the walkthrough"
Assistant: "Got it, continuing from..." (50 tokens)
```

**Savings: 150-450 tokens per session start!**

## Advanced Usage

### Search Past Sessions
```bash
# List all walkthroughs
ls -lt ~/.uatp/session_walkthroughs/

# Search for specific topic
grep -l "API Development" ~/.uatp/session_walkthroughs/*.md

# View specific date
cat ~/.uatp/session_walkthroughs/session_20251206_*.md
```

### Integration with AI
At session start, paste the walkthrough:
```
"Here's what we did last time (see attached walkthrough).
Continue from the Next Steps section."
```

## Auto-Sync (Coming Soon)
- Weekly summary emails
- Integration with project management tools
- Searchable walkthrough database
- Team collaboration features

## Troubleshooting

### No walkthroughs generated?
Check: `tail -20 /Users/kay/uatp-capsule-engine/hook_capture.log`

### Can't find walkthrough?
```bash
ls -lt ~/.uatp/session_walkthroughs/ | head -5
```

### Want more detail?
The full conversation is always in `live_capture.db`:
```bash
sqlite3 /Users/kay/uatp-capsule-engine/live_capture.db \
  "SELECT * FROM capture_messages WHERE session_id='<id>';"
```

---

##  Best Practices

1. **End sessions properly** - Always run `./end_claude_session.sh`
2. **Review walkthrough** - Glance at it before starting new work
3. **Reference by section** - "Continue from Next Steps #3"
4. **Archive old walkthroughs** - Monthly cleanup keeps it manageable

---

**Token savings add up!** Over 20 sessions, you'll save **3,000-9,000 tokens**
