# Standalone Ollama Capture Proxy

A lightweight, standalone proxy that sits between any Ollama client and the
Ollama server, capturing every interaction as a signed capsule in a local
SQLite database. No UATP codebase required.

## Architecture

```
Any App  -->  Proxy (:11435)  -->  Ollama (:11434)  -->  Gemma/Llama/etc
                  |
            capsules.db
        (signed, with economics
         + thinking extraction)
```

## What it captures

- **Full prompt and response** text
- **Economics** — token counts, eval duration, tokens/sec, time-to-first-token
  (from Ollama API metrics in the final streaming chunk)
- **Extended thinking** — extracts `<think>` / `<thinking>` tags (Gemma 4, etc.)
- **Ed25519 signature** over the capsule payload (requires PyNaCl) or SHA-256
  content hash as fallback
- **Timestamps** and duration

## Install

```bash
cd scripts/proxy
pip install -r requirements.txt
```

PyNaCl is optional. Without it the proxy still works but capsules are
hash-only (no cryptographic signature).

## Run

```bash
# Default: listen on :11435, forward to localhost:11434
python proxy.py

# Custom ports / bind address
python proxy.py --port 8080 --ollama-url http://remote:11434 --host 0.0.0.0

# Verbose logging
python proxy.py -v
```

Then point your Ollama clients at the proxy:

```bash
export OLLAMA_HOST=http://localhost:11435
ollama run gemma4
```

Or configure VS Code / Cursor / Open WebUI to use `http://localhost:11435`.

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--port`, `-p` | 11435 | Proxy listen port |
| `--ollama-url`, `-u` | http://localhost:11434 | Upstream Ollama URL |
| `--db` | capsules.db | SQLite database path |
| `--host` | 127.0.0.1 | Bind address (use 0.0.0.0 for Docker) |
| `--verbose`, `-v` | off | Debug logging |

## Database

Capsules are stored in `capsules.db` (or the path you specify with `--db`).

```bash
# Count captured capsules
sqlite3 capsules.db "SELECT COUNT(*) FROM capsules"

# Recent captures
sqlite3 capsules.db "SELECT capsule_id, model, length(response) FROM capsules ORDER BY timestamp DESC LIMIT 10"

# View economics
sqlite3 capsules.db "SELECT capsule_id, json_extract(payload, '$.economics.tokens_per_second') as tps FROM capsules ORDER BY timestamp DESC LIMIT 5"

# View thinking extraction
sqlite3 capsules.db "SELECT capsule_id, json_extract(payload, '$.extended_thinking.thinking_chars') FROM capsules WHERE json_extract(payload, '$.extended_thinking') IS NOT NULL"
```

## Signing

On first run, the proxy generates an Ed25519 key pair saved to
`proxy_signing.key`. Each capsule payload is signed and the signature +
public key are stored in the `verification` column. If PyNaCl is not
installed, capsules still get a SHA-256 content hash.

## Differences from the full UATP proxy

This is a stripped-down standalone version. Removed:
- Self-assessment loop (model evaluating its own response)
- Calibration context injection
- LayeredCapsuleBuilder / provenance classes
- RFC 3161 timestamps
- Trust posture / quality assessment structures
- Dependency on the UATP codebase

Kept: core proxy logic, streaming support, capsule creation with signing,
economics extraction, thinking extraction, SQLite storage.
