#!/usr/bin/env python3
"""
Gemma RAG with UATP Provenance
==============================

Retrieval-Augmented Generation for local codebases with full provenance tracking.

Gold standard approach:
1. Index codebase files
2. Semantic/keyword retrieval to find relevant files
3. Inject file contents into prompt
4. Query Gemma via Ollama (through UATP proxy for capture)
5. Track exactly which files were used with cryptographic hashes

Usage:
    python -m src.integrations.gemma_rag "What does the provenance system do?"
    python -m src.integrations.gemma_rag "Explain the capsule format" --files src/core/
    python -m src.integrations.gemma_rag --interactive
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

# UATP proxy port for automatic capture
PROXY_URL = "http://localhost:11435"
OLLAMA_URL = "http://localhost:11434"

# File patterns to index
CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".rs",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".sql",
    ".sh",
    ".bash",
}

# Files/dirs to skip
SKIP_PATTERNS = {
    "__pycache__",
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    ".cache",
    "*.pyc",
    "*.log",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    "archive",
    ".local",
    "sdk/typescript/node_modules",
    "eggs",
    "*.egg-info",
    "htmlcov",
    ".coverage",
}

# Max file size to include (100KB)
MAX_FILE_SIZE = 100 * 1024

# Max total context size (characters)
MAX_CONTEXT_SIZE = 50000


class FileIndex:
    """Index of codebase files for retrieval."""

    def __init__(self, root_path: str = "."):
        self.root = Path(root_path).resolve()
        self.files: Dict[str, Dict[str, Any]] = {}
        self._index()

    def _should_skip(self, path: Path) -> bool:
        """Check if path should be skipped."""
        for pattern in SKIP_PATTERNS:
            if pattern in str(path):
                return True
        return False

    def _index(self):
        """Index all relevant files in the codebase."""
        for ext in CODE_EXTENSIONS:
            for file_path in self.root.rglob(f"*{ext}"):
                if self._should_skip(file_path):
                    continue
                if file_path.stat().st_size > MAX_FILE_SIZE:
                    continue

                rel_path = str(file_path.relative_to(self.root))
                try:
                    content = file_path.read_text(errors="ignore")
                    self.files[rel_path] = {
                        "path": rel_path,
                        "abs_path": str(file_path),
                        "size": len(content),
                        "hash": hashlib.sha256(content.encode()).hexdigest()[:16],
                        "content": content,
                        "keywords": self._extract_keywords(content, file_path),
                    }
                except Exception:
                    pass

    def _extract_keywords(self, content: str, path: Path) -> set:
        """Extract keywords from file for matching."""
        keywords = set()

        # Add filename parts
        keywords.update(path.stem.lower().split("_"))
        keywords.update(path.stem.lower().split("-"))

        # Add directory names
        for part in path.parts[:-1]:
            keywords.add(part.lower())

        # Extract class/function names (Python)
        if path.suffix == ".py":
            keywords.update(re.findall(r"class\s+(\w+)", content))
            keywords.update(re.findall(r"def\s+(\w+)", content))

        # Extract common terms
        words = re.findall(r"\b[a-zA-Z]{4,}\b", content.lower())
        # Count frequency and keep common ones
        word_freq = {}
        for w in words:
            word_freq[w] = word_freq.get(w, 0) + 1
        top_words = sorted(word_freq.items(), key=lambda x: -x[1])[:20]
        keywords.update(w for w, _ in top_words)

        return keywords

    def search(self, query: str, max_files: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant files based on query."""
        query_terms = set(query.lower().split())

        # Also extract key terms from query
        query_terms.update(re.findall(r"\b[a-zA-Z]{4,}\b", query.lower()))

        scored = []
        for path, info in self.files.items():
            # Score based on keyword overlap
            overlap = len(query_terms & info["keywords"])

            # Boost for path matches
            path_lower = path.lower()
            for term in query_terms:
                if term in path_lower:
                    overlap += 3

            # Boost for exact phrase in content
            if query.lower() in info["content"].lower():
                overlap += 5

            if overlap > 0:
                scored.append((overlap, path, info))

        # Sort by score descending
        scored.sort(key=lambda x: -x[0])

        return [info for _, _, info in scored[:max_files]]

    def get_files(self, paths: List[str]) -> List[Dict[str, Any]]:
        """Get specific files by path pattern."""
        results = []
        for pattern in paths:
            pattern = pattern.lower()
            for path, info in self.files.items():
                if pattern in path.lower():
                    results.append(info)
        return results


