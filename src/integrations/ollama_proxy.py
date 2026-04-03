#!/usr/bin/env python3
"""
UATP Ollama Proxy - Transparent Capture for All Ollama Traffic
===============================================================

A transparent proxy that sits between any Ollama client and the Ollama server,
capturing ALL interactions as signed UATP capsules.

Architecture:
    Any App → UATP Proxy (:11435) → Ollama (:11434) → Gemma/Llama/etc
                    ↓
              UATP Capsule (signed, timestamped, layered format)

Usage:
    # Start the proxy
    python -m src.integrations.ollama_proxy

    # Configure clients to use the proxy
    export OLLAMA_HOST=http://localhost:11435

    # Now ANY Ollama client automatically gets captured:
    # - ollama run gemma4
    # - VS Code Ollama extension
    # - Cursor with Ollama
    # - Web UIs like Open WebUI
    # - Python scripts using ollama library

Options:
    --port PORT         Proxy listen port (default: 11435)
    --ollama-url URL    Upstream Ollama URL (default: http://localhost:11434)
    --assess            Auto-trigger self-assessment after each response
    --verbose           Enable verbose logging
"""

import argparse
import asyncio
import hashlib
import json
import logging
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# HTTP server
from aiohttp import ClientSession, ClientTimeout, web

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# UATP imports
try:
    from src.core.layered_capsule_builder import LayeredCapsuleBuilder
    from src.core.provenance import EpistemicClass, Event, Evidence, ProofLevel
    from src.security.rfc3161_timestamps import RFC3161Timestamper
    from src.security.uatp_crypto_v7 import UATPCryptoV7

    _UATP_AVAILABLE = True
except ImportError as e:
    logger.warning(f"UATP modules not available: {e}")
    _UATP_AVAILABLE = False
    EpistemicClass = None


# Self-assessment prompt
SELF_ASSESSMENT_PROMPT = """
Review your previous response and provide a structured self-assessment.

IMPORTANT: DO NOT defend your answer. BE HONEST about limitations.
This assessment will be compared against actual outcomes to measure your calibration.

Respond in this exact JSON format (no other text):
{
    "confidence_estimate": <float 0.0-1.0>,
    "grounding_sources": ["<list what you based this on>"],
    "assumptions_made": ["<list assumptions that might be wrong>"],
    "uncertainty_areas": ["<where you're least sure>"],
    "potential_errors": ["<what could be wrong>"],
    "would_change_if": ["<conditions that would change your answer>"],
    "verification_needed": ["<what should be checked>"]
}
"""


