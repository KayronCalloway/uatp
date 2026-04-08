#!/usr/bin/env python3
"""
Standalone Ollama Capture Proxy
================================

Transparent proxy that sits between any Ollama client and Ollama server,
capturing all interactions as signed capsules in a local SQLite database.

Architecture:
    Any App -> Proxy (:11435) -> Ollama (:11434) -> Gemma/Llama/etc
                    |
              capsules.db (signed, with economics + thinking extraction)

No UATP codebase required. Optional Ed25519 signing via PyNaCl.
"""

import argparse
import asyncio
import hashlib
import json
import logging
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from aiohttp import ClientSession, ClientTimeout, web

# Optional Ed25519 signing
try:
    from nacl.encoding import HexEncoder
    from nacl.signing import SigningKey

    _NACL = True
except ImportError:
    _NACL = False

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("ollama-proxy")

# ---------------------------------------------------------------------------
# Signing helpers
# ---------------------------------------------------------------------------


class Signer:
    """Ed25519 signer (PyNaCl) with hash-only fallback."""

    def __init__(self, key_path: str = "proxy_signing.key"):
        self.key_path = Path(key_path)
        self._sk: Optional[Any] = None
        if _NACL:
            self._init_key()

    def _init_key(self):
        if self.key_path.exists():
            self._sk = SigningKey(self.key_path.read_bytes())
            logger.info(f"Loaded signing key from {self.key_path}")
        else:
            self._sk = SigningKey.generate()
            self.key_path.write_bytes(bytes(self._sk))
            logger.info(f"Generated new signing key -> {self.key_path}")

    def sign(self, payload: dict) -> dict:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode()).hexdigest()
        result = {"content_hash": digest, "algorithm": "sha256"}
        if self._sk:
            sig = self._sk.sign(
                canonical.encode(), encoder=HexEncoder
            ).signature.decode()
            result.update(
                {
                    "signature": sig,
                    "public_key": self._sk.verify_key.encode(
                        encoder=HexEncoder
                    ).decode(),
                    "sign_algorithm": "ed25519",
                }
            )
        return result


# ---------------------------------------------------------------------------
# SQLite storage
# ---------------------------------------------------------------------------


def init_db(path: str) -> None:
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS capsules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            capsule_id TEXT UNIQUE NOT NULL,
            timestamp TEXT NOT NULL,
            model TEXT,
            prompt TEXT,
            response TEXT,
            payload JSON,
            verification JSON,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Thinking extraction
# ---------------------------------------------------------------------------

_THINK_RE = re.compile(
    r"<think(?:ing)?>(.*?)</think(?:ing)?>", re.DOTALL | re.IGNORECASE
)


def extract_thinking(text: str) -> dict:
    m = _THINK_RE.search(text)
    if not m:
        return {}
    thinking = m.group(1).strip()
    clean = _THINK_RE.sub("", text).strip()
    return {
        "thinking": thinking[:10000],
        "thinking_chars": len(thinking),
        "response_chars": len(clean),
        "ratio": round(len(thinking) / max(1, len(clean)), 2),
    }


# ---------------------------------------------------------------------------
# Economics extraction
# ---------------------------------------------------------------------------


def extract_economics(meta: dict, prompt: str, model: str) -> dict:
    ec = meta.get("eval_count", 0)
    ed = meta.get("eval_duration", 0)
    td = meta.get("total_duration", 0)
    pc = meta.get("prompt_eval_count", 0) or len(prompt.split())
    return {
        "input_tokens": pc,
        "output_tokens": ec,
        "total_tokens": pc + ec,
        "eval_duration_ns": ed,
        "total_duration_ns": td,
        "tokens_per_second": round(ec / (ed / 1e9), 1) if ed and ec else None,
        "time_to_first_token_ms": round((td - ed) / 1e6, 1) if td and ed else None,
        "model": model,
        "cost_usd": 0.0,
    }


# ---------------------------------------------------------------------------
# Proxy
# ---------------------------------------------------------------------------


