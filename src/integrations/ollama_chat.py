#!/usr/bin/env python3
"""
UATP Ollama Chat - Natural chat interface with automatic RAG context.

Just like `ollama run gemma4` but automatically pulls relevant files
from your codebase and injects them as context.

Usage:
    python -m src.integrations.ollama_chat
    python -m src.integrations.ollama_chat --model gemma4
    python -m src.integrations.ollama_chat --no-rag  # disable context injection
"""

import argparse
import sys
from pathlib import Path

import requests

# RAG system
from src.integrations.gemma_rag import MAX_CONTEXT_SIZE, FileIndex

# Proxy port for capture
PROXY_URL = "http://localhost:11435"
OLLAMA_URL = "http://localhost:11434"


class OllamaChat:
    """Natural chat with automatic RAG context."""

    def __init__(
        self,
        model: str = "gemma4",
        use_proxy: bool = True,
        use_rag: bool = True,
        root_path: str = ".",
        max_context_files: int = 3,
    ):
        self.model = model
        self.base_url = PROXY_URL if use_proxy else OLLAMA_URL
        self.use_rag = use_rag
        self.max_context_files = max_context_files
        self.conversation: list = []

        # Initialize file index for RAG
        if use_rag:
            print(f"Indexing codebase from {root_path}...")
            self.index = FileIndex(root_path)
            print(f"Indexed {len(self.index.files)} files")
        else:
            self.index = None

    def _get_context(self, query: str) -> tuple[str, list]:
        """Get relevant file context for the query."""
        if not self.use_rag or not self.index:
            return "", []

        files = self.index.search(query, max_files=self.max_context_files)
        if not files:
            return "", []

        context_parts = []
        file_refs = []
        total_size = 0
        max_size = MAX_CONTEXT_SIZE // 2  # Leave room for conversation

        for f in files:
            content = f["content"]
            if total_size + len(content) > max_size:
                remaining = max_size - total_size
                if remaining > 500:
                    content = content[:remaining] + "\n... [truncated]"
                else:
                    break

            context_parts.append(f"### {f['path']}\n```\n{content}\n```")
            file_refs.append(f["path"])
            total_size += len(content)

        if context_parts:
            context = "## Relevant Files\n" + "\n\n".join(context_parts)
            return context, file_refs

        return "", []

    def _spinner(self, stop_event):
        """Show a spinner while thinking."""
        import itertools

        spinner_chars = itertools.cycle(
            ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        )
        while not stop_event.is_set():
            sys.stdout.write(f"\r{next(spinner_chars)} Thinking...")
            sys.stdout.flush()
            stop_event.wait(0.1)
        sys.stdout.write("\r" + " " * 20 + "\r")  # Clear the line
        sys.stdout.flush()

    def chat(self, user_message: str) -> str:
        """Send a message and get a response."""
        import json
        import threading

        # Show searching indicator
        if self.use_rag:
            print("Searching files...", end="", flush=True)

        # Get relevant context
        context, files_used = self._get_context(user_message)

        if self.use_rag:
            if files_used:
                print(f"\r[{len(files_used)} files found]", flush=True)
            else:
                print("\r[no relevant files]", flush=True)

        # Build messages
        messages = list(self.conversation)  # Copy history

        # Add context as system message if we have it
        if context:
            # Insert context before user message
            messages.append(
                {
                    "role": "system",
                    "content": f"Use the following codebase files to help answer:\n\n{context}",
                }
            )

        messages.append({"role": "user", "content": user_message})

        # Start spinner in background
        stop_spinner = threading.Event()
        spinner_thread = threading.Thread(target=self._spinner, args=(stop_spinner,))
        spinner_thread.start()

        # Send to Ollama
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                },
                stream=True,
                timeout=120,
            )
            response.raise_for_status()

            # Stop spinner once we start getting response
            first_chunk = True

            # Stream response
            full_response = ""
            for line in response.iter_lines():
                if line:
                    if first_chunk:
                        stop_spinner.set()
                        spinner_thread.join()
                        first_chunk = False

                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        print(content, end="", flush=True)
                        full_response += content
                    if chunk.get("done"):
                        break

            # Make sure spinner is stopped
            if first_chunk:
                stop_spinner.set()
                spinner_thread.join()

            print()  # Newline after response

            # Update conversation history
            self.conversation.append({"role": "user", "content": user_message})
            self.conversation.append({"role": "assistant", "content": full_response})

            return full_response

        except requests.exceptions.ConnectionError:
            return f"Error: Cannot connect to Ollama at {self.base_url}. Is it running?"
        except Exception as e:
            return f"Error: {e}"

    def interactive(self):
        """Run interactive chat session."""
        print()
        print("=" * 60)
        print(f"UATP Ollama Chat - {self.model}")
        print("=" * 60)
        print(f"RAG: {'enabled' if self.use_rag else 'disabled'}")
        if self.index:
            print(f"Files indexed: {len(self.index.files)}")
        print(
            f"Capture: {'via proxy' if 'localhost:11435' in self.base_url else 'direct'}"
        )
        print()
        print("Commands:")
        print("  /clear  - Clear conversation history")
        print("  /rag    - Toggle RAG on/off")
        print("  /files  - Show indexed file count")
        print("  /quit   - Exit")
        print("=" * 60)
        print()

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                cmd = user_input.lower().split()[0]

                if cmd in ("/quit", "/exit", "/bye"):
                    print("Goodbye!")
                    break
                elif cmd == "/clear":
                    self.conversation = []
                    print("Conversation cleared.")
                    continue
                elif cmd == "/rag":
                    self.use_rag = not self.use_rag
                    print(f"RAG: {'enabled' if self.use_rag else 'disabled'}")
                    continue
                elif cmd == "/files":
                    if self.index:
                        print(f"Indexed {len(self.index.files)} files")
                    else:
                        print("No index (RAG disabled at startup)")
                    continue
                else:
                    print(f"Unknown command: {cmd}")
                    continue

            # Chat
            print()
            print("Gemma: ", end="")
            self.chat(user_input)
            print()


def main():
    parser = argparse.ArgumentParser(
        description="UATP Ollama Chat - Natural chat with automatic RAG"
    )
    parser.add_argument(
        "--model", "-m", default="gemma4", help="Ollama model to use (default: gemma4)"
    )
    parser.add_argument(
        "--no-rag", action="store_true", help="Disable automatic RAG context"
    )
    parser.add_argument(
        "--no-proxy", action="store_true", help="Don't use UATP proxy (skip capture)"
    )
    parser.add_argument(
        "--root",
        "-r",
        default=".",
        help="Root directory for RAG indexing (default: current)",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=3,
        help="Max files to inject per query (default: 3)",
    )

    args = parser.parse_args()

    chat = OllamaChat(
        model=args.model,
        use_proxy=not args.no_proxy,
        use_rag=not args.no_rag,
        root_path=args.root,
        max_context_files=args.max_files,
    )

    chat.interactive()


if __name__ == "__main__":
    main()