class OllamaProxy:
    """Transparent proxy for Ollama with UATP capture."""

    def __init__(
        self,
        proxy_port: int = 11435,
        ollama_url: str = "http://localhost:11434",
        db_path: str = "uatp_dev.db",
        auto_assess: bool = False,
        verbose: bool = False,
    ):
        self.proxy_port = proxy_port
        self.ollama_url = ollama_url.rstrip("/")
        self.db_path = db_path
        self.auto_assess = auto_assess
        self.verbose = verbose

        # HTTP client session (created on startup)
        self._client: Optional[ClientSession] = None

        # Crypto for signing
        self._crypto = None
        if _UATP_AVAILABLE:
            try:
                self._crypto = UATPCryptoV7(
                    key_dir=".uatp_keys",
                    signer_id="ollama_proxy",
                    enable_pq=True,
                )
                logger.info("Crypto initialized for signing")
            except Exception as e:
                logger.warning(f"Crypto initialization failed: {e}")

        # Stats
        self.requests_proxied = 0
        self.capsules_created = 0
        self.start_time = None

    async def start(self):
        """Start the proxy server."""
        self.start_time = time.time()

        # Create HTTP client
        timeout = ClientTimeout(total=300)  # 5 min timeout for long generations
        self._client = ClientSession(timeout=timeout)

        # Create web app
        app = web.Application()

        # Route all requests through proxy
        app.router.add_route("*", "/{path:.*}", self.handle_request)
        app.router.add_route("*", "/", self.handle_request)

        # Start server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.proxy_port)

        logger.info("=" * 60)
        logger.info("UATP Ollama Proxy")
        logger.info("=" * 60)
        logger.info(f"Proxy listening on: http://localhost:{self.proxy_port}")
        logger.info(f"Forwarding to Ollama: {self.ollama_url}")
        logger.info(f"Auto-assessment: {'enabled' if self.auto_assess else 'disabled'}")
        logger.info("")
        logger.info(
            "To use, set: export OLLAMA_HOST=http://localhost:{self.proxy_port}"
        )
        logger.info("Or configure your Ollama client to use this URL")
        logger.info("=" * 60)

        await site.start()

        # Keep running
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
        finally:
            await self._client.close()
            await runner.cleanup()

    async def handle_request(self, request: web.Request) -> web.Response:
        """Handle incoming request - proxy and optionally capture."""
        path = "/" + request.match_info.get("path", "")
        method = request.method
        self.requests_proxied += 1

        if self.verbose:
            logger.info(f"[PROXY] {method} {path}")

        # Read request body
        body = await request.read()

        # Determine if this is a capturable endpoint
        capturable = path in ("/api/generate", "/api/chat")
        is_streaming = False

        if capturable and body:
            try:
                req_data = json.loads(body)
                is_streaming = req_data.get(
                    "stream", True
                )  # Ollama defaults to streaming
            except json.JSONDecodeError:
                pass

        # Forward to Ollama
        target_url = f"{self.ollama_url}{path}"

        try:
            if capturable:
                if is_streaming:
                    # Handle streaming response with capture
                    return await self._handle_streaming(request, target_url, body, path)
                else:
                    # Handle non-streaming response with capture
                    return await self._handle_non_streaming(
                        request, target_url, body, path
                    )
            else:
                # Simple proxy for non-capturable endpoints
                return await self._simple_proxy(request, target_url, body)

        except Exception as e:
            logger.error(f"Proxy error: {e}")
            return web.Response(
                status=502,
                text=json.dumps({"error": f"Proxy error: {str(e)}"}),
                content_type="application/json",
            )

    async def _simple_proxy(
        self, request: web.Request, target_url: str, body: bytes
    ) -> web.Response:
        """Simple request forwarding without capture."""
        headers = {
            k: v
            for k, v in request.headers.items()
            if k.lower() not in ("host", "content-length")
        }

        async with self._client.request(
            request.method,
            target_url,
            headers=headers,
            data=body,
        ) as resp:
            response_body = await resp.read()
            return web.Response(
                status=resp.status,
                body=response_body,
                headers={
                    k: v
                    for k, v in resp.headers.items()
                    if k.lower() not in ("content-length", "transfer-encoding")
                },
            )

    async def _handle_non_streaming(
        self,
        request: web.Request,
        target_url: str,
        body: bytes,
        path: str,
    ) -> web.Response:
        """Handle non-streaming response with UATP capture."""
        headers = {
            k: v
            for k, v in request.headers.items()
            if k.lower() not in ("host", "content-length")
        }

        # Parse request
        try:
            req_data = json.loads(body)
        except json.JSONDecodeError:
            req_data = {}

        # Extract prompt/messages
        if path == "/api/generate":
            prompt = req_data.get("prompt", "")
            model = req_data.get("model", "unknown")
        else:  # /api/chat
            messages = req_data.get("messages", [])
            prompt = messages[-1].get("content", "") if messages else ""
            model = req_data.get("model", "unknown")

        capture_start = time.time()

        # Forward to Ollama
        async with self._client.request(
            "POST",
            target_url,
            headers=headers,
            data=body,
        ) as resp:
            response_body = await resp.read()
            status = resp.status
            resp_headers = {
                k: v
                for k, v in resp.headers.items()
                if k.lower() not in ("content-length", "transfer-encoding")
            }

        # Parse response for capture
        full_response = ""
        response_metadata = {}

        if status == 200:
            try:
                resp_data = json.loads(response_body)
                if path == "/api/generate":
                    full_response = resp_data.get("response", "")
                    response_metadata = {
                        "model": resp_data.get("model"),
                        "created_at": resp_data.get("created_at"),
                        "total_duration": resp_data.get("total_duration"),
                        "eval_count": resp_data.get("eval_count"),
                    }
                else:  # /api/chat
                    full_response = resp_data.get("message", {}).get("content", "")
                    response_metadata = {
                        "model": resp_data.get("model"),
                        "created_at": resp_data.get("created_at"),
                        "total_duration": resp_data.get("total_duration"),
                    }
            except json.JSONDecodeError:
                pass

        # Capture as UATP capsule (async)
        if full_response:
            asyncio.create_task(
                self._capture_interaction(
                    prompt=prompt,
                    response=full_response,
                    model=model,
                    metadata=response_metadata,
                    duration=time.time() - capture_start,
                    endpoint=path,
                    request_data=req_data,
                )
            )

        return web.Response(
            status=status,
            body=response_body,
            headers=resp_headers,
        )

    async def _handle_streaming(
        self,
        request: web.Request,
        target_url: str,
        body: bytes,
        path: str,
    ) -> web.StreamResponse:
        """Handle streaming response with UATP capture."""
        headers = {
            k: v
            for k, v in request.headers.items()
            if k.lower() not in ("host", "content-length")
        }

        # Parse request
        try:
            req_data = json.loads(body)
        except json.JSONDecodeError:
            req_data = {}

        # Extract prompt/messages
        if path == "/api/generate":
            prompt = req_data.get("prompt", "")
            model = req_data.get("model", "unknown")
        else:  # /api/chat
            messages = req_data.get("messages", [])
            prompt = messages[-1].get("content", "") if messages else ""
            model = req_data.get("model", "unknown")

        # Prepare streaming response
        response = web.StreamResponse(
            status=200, headers={"Content-Type": "application/x-ndjson"}
        )
        await response.prepare(request)

        # Collect full response while streaming
        full_response = ""
        response_metadata = {}
        capture_start = time.time()

        async with self._client.request(
            "POST",
            target_url,
            headers=headers,
            data=body,
        ) as resp:
            async for line in resp.content:
                # Forward to client immediately
                await response.write(line)

                # Parse and collect response
                try:
                    chunk = json.loads(line.decode())

                    if path == "/api/generate":
                        full_response += chunk.get("response", "")
                        if chunk.get("done"):
                            response_metadata = {
                                "model": chunk.get("model"),
                                "created_at": chunk.get("created_at"),
                                "total_duration": chunk.get("total_duration"),
                                "eval_count": chunk.get("eval_count"),
                                "eval_duration": chunk.get("eval_duration"),
                            }
                    else:  # /api/chat
                        msg = chunk.get("message", {})
                        full_response += msg.get("content", "")
                        if chunk.get("done"):
                            response_metadata = {
                                "model": chunk.get("model"),
                                "created_at": chunk.get("created_at"),
                                "total_duration": chunk.get("total_duration"),
                                "eval_count": chunk.get("eval_count"),
                                "eval_duration": chunk.get("eval_duration"),
                            }
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass

        await response.write_eof()

        # Capture as UATP capsule (async, don't block response)
        asyncio.create_task(
            self._capture_interaction(
                prompt=prompt,
                response=full_response,
                model=model,
                metadata=response_metadata,
                duration=time.time() - capture_start,
                endpoint=path,
                request_data=req_data,
            )
        )

        return response

    async def _capture_interaction(
        self,
        prompt: str,
        response: str,
        model: str,
        metadata: Dict[str, Any],
        duration: float,
        endpoint: str,
        request_data: Dict[str, Any],
    ):
        """Capture interaction as UATP capsule."""
        try:
            capsule_id = self._create_capsule(
                prompt=prompt,
                response=response,
                model=model,
                metadata=metadata,
                endpoint=endpoint,
            )

            if capsule_id:
                self.capsules_created += 1
                logger.info(
                    f"[CAPTURE] {capsule_id} | {model} | {len(prompt)} chars → {len(response)} chars"
                )

                # Auto-assessment if enabled
                if self.auto_assess and _UATP_AVAILABLE:
                    asyncio.create_task(
                        self._capture_self_assessment(
                            capsule_id=capsule_id,
                            original_prompt=prompt,
                            original_response=response,
                            model=model,
                        )
                    )

        except Exception as e:
            logger.error(f"Capture failed: {e}")

    def _create_capsule(
        self,
        prompt: str,
        response: str,
        model: str,
        metadata: Dict[str, Any],
        endpoint: str,
    ) -> Optional[str]:
        """Create and store a UATP capsule."""
        if not _UATP_AVAILABLE:
            return None

        timestamp = datetime.now(timezone.utc)
        capsule_id = f"caps_{timestamp.strftime('%Y_%m_%d_%H%M%S')}_{model}"

        # Build events
        events = [
            Event(
                event_type="user_prompt",
                timestamp=timestamp,
                data={"content": prompt, "source": "ollama_proxy"},
                proof=ProofLevel.TOOL_VERIFIED,
                epistemic_class=EpistemicClass.TOOL_OBSERVED,
            ),
            Event(
                event_type="model_response",
                timestamp=timestamp,
                data={
                    "content": response[:1000] + "..."
                    if len(response) > 1000
                    else response,
                    "model": model,
                    "endpoint": endpoint,
                },
                proof=ProofLevel.TOOL_VERIFIED,
                epistemic_class=EpistemicClass.TOOL_OBSERVED,
            ),
        ]

        # Build evidence
        content_hash = hashlib.sha256((prompt + response).encode()).hexdigest()

        evidence = [
            Evidence(
                claim="Interaction content hash",
                verified=True,
                proof=ProofLevel.CRYPTO_VERIFIED,
                artifact=content_hash,
                verification_method="sha256_hash",
            ),
        ]

        # Create payload with layered structure
        payload = {
            "schema_version": "2.0_layered",
            "capsule_type": "ollama_proxy_capture",
            "prompt": prompt,
            "response": response,
            "model": model,
            "metadata": metadata,
            "layers": {
                "events": [e.to_dict() for e in events],
                "evidence": [e.to_dict() for e in evidence],
                "interpretation": {
                    "summary": f"Ollama {model} response captured via proxy",
                    "claims": [],
                    "status": "unverified",
                    "epistemic_class": "model_claim",
                },
                "judgment": {
                    "gates_passed": ["provenance_complete", "interpretation_separated"],
                    "court_admissible": False,
                    "blockers": ["Missing external timestamp verification"],
                },
            },
            "trust_posture": {
                "provenance_integrity": "medium",
                "artifact_verifiability": "high",
                "semantic_alignment": "unknown",
                "decision_completeness": "low",
                "risk_calibration": "low",
                "legal_reliance_readiness": "not_ready",
                "operational_utility": "high",
            },
        }

        # Sign using UATP v7 crypto
        verification = {}
        if self._crypto:
            try:
                verification = self._crypto.sign_capsule(
                    payload, timestamp_mode="local"
                )
            except Exception as e:
                logger.warning(f"Signing failed: {e}")

        # Store
        self._save_capsule(
            capsule_id=capsule_id,
            timestamp=timestamp,
            capsule_type="ollama_proxy_capture",
            payload=payload,
            verification=verification,
            model=model,
        )

        return capsule_id

    async def _capture_self_assessment(
        self,
        capsule_id: str,
        original_prompt: str,
        original_response: str,
        model: str,
    ):
        """Trigger and capture self-assessment."""
        try:
            # Build assessment request
            messages = [
                {"role": "user", "content": original_prompt},
                {"role": "assistant", "content": original_response},
                {"role": "user", "content": SELF_ASSESSMENT_PROMPT},
            ]

            # Call Ollama directly (not through proxy to avoid infinite loop)
            async with self._client.post(
                f"{self.ollama_url}/api/chat",
                json={"model": model, "messages": messages, "stream": False},
            ) as resp:
                if resp.status != 200:
                    return

                result = await resp.json()
                assessment_text = result.get("message", {}).get("content", "")

            # Parse assessment
            assessment = self._parse_assessment(assessment_text)

            # Create assessment capsule
            self._create_assessment_capsule(
                parent_capsule_id=capsule_id,
                assessment=assessment,
                raw_text=assessment_text,
                model=model,
            )

            if assessment.get("confidence_estimate"):
                logger.info(
                    f"[ASSESS] {capsule_id}_self | confidence={assessment['confidence_estimate']}"
                )

        except Exception as e:
            logger.warning(f"Self-assessment capture failed: {e}")

    def _parse_assessment(self, text: str) -> Dict[str, Any]:
        """Parse self-assessment JSON from model response."""
        try:
            # Try to find JSON in the response
            json_match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

        # Try the whole text
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        return {"raw_response": text}

    def _create_assessment_capsule(
        self,
        parent_capsule_id: str,
        assessment: Dict[str, Any],
        raw_text: str,
        model: str,
    ):
        """Create self-assessment capsule linked to parent."""
        if not _UATP_AVAILABLE:
            return

        timestamp = datetime.now(timezone.utc)
        capsule_id = f"{parent_capsule_id}_self"

        payload = {
            "schema_version": "2.0_layered",
            "capsule_type": "model_self_assessment",
            "epistemic_class": "model_self_assessment",
            "assessment": assessment,
            "raw_response": raw_text,
            "layers": {
                "events": [
                    {
                        "event_type": "self_assessment_request",
                        "timestamp": timestamp.isoformat(),
                        "data": {"parent_capsule_id": parent_capsule_id},
                        "proof": "tool_verified",
                        "epistemic_class": "tool_observed",
                    }
                ],
                "evidence": [],
                "interpretation": {
                    "summary": "Model self-assessment (testimony, not proof)",
                    "status": "unverified",
                    "epistemic_class": "model_self_assessment",
                },
                "judgment": {
                    "gates_passed": [],
                    "court_admissible": False,
                    "blockers": ["Self-assessment cannot self-verify"],
                },
            },
            "trust_posture": {
                "provenance_integrity": "low",
                "artifact_verifiability": "low",
                "semantic_alignment": "unknown",
                "decision_completeness": "unknown",
                "risk_calibration": "untested",
                "legal_reliance_readiness": "not_ready",
                "operational_utility": "medium",
            },
        }

        # Sign using UATP v7 crypto
        verification = {}
        if self._crypto:
            try:
                verification = self._crypto.sign_capsule(
                    payload, timestamp_mode="local"
                )
            except Exception as e:
                logger.warning(f"Assessment signing failed: {e}")

        self._save_capsule(
            capsule_id=capsule_id,
            timestamp=timestamp,
            capsule_type="model_self_assessment",
            payload=payload,
            verification=verification,
            model=model,
            parent_capsule_id=parent_capsule_id,
        )

    def _save_capsule(
        self,
        capsule_id: str,
        timestamp: datetime,
        capsule_type: str,
        payload: Dict[str, Any],
        verification: Dict[str, Any],
        model: str,
        parent_capsule_id: Optional[str] = None,
    ):
        """Save capsule to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Include model in payload for identification
            payload["_source"] = f"ollama_proxy:{model}"

            cursor.execute(
                """
                INSERT INTO capsules (
                    capsule_id, timestamp, capsule_type, payload, verification,
                    parent_capsule_id, version, status
                ) VALUES (?, ?, ?, ?, ?, ?, '1.0', 'active')
            """,
                (
                    capsule_id,
                    timestamp.isoformat(),
                    capsule_type,
                    json.dumps(payload),
                    json.dumps(verification),
                    parent_capsule_id,
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Database save failed: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get proxy statistics."""
        uptime = time.time() - self.start_time if self.start_time else 0
        return {
            "uptime_seconds": uptime,
            "requests_proxied": self.requests_proxied,
            "capsules_created": self.capsules_created,
            "capture_rate": self.capsules_created / max(1, self.requests_proxied),
        }


async def main():
    parser = argparse.ArgumentParser(
        description="UATP Ollama Proxy - Transparent capture for all Ollama traffic"
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=11435,
        help="Proxy listen port (default: 11435)",
    )
    parser.add_argument(
        "--ollama-url",
        "-u",
        default="http://localhost:11434",
        help="Upstream Ollama URL (default: http://localhost:11434)",
    )
    parser.add_argument(
        "--assess",
        "-a",
        action="store_true",
        help="Auto-trigger self-assessment after each response",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--db-path", default="uatp_dev.db", help="Database path (default: uatp_dev.db)"
    )

    args = parser.parse_args()

    proxy = OllamaProxy(
        proxy_port=args.port,
        ollama_url=args.ollama_url,
        db_path=args.db_path,
        auto_assess=args.assess,
        verbose=args.verbose,
    )

    try:
        await proxy.start()
    except KeyboardInterrupt:
        logger.info("Proxy shutting down...")
        stats = proxy.get_stats()
        logger.info(f"Final stats: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