class OllamaProxy:
    def __init__(
        self,
        port=11435,
        ollama_url="http://localhost:11434",
        db_path="capsules.db",
        host="127.0.0.1",
        verbose=False,
    ):
        self.port = port
        self.host = host
        self.ollama_url = ollama_url.rstrip("/")
        self.db_path = db_path
        self.verbose = verbose
        self._client: Optional[ClientSession] = None
        self._signer = Signer()
        self.stats = {"proxied": 0, "captured": 0, "started": None}
        init_db(db_path)

    # -- lifecycle ----------------------------------------------------------

    async def start(self):
        self.stats["started"] = time.time()
        self._client = ClientSession(timeout=ClientTimeout(total=300))
        app = web.Application()
        app.router.add_route("*", "/{path:.*}", self.handle)
        app.router.add_route("*", "/", self.handle)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        logger.info("=" * 55)
        logger.info("Ollama Capture Proxy (standalone)")
        logger.info("=" * 55)
        logger.info(f"Listening : http://{self.host}:{self.port}")
        logger.info(f"Upstream  : {self.ollama_url}")
        logger.info(f"Database  : {self.db_path}")
        logger.info(f"Signing   : {'Ed25519 (PyNaCl)' if _NACL else 'hash-only'}")
        logger.info("=" * 55)
        await site.start()
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
        finally:
            await self._client.close()
            await runner.cleanup()

    # -- routing ------------------------------------------------------------

    async def handle(self, req: web.Request) -> web.Response:
        path = "/" + req.match_info.get("path", "")
        self.stats["proxied"] += 1
        body = await req.read()
        target = f"{self.ollama_url}{path}"

        if path in ("/api/generate", "/api/chat") and body:
            try:
                data = json.loads(body)
                streaming = data.get("stream", True)
            except json.JSONDecodeError:
                data, streaming = {}, False
            if streaming:
                return await self._stream(req, target, body, path, data)
            else:
                return await self._non_stream(req, target, body, path, data)

        return await self._passthrough(req, target, body)

    # -- passthrough --------------------------------------------------------

    def _fwd_headers(self, req):
        return {
            k: v
            for k, v in req.headers.items()
            if k.lower() not in ("host", "content-length")
        }

    async def _passthrough(self, req, url, body):
        async with self._client.request(
            req.method, url, headers=self._fwd_headers(req), data=body
        ) as r:
            rb = await r.read()
            return web.Response(
                status=r.status,
                body=rb,
                headers={
                    k: v
                    for k, v in r.headers.items()
                    if k.lower() not in ("content-length", "transfer-encoding")
                },
            )

    # -- non-streaming capture ----------------------------------------------

    async def _non_stream(self, req, url, body, path, data):
        model = data.get("model", "unknown")
        prompt = self._extract_prompt(data, path)
        t0 = time.time()
        async with self._client.post(
            url, headers=self._fwd_headers(req), data=body
        ) as r:
            rb = await r.read()
            status = r.status
            rh = {
                k: v
                for k, v in r.headers.items()
                if k.lower() not in ("content-length", "transfer-encoding")
            }
        if status == 200:
            try:
                rd = json.loads(rb)
                resp_text = (
                    rd.get("response", "")
                    if path == "/api/generate"
                    else rd.get("message", {}).get("content", "")
                )
                meta = {
                    k: rd.get(k)
                    for k in (
                        "model",
                        "total_duration",
                        "eval_count",
                        "eval_duration",
                        "prompt_eval_count",
                    )
                }
            except json.JSONDecodeError:
                resp_text, meta = "", {}
            if resp_text:
                asyncio.create_task(
                    self._capture(
                        prompt, resp_text, model, meta, time.time() - t0, path
                    )
                )
        return web.Response(status=status, body=rb, headers=rh)

    # -- streaming capture --------------------------------------------------

    async def _stream(self, req, url, body, path, data):
        model = data.get("model", "unknown")
        prompt = self._extract_prompt(data, path)
        resp = web.StreamResponse(
            status=200, headers={"Content-Type": "application/x-ndjson"}
        )
        await resp.prepare(req)
        full = ""
        meta: Dict[str, Any] = {}
        t0 = time.time()
        async with self._client.post(
            url, headers=self._fwd_headers(req), data=body
        ) as r:
            async for line in r.content:
                await resp.write(line)
                try:
                    chunk = json.loads(line.decode())
                    if path == "/api/generate":
                        full += chunk.get("response", "")
                    else:
                        full += chunk.get("message", {}).get("content", "")
                    if chunk.get("done"):
                        meta = {
                            k: chunk.get(k)
                            for k in (
                                "model",
                                "total_duration",
                                "eval_count",
                                "eval_duration",
                                "prompt_eval_count",
                            )
                        }
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
        await resp.write_eof()
        if full:
            asyncio.create_task(
                self._capture(prompt, full, model, meta, time.time() - t0, path)
            )
        return resp

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _extract_prompt(data, path):
        if path == "/api/generate":
            return data.get("prompt", "")
        msgs = data.get("messages", [])
        return msgs[-1].get("content", "") if msgs else ""

    # -- capture & store ----------------------------------------------------

    async def _capture(self, prompt, response, model, meta, duration, endpoint):
        try:
            ts = datetime.now(timezone.utc)
            cid = f"caps_{ts.strftime('%Y_%m_%d_%H%M%S')}_{model}"
            payload = {
                "capsule_type": "ollama_proxy_capture",
                "prompt": prompt,
                "response": response,
                "model": model,
                "endpoint": endpoint,
                "timestamp": ts.isoformat(),
                "duration_s": round(duration, 3),
                "content_hash": hashlib.sha256(
                    (prompt + response).encode()
                ).hexdigest(),
                "economics": extract_economics(meta, prompt, model),
            }
            thinking = extract_thinking(response)
            if thinking:
                payload["extended_thinking"] = thinking
            verification = self._signer.sign(payload)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._store,
                cid,
                ts,
                model,
                prompt,
                response,
                payload,
                verification,
            )
            self.stats["captured"] += 1
            logger.info(
                f"[CAPTURE] {cid} | {model} | {len(prompt)}→{len(response)} chars"
            )
        except Exception as e:
            logger.error(f"Capture failed: {e}")

    def _store(self, cid, ts, model, prompt, response, payload, verification):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR IGNORE INTO capsules (capsule_id,timestamp,model,prompt,response,payload,verification) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                cid,
                ts.isoformat(),
                model,
                prompt,
                response,
                json.dumps(payload),
                json.dumps(verification),
            ),
        )
        conn.commit()
        conn.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


async def main():
    p = argparse.ArgumentParser(description="Standalone Ollama Capture Proxy")
    p.add_argument("--port", "-p", type=int, default=11435)
    p.add_argument("--ollama-url", "-u", default="http://localhost:11434")
    p.add_argument("--db", default="capsules.db", help="SQLite database path")
    p.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address (default: 127.0.0.1, use 0.0.0.0 for Docker)",
    )
    p.add_argument("--verbose", "-v", action="store_true")
    a = p.parse_args()
    if a.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    proxy = OllamaProxy(
        port=a.port,
        ollama_url=a.ollama_url,
        db_path=a.db,
        host=a.host,
        verbose=a.verbose,
    )
    try:
        await proxy.start()
    except KeyboardInterrupt:
        logger.info(f"Shutting down. Stats: {proxy.stats}")


if __name__ == "__main__":
    asyncio.run(main())
