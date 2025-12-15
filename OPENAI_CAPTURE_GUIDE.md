# OpenAI API Auto-Capture Guide

This guide shows you how to use OpenAI's API while automatically capturing all conversations to UATP capsules.

## Quick Start

### 1. Set up your OpenAI API key

```bash
# Add to .env file
echo 'OPENAI_API_KEY=sk-your-api-key-here' >> .env
```

### 2. Run the example

```bash
python3 use_openai_with_capture.py
```

This will make example API calls and automatically save them to your UATP database.

## How to Use in Your Own Code

### Option 1: Drop-in Replacement (Recommended)

Replace your normal OpenAI client with the capture-enabled version:

```python
import asyncio
from src.live_capture.openai_hook import CaptureEnabledOpenAI

async def main():
    # This replaces: from openai import OpenAI
    client = CaptureEnabledOpenAI(user_id="kay", auto_capture=True)

    # Use it exactly like the normal OpenAI client
    result = await client.chat_completion(
        messages=[
            {"role": "user", "content": "Hello!"}
        ],
        model="gpt-4"
    )

    print(result['response'])
    # 🎯 Automatically saved to UATP database!

asyncio.run(main())
```

### Option 2: Manual Capture (for existing code)

If you already have OpenAI code and don't want to rewrite it:

```python
import asyncio
from openai import OpenAI
from src.live_capture.openai_hook import capture_openai_interaction

async def main():
    # Your existing OpenAI code
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )

    # Add this line to capture it
    await capture_openai_interaction(
        user_input="Hello!",
        assistant_response=response.choices[0].message.content,
        model="gpt-4",
        user_id="kay"
    )
    # 🎯 Now it's in UATP!

asyncio.run(main())
```

### Option 3: Build Your Own ChatGPT Interface

Create your own chat interface that routes through UATP:

```python
import asyncio
from src.live_capture.openai_hook import CaptureEnabledOpenAI

async def my_chatgpt():
    client = CaptureEnabledOpenAI(user_id="kay")

    conversation = []

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit']:
            break

        conversation.append({"role": "user", "content": user_input})

        result = await client.chat_completion(
            messages=conversation,
            model="gpt-4"
        )

        ai_response = result['response']
        conversation.append({"role": "assistant", "content": ai_response})

        print(f"AI: {ai_response}")
        # 🎯 Every exchange automatically saved!

asyncio.run(my_chatgpt())
```

## What Gets Captured

Every API call captures:

- **User Input**: Your message/prompt
- **AI Response**: ChatGPT's response
- **Model**: Which model was used (gpt-4, gpt-3.5-turbo, etc.)
- **Conversation Context**: Full conversation history
- **Token Usage**: How many tokens were used
- **Timestamps**: When the interaction occurred
- **Platform**: Marked as "openai"

All of this is saved as a UATP capsule with cryptographic verification.

## View Your Captured Conversations

1. Start the frontend: `npm run dev` (in frontend/ directory)
2. Open: http://localhost:3000
3. All your OpenAI conversations will appear alongside Claude Code conversations

## Benefits

✅ **Automatic Audit Trail**: Every OpenAI interaction is logged
✅ **Compliance Ready**: Cryptographically signed capsules for regulatory proof
✅ **Attribution Tracking**: Know exactly what you asked and what the AI said
✅ **Quality Analysis**: Get quality scores for AI responses
✅ **Cross-Platform**: OpenAI + Claude Code + other platforms in one place

## Technical Details

**Storage Format**: Capsules with `capsule_type: "conversation"`
**Platform**: Tagged as `"openai"` in payload
**Database**: PostgreSQL (same as Claude Code captures)
**Real-time**: <50ms capture overhead
**Signature**: Ed25519 cryptographic signatures

## Troubleshooting

### "OPENAI_API_KEY not found"
Add your API key to `.env` file or export it:
```bash
export OPENAI_API_KEY=sk-...
```

### "OpenAI library not installed"
Install the OpenAI Python package:
```bash
pip install openai
```

### "Database connection failed"
Make sure PostgreSQL is running:
```bash
psql -U uatp_user -d uatp_capsule_engine -c "SELECT 1;"
```

## What This Does NOT Do

❌ **Does NOT capture ChatGPT web UI** (chat.openai.com) - Use web export for that
❌ **Does NOT capture ChatGPT desktop app** - Desktop app uses proprietary storage
❌ **Does NOT intercept existing app conversations** - Only captures API calls you make

This is for **programmatic use** - when you write code that calls OpenAI API.

## Next Steps

1. Run `python3 use_openai_with_capture.py` to see it in action
2. Build your own tools using `CaptureEnabledOpenAI`
3. View captured conversations in the UATP frontend
4. Get quality scores and attribution tracking automatically
