"""
Performance Compression Middleware
=================================

High-performance response compression middleware with:
- gzip and brotli compression support
- Smart compression based on content type and size
- Optimized compression levels for performance vs. size trade-offs
- Cache-aware compression headers
- Performance metrics tracking
"""

import asyncio
import gzip
import logging
import time
from typing import Any, Dict, List, Optional

import brotli
from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveCallable,
    ASGISendCallable,
    Scope,
)

logger = logging.getLogger(__name__)


class CompressionMiddleware:
    """High-performance compression middleware with intelligent compression strategies."""

    def __init__(
        self,
        app: ASGI3Application,
        minimum_size: int = 500,
        gzip_level: int = 6,
        brotli_level: int = 4,
        compressible_types: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
    ):
        self.app = app
        self.minimum_size = minimum_size
        self.gzip_level = gzip_level
        self.brotli_level = brotli_level
        self.exclude_paths = exclude_paths or ["/metrics", "/health/ping"]

        # Default compressible MIME types
        self.compressible_types = compressible_types or [
            "application/json",
            "application/javascript",
            "application/x-javascript",
            "text/css",
            "text/html",
            "text/javascript",
            "text/plain",
            "text/xml",
            "application/xml",
            "application/xhtml+xml",
            "application/rss+xml",
            "application/atom+xml",
            "image/svg+xml",
        ]

        # Performance metrics
        self.compression_stats = {
            "requests_compressed": 0,
            "requests_skipped": 0,
            "bytes_saved": 0,
            "compression_time": 0.0,
            "gzip_requests": 0,
            "brotli_requests": 0,
        }

    async def __call__(
        self, scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        """ASGI middleware entry point."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Check if path should be excluded from compression
        path = scope.get("path", "")
        if any(path.startswith(exclude) for exclude in self.exclude_paths):
            await self.app(scope, receive, send)
            return

        # Get client's accepted encodings
        accept_encoding = ""
        for name, value in scope.get("headers", []):
            if name == b"accept-encoding":
                accept_encoding = value.decode("latin1")
                break

        # Determine best compression method
        compression_method = self._select_compression_method(accept_encoding)

        if not compression_method:
            await self.app(scope, receive, send)
            return

        # Wrap the send function to intercept and compress responses
        send_wrapper = CompressionSendWrapper(
            send,
            compression_method,
            self.minimum_size,
            self.compressible_types,
            self.gzip_level,
            self.brotli_level,
            self.compression_stats,
        )

        await self.app(scope, receive, send_wrapper)

    def _select_compression_method(self, accept_encoding: str) -> Optional[str]:
        """Select the best compression method based on client capabilities."""
        if not accept_encoding:
            return None

        # Parse accepted encodings with quality values
        encodings = {}
        for encoding in accept_encoding.split(","):
            encoding = encoding.strip()
            if ";q=" in encoding:
                name, quality = encoding.split(";q=", 1)
                try:
                    encodings[name.strip()] = float(quality)
                except ValueError:
                    encodings[name.strip()] = 1.0
            else:
                encodings[encoding] = 1.0

        # Prefer brotli for better compression, then gzip
        if "br" in encodings and encodings["br"] > 0:
            return "br"
        elif "gzip" in encodings and encodings["gzip"] > 0:
            return "gzip"

        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics."""
        total_requests = (
            self.compression_stats["requests_compressed"]
            + self.compression_stats["requests_skipped"]
        )
        compression_ratio = 0.0
        avg_compression_time = 0.0

        if self.compression_stats["requests_compressed"] > 0:
            avg_compression_time = (
                self.compression_stats["compression_time"]
                / self.compression_stats["requests_compressed"]
            )

        return {
            "total_requests": total_requests,
            "requests_compressed": self.compression_stats["requests_compressed"],
            "requests_skipped": self.compression_stats["requests_skipped"],
            "compression_rate": self.compression_stats["requests_compressed"]
            / max(total_requests, 1),
            "bytes_saved": self.compression_stats["bytes_saved"],
            "avg_compression_time_ms": round(avg_compression_time * 1000, 2),
            "gzip_requests": self.compression_stats["gzip_requests"],
            "brotli_requests": self.compression_stats["brotli_requests"],
        }


class CompressionSendWrapper:
    """Wrapper for the ASGI send callable to handle response compression."""

    def __init__(
        self,
        send: ASGISendCallable,
        compression_method: str,
        minimum_size: int,
        compressible_types: List[str],
        gzip_level: int,
        brotli_level: int,
        stats: Dict[str, Any],
    ):
        self.send = send
        self.compression_method = compression_method
        self.minimum_size = minimum_size
        self.compressible_types = compressible_types
        self.gzip_level = gzip_level
        self.brotli_level = brotli_level
        self.stats = stats

        self.response_started = False
        self.should_compress = False
        self.content_type = ""
        self.content_length = 0
        self.buffer = bytearray()

    async def __call__(self, message: Dict[str, Any]) -> None:
        """Handle ASGI messages."""
        message_type = message["type"]

        if message_type == "http.response.start":
            await self._handle_response_start(message)
        elif message_type == "http.response.body":
            await self._handle_response_body(message)
        else:
            await self.send(message)

    async def _handle_response_start(self, message: Dict[str, Any]) -> None:
        """Handle response start message."""
        headers = list(message.get("headers", []))

        # Extract content type and length
        for name, value in headers:
            name_str = name.decode("latin1").lower()
            value_str = value.decode("latin1")

            if name_str == "content-type":
                self.content_type = value_str.split(";")[0].strip()
            elif name_str == "content-length":
                try:
                    self.content_length = int(value_str)
                except ValueError:
                    pass

        # Determine if we should compress
        self.should_compress = (
            self._is_compressible_type(self.content_type)
            and self.content_length >= self.minimum_size
            and not self._has_content_encoding(headers)
        )

        if self.should_compress:
            # Remove content-length header as it will change
            headers = [
                (name, value)
                for name, value in headers
                if name.decode("latin1").lower() != "content-length"
            ]

            # Add compression headers
            if self.compression_method == "br":
                headers.append((b"content-encoding", b"br"))
            else:
                headers.append((b"content-encoding", b"gzip"))

            # Add vary header for caching
            headers.append((b"vary", b"Accept-Encoding"))

            message["headers"] = headers

        await self.send(message)
        self.response_started = True

    async def _handle_response_body(self, message: Dict[str, Any]) -> None:
        """Handle response body message."""
        body = message.get("body", b"")
        more_body = message.get("more_body", False)

        if self.should_compress:
            # Buffer the body content
            self.buffer.extend(body)

            if not more_body:
                # Compress the complete body
                start_time = time.time()
                compressed_body = await self._compress_body(bytes(self.buffer))
                compression_time = time.time() - start_time

                # Update statistics
                original_size = len(self.buffer)
                compressed_size = len(compressed_body)
                bytes_saved = original_size - compressed_size

                self.stats["requests_compressed"] += 1
                self.stats["bytes_saved"] += bytes_saved
                self.stats["compression_time"] += compression_time

                if self.compression_method == "br":
                    self.stats["brotli_requests"] += 1
                else:
                    self.stats["gzip_requests"] += 1

                logger.debug(
                    f"Compressed response: {original_size} -> {compressed_size} bytes "
                    f"({bytes_saved} saved, {compression_time*1000:.2f}ms)"
                )

                # Send compressed body
                await self.send(
                    {
                        "type": "http.response.body",
                        "body": compressed_body,
                        "more_body": False,
                    }
                )
            # If more_body is True, keep buffering
        else:
            # Pass through without compression
            if not self.response_started:
                self.stats["requests_skipped"] += 1
            await self.send(message)

    def _is_compressible_type(self, content_type: str) -> bool:
        """Check if content type is compressible."""
        return any(content_type.startswith(ct) for ct in self.compressible_types)

    def _has_content_encoding(self, headers: List[tuple]) -> bool:
        """Check if response already has content encoding."""
        for name, value in headers:
            if name.decode("latin1").lower() == "content-encoding":
                return True
        return False

    async def _compress_body(self, body: bytes) -> bytes:
        """Compress response body."""
        if self.compression_method == "br":
            return await self._compress_brotli(body)
        else:
            return await self._compress_gzip(body)

    async def _compress_gzip(self, body: bytes) -> bytes:
        """Compress body using gzip."""

        def compress():
            return gzip.compress(body, compresslevel=self.gzip_level)

        # Run compression in thread pool for large bodies
        if len(body) > 64 * 1024:  # 64KB threshold
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, compress)
        else:
            return compress()

    async def _compress_brotli(self, body: bytes) -> bytes:
        """Compress body using brotli."""

        def compress():
            return brotli.compress(body, quality=self.brotli_level)

        # Run compression in thread pool for large bodies
        if len(body) > 64 * 1024:  # 64KB threshold
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, compress)
        else:
            return compress()


def create_compression_middleware(
    app: ASGI3Application,
    minimum_size: int = 500,
    gzip_level: int = 6,
    brotli_level: int = 4,
    compressible_types: Optional[List[str]] = None,
    exclude_paths: Optional[List[str]] = None,
) -> CompressionMiddleware:
    """Factory function to create compression middleware."""
    return CompressionMiddleware(
        app=app,
        minimum_size=minimum_size,
        gzip_level=gzip_level,
        brotli_level=brotli_level,
        compressible_types=compressible_types,
        exclude_paths=exclude_paths,
    )
