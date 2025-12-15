# ChatGPT Web Export Import Guide

This guide shows you how to export your ChatGPT conversations from the web and import them into UATP.

## Step 1: Export Your ChatGPT Data

1. Go to https://chat.openai.com
2. Click your **profile icon** (bottom left)
3. Click **Settings**
4. Go to **Data controls**
5. Click **Export data**
6. OpenAI will send you an email (can take a few minutes to a few hours)
7. Click the download link in the email
8. Extract the zip file - you'll get a file called `conversations.json`

## Step 2: Import to UATP

Once you have `conversations.json`:

```bash
python3 capture_chatgpt_conversations.py /path/to/conversations.json
```

For example, if you downloaded it to your Downloads folder:

```bash
python3 capture_chatgpt_conversations.py ~/Downloads/conversations.json
```

## What Gets Imported

- **All your ChatGPT conversations**
- **Full message history** for each conversation
- **Timestamps** when conversations happened
- **Conversation titles**
- **Message roles** (user/assistant)

Each conversation becomes a UATP capsule with:
- `capsule_type: "conversation"`
- `platform: "chatgpt"`
- `session_type: "chatgpt_web"`
- Cryptographic signature
- All message content

## View Imported Conversations

After import:
1. Start the frontend: `cd frontend && npm run dev`
2. Open: http://localhost:3000
3. Your ChatGPT conversations will appear alongside Claude Code conversations

## Example Output

```
======================================================================
  Importing ChatGPT Export
======================================================================

📂 Loaded export file: 145 conversations found

✅ Imported: Building a REST API with FastAPI and PostgreSQL
✅ Imported: Python async programming best practices
✅ Imported: Understanding Docker containers
...

======================================================================
✅ Import Complete: 145 conversations imported
======================================================================

🎯 View in frontend: http://localhost:3000
```

## Troubleshooting

### File not found
Make sure the path to conversations.json is correct:
```bash
# Check if file exists
ls -la ~/Downloads/conversations.json

# Use absolute path
python3 capture_chatgpt_conversations.py /Users/kay/Downloads/conversations.json
```

### Database connection error
Make sure PostgreSQL is running:
```bash
psql -U uatp_user -d uatp_capsule_engine -c "SELECT 1;"
```

### No conversations found
The export format might have changed. Check the JSON structure:
```bash
head -n 50 ~/Downloads/conversations.json
```

## Notes

- This is a **one-time import** of historical data
- Run it again with new exports to import new conversations
- Duplicates are automatically skipped (based on conversation ID)
- The script will never overwrite existing capsules

## What's Next?

After importing historical data:
- Use OpenAI API wrapper for future programmatic conversations (see OPENAI_CAPTURE_GUIDE.md)
- Continue using Claude Code (already auto-capturing)
- All conversations appear in one unified UATP system
