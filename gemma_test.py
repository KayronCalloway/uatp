#!/usr/bin/env python3
"""
Simple Gemma file reader test.
Run from repo root: python3 gemma_test.py
"""

from pathlib import Path

import requests

BASE = Path(__file__).parent

# Use UATP proxy for automatic capture
OLLAMA_URL = "http://localhost:11435"  # proxy port


def ask_gemma(prompt: str) -> str:
    """Send prompt to Gemma via Ollama."""
    res = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": "gemma4",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        timeout=120,
    )
    return res.json()["message"]["content"]


def read_and_ask(file_path: str, question: str) -> str:
    """Read a file and ask Gemma about it."""
    full_path = BASE / file_path
    with open(full_path) as f:
        content = f.read()

    prompt = f"""You are analyzing the UATP (Unified Agent Trust Protocol) project.

Here is the source file `{file_path}`:

```
{content}
```

{question}
"""
    return ask_gemma(prompt)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Custom file and question
        file_path = sys.argv[1]
        question = sys.argv[2] if len(sys.argv) > 2 else "Explain what this file does."
    else:
        # Default: explain README
        file_path = "CLAUDE.md"
        question = "What is UATP and what are its key features? Be concise."

    print(f"📁 Reading: {file_path}")
    print(f"❓ Question: {question}")
    print("-" * 60)

    response = read_and_ask(file_path, question)
    print(response)