class GemmaRAG:
    """RAG system for Gemma with UATP provenance."""

    def __init__(
        self,
        root_path: str = ".",
        model: str = "gemma4",
        use_proxy: bool = True,
    ):
        self.root_path = root_path
        self.model = model
        self.base_url = PROXY_URL if use_proxy else OLLAMA_URL
        self.index = FileIndex(root_path)

        print(f"Indexed {len(self.index.files)} files from {root_path}")

    def _build_context(self, files: List[Dict[str, Any]]) -> Tuple[str, List[Dict]]:
        """Build context string from files, respecting size limits."""
        context_parts = []
        file_refs = []
        total_size = 0

        for f in files:
            content = f["content"]
            if total_size + len(content) > MAX_CONTEXT_SIZE:
                # Truncate if needed
                remaining = MAX_CONTEXT_SIZE - total_size
                if remaining > 1000:
                    content = content[:remaining] + "\n... [truncated]"
                else:
                    break

            context_parts.append(f"### File: {f['path']}\n```\n{content}\n```\n")
            file_refs.append(
                {
                    "path": f["path"],
                    "hash": f["hash"],
                    "size": f["size"],
                }
            )
            total_size += len(content)

        return "\n".join(context_parts), file_refs

    def query(
        self,
        question: str,
        file_paths: Optional[List[str]] = None,
        max_files: int = 5,
    ) -> Dict[str, Any]:
        """
        Query Gemma with relevant file context.

        Returns response with full provenance tracking.
        """
        # Get relevant files
        if file_paths:
            files = self.index.get_files(file_paths)
        else:
            files = self.index.search(question, max_files)

        if not files:
            return {
                "error": "No relevant files found",
                "query": question,
            }

        # Build context
        context, file_refs = self._build_context(files)

        # Build prompt
        prompt = f"""You are analyzing the UATP (Unified Agent Trust Protocol) codebase.

## Source Files
{context}

## Question
{question}

Provide a clear, accurate answer based on the source files above. Reference specific files when relevant."""

        # Query Gemma
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()
            answer = result.get("message", {}).get("content", "")
        except Exception as e:
            return {
                "error": f"Gemma query failed: {e}",
                "query": question,
                "files_used": file_refs,
            }

        # Build provenance record
        provenance = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": question,
            "model": self.model,
            "files_used": file_refs,
            "total_context_chars": sum(f["size"] for f in file_refs),
            "response_length": len(answer),
            "retrieval_method": "keyword_search"
            if not file_paths
            else "explicit_paths",
        }

        return {
            "answer": answer,
            "provenance": provenance,
            "files_used": [f["path"] for f in file_refs],
        }

    def interactive(self):
        """Interactive query mode."""
        print("\n" + "=" * 60)
        print("Gemma RAG - Interactive Mode")
        print("=" * 60)
        print(f"Model: {self.model}")
        print(f"Indexed files: {len(self.index.files)}")
        print(f"Using proxy: {self.base_url}")
        print("\nCommands:")
        print("  /files <pattern>  - List matching files")
        print("  /use <paths>      - Set explicit files for next query")
        print("  /clear            - Clear explicit file selection")
        print("  /quit             - Exit")
        print("=" * 60 + "\n")

        explicit_files = None

        while True:
            try:
                query = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not query:
                continue

            if query.startswith("/"):
                cmd_parts = query.split(maxsplit=1)
                cmd = cmd_parts[0].lower()
                arg = cmd_parts[1] if len(cmd_parts) > 1 else ""

                if cmd == "/quit":
                    break
                elif cmd == "/files":
                    matches = (
                        self.index.search(arg, max_files=10)
                        if arg
                        else list(self.index.files.values())[:10]
                    )
                    print(f"\nFiles ({len(matches)} shown):")
                    for f in matches:
                        print(f"  {f['path']} ({f['size']} chars)")
                    print()
                elif cmd == "/use":
                    if arg:
                        explicit_files = arg.split()
                        print(f"Will use files matching: {explicit_files}")
                    else:
                        print("Usage: /use <path1> <path2> ...")
                elif cmd == "/clear":
                    explicit_files = None
                    print("Cleared explicit file selection")
                else:
                    print(f"Unknown command: {cmd}")
                continue

            # Query Gemma
            print("\nSearching relevant files...")
            result = self.query(query, file_paths=explicit_files)

            if "error" in result:
                print(f"\nError: {result['error']}\n")
                continue

            print(f"\nFiles used: {', '.join(result['files_used'])}")
            print("\n" + "-" * 40)
            print(f"\nGemma:\n{result['answer']}\n")
            print("-" * 40)

            # Show provenance
            prov = result["provenance"]
            print(
                f"[Provenance: {prov['total_context_chars']} chars from {len(prov['files_used'])} files]"
            )
            print()


def main():
    parser = argparse.ArgumentParser(description="Gemma RAG with UATP Provenance")
    parser.add_argument("query", nargs="?", help="Question to ask about the codebase")
    parser.add_argument(
        "--files", "-f", nargs="+", help="Specific file paths/patterns to include"
    )
    parser.add_argument(
        "--root", "-r", default=".", help="Root directory to index (default: current)"
    )
    parser.add_argument(
        "--model", "-m", default="gemma4", help="Ollama model (default: gemma4)"
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Interactive mode"
    )
    parser.add_argument(
        "--no-proxy", action="store_true", help="Don't use UATP proxy (skip capture)"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=5,
        help="Max files to include in context (default: 5)",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output as JSON (includes full provenance)"
    )

    args = parser.parse_args()

    rag = GemmaRAG(
        root_path=args.root,
        model=args.model,
        use_proxy=not args.no_proxy,
    )

    if args.interactive:
        rag.interactive()
    elif args.query:
        result = rag.query(
            args.query,
            file_paths=args.files,
            max_files=args.max_files,
        )

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if "error" in result:
                print(f"Error: {result['error']}")
                sys.exit(1)

            print(f"\n📁 Files used: {', '.join(result['files_used'])}\n")
            print("-" * 60)
            print(result["answer"])
            print("-" * 60)
            print(
                f"\n📋 Provenance: {result['provenance']['total_context_chars']} chars"
            )
            print(f"   from {len(result['provenance']['files_used'])} files")
            for f in result["provenance"]["files_used"]:
                print(f"   - {f['path']} (sha256:{f['hash']})")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
