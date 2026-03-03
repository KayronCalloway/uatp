"""
Content-Addressed Storage Service - UATP 7.2 Model Registry Protocol

Provides content-addressed storage for model artifacts with:
- SHA-256 content hashing
- Integrity verification
- Multiple storage backend support
- Deduplication
"""

import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, BinaryIO, Dict, Optional, Union

# Try to import aiofiles for async I/O
try:
    import aiofiles
    import aiofiles.os

    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False

logger = logging.getLogger(__name__)

if not AIOFILES_AVAILABLE:
    logger.warning(
        "aiofiles not available - using blocking file I/O. "
        "Install aiofiles for better async performance: pip install aiofiles"
    )


class StorageBackend(str, Enum):
    """Supported storage backends."""

    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"
    AZURE = "azure"
    IPFS = "ipfs"


@dataclass
class StorageLocation:
    """Information about stored artifact location."""

    backend: StorageBackend
    uri: str
    content_hash: str
    size_bytes: int
    stored_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "backend": self.backend.value,
            "uri": self.uri,
            "content_hash": self.content_hash,
            "size_bytes": self.size_bytes,
            "stored_at": self.stored_at.isoformat(),
        }


@dataclass
class RetrievalResult:
    """Result of artifact retrieval."""

    success: bool
    content_hash: str
    data: Optional[bytes]
    size_bytes: int
    verified: bool
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "content_hash": self.content_hash,
            "size_bytes": self.size_bytes,
            "verified": self.verified,
            "error": self.error,
        }


class StorageProvider(ABC):
    """Abstract base class for storage providers."""

    @abstractmethod
    async def store(
        self,
        content_hash: str,
        data: Union[bytes, BinaryIO],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StorageLocation:
        """Store content and return location."""
        pass

    @abstractmethod
    async def retrieve(self, content_hash: str) -> RetrievalResult:
        """Retrieve content by hash."""
        pass

    @abstractmethod
    async def exists(self, content_hash: str) -> bool:
        """Check if content exists."""
        pass

    @abstractmethod
    async def delete(self, content_hash: str) -> bool:
        """Delete content by hash."""
        pass

    @abstractmethod
    async def get_metadata(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Get metadata for content."""
        pass


class LocalStorageProvider(StorageProvider):
    """
    Local filesystem storage provider.

    Stores artifacts in a content-addressed directory structure:
    base_path/
        ab/
            cd/
                abcd1234...  (full hash as filename)
    """

    def __init__(self, base_path: str = "./data/artifacts"):
        """Initialize local storage provider."""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._metadata_suffix = ".meta.json"

    def _get_path(self, content_hash: str) -> Path:
        """Get file path for content hash."""
        # SECURITY: Validate content_hash is a valid hex string to prevent directory traversal
        # Content hashes must be exactly 64 hex characters (SHA-256)
        if not content_hash or len(content_hash) != 64:
            raise ValueError(
                f"Invalid content hash length: expected 64, got {len(content_hash) if content_hash else 0}"
            )
        if not all(c in "0123456789abcdefABCDEF" for c in content_hash):
            raise ValueError("Content hash must contain only hexadecimal characters")

        # Normalize to lowercase for consistent paths
        content_hash = content_hash.lower()

        # Use first 4 chars as directory structure
        result_path = self.base_path / content_hash[:2] / content_hash[2:4] / content_hash

        # SECURITY: Defense-in-depth - verify resolved path is within base_path
        # This catches any edge cases where path construction might escape base_path
        resolved_path = result_path.resolve()
        resolved_base = self.base_path.resolve()
        try:
            resolved_path.relative_to(resolved_base)
        except ValueError:
            raise ValueError(
                f"Security violation: path {resolved_path} escapes base directory"
            )

        return result_path

    async def store(
        self,
        content_hash: str,
        data: Union[bytes, BinaryIO],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StorageLocation:
        """Store content to local filesystem."""
        path = self._get_path(content_hash)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write data
        if isinstance(data, bytes):
            content = data
        else:
            content = data.read()

        # Verify hash matches
        actual_hash = hashlib.sha256(content).hexdigest()
        if actual_hash != content_hash:
            raise ValueError(
                f"Content hash mismatch: expected {content_hash}, got {actual_hash}"
            )

        # Use async file I/O if available
        if AIOFILES_AVAILABLE:
            async with aiofiles.open(path, "wb") as f:
                await f.write(content)
        else:
            path.write_bytes(content)

        size_bytes = len(content)

        # Write metadata if provided
        if metadata:
            import json

            meta_path = Path(str(path) + self._metadata_suffix)
            if AIOFILES_AVAILABLE:
                async with aiofiles.open(meta_path, "w") as f:
                    await f.write(json.dumps(metadata))
            else:
                meta_path.write_text(json.dumps(metadata))

        logger.info(f"Stored artifact {content_hash[:16]}... ({size_bytes} bytes)")

        return StorageLocation(
            backend=StorageBackend.LOCAL,
            uri=str(path.absolute()),
            content_hash=content_hash,
            size_bytes=size_bytes,
            stored_at=datetime.now(timezone.utc),
        )

    async def retrieve(self, content_hash: str) -> RetrievalResult:
        """Retrieve content from local filesystem."""
        path = self._get_path(content_hash)

        if not path.exists():
            return RetrievalResult(
                success=False,
                content_hash=content_hash,
                data=None,
                size_bytes=0,
                verified=False,
                error=f"Content not found: {content_hash}",
            )

        # Use async file I/O if available
        if AIOFILES_AVAILABLE:
            async with aiofiles.open(path, "rb") as f:
                data = await f.read()
        else:
            data = path.read_bytes()

        size_bytes = len(data)

        # Verify integrity
        actual_hash = hashlib.sha256(data).hexdigest()
        verified = actual_hash == content_hash

        if not verified:
            logger.warning(
                f"Content integrity check failed for {content_hash}: got {actual_hash}"
            )

        return RetrievalResult(
            success=True,
            content_hash=content_hash,
            data=data,
            size_bytes=size_bytes,
            verified=verified,
        )

    async def exists(self, content_hash: str) -> bool:
        """Check if content exists."""
        return self._get_path(content_hash).exists()

    async def delete(self, content_hash: str) -> bool:
        """Delete content."""
        path = self._get_path(content_hash)
        meta_path = Path(str(path) + self._metadata_suffix)

        if path.exists():
            # Use async file operations if available
            if AIOFILES_AVAILABLE:
                await aiofiles.os.remove(path)
                if meta_path.exists():
                    await aiofiles.os.remove(meta_path)
            else:
                path.unlink()
                if meta_path.exists():
                    meta_path.unlink()
            logger.info(f"Deleted artifact {content_hash[:16]}...")
            return True
        return False

    async def get_metadata(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Get metadata for content."""
        import json

        meta_path = Path(str(self._get_path(content_hash)) + self._metadata_suffix)
        if meta_path.exists():
            if AIOFILES_AVAILABLE:
                async with aiofiles.open(meta_path, "r") as f:
                    return json.loads(await f.read())
            else:
                return json.loads(meta_path.read_text())
        return None


class ContentAddressedStorage:
    """
    Content-addressed storage service.

    Provides high-level interface for storing and retrieving model
    artifacts with content-addressing and deduplication.
    """

    def __init__(
        self,
        default_backend: StorageBackend = StorageBackend.LOCAL,
        local_base_path: str = "./data/artifacts",
    ):
        """
        Initialize content-addressed storage.

        Args:
            default_backend: Default storage backend
            local_base_path: Base path for local storage
        """
        self.default_backend = default_backend
        self._providers: Dict[StorageBackend, StorageProvider] = {}

        # Initialize local provider by default
        self._providers[StorageBackend.LOCAL] = LocalStorageProvider(local_base_path)

    def get_provider(self, backend: StorageBackend) -> StorageProvider:
        """Get storage provider for backend."""
        if backend not in self._providers:
            raise ValueError(f"Storage backend not configured: {backend}")
        return self._providers[backend]

    @staticmethod
    def compute_hash(data: Union[bytes, BinaryIO]) -> str:
        """Compute SHA-256 hash of data."""
        if isinstance(data, bytes):
            return hashlib.sha256(data).hexdigest()
        else:
            hasher = hashlib.sha256()
            for chunk in iter(lambda: data.read(8192), b""):
                hasher.update(chunk)
            data.seek(0)
            return hasher.hexdigest()

    async def store(
        self,
        data: Union[bytes, BinaryIO],
        metadata: Optional[Dict[str, Any]] = None,
        backend: Optional[StorageBackend] = None,
    ) -> StorageLocation:
        """
        Store content with automatic content-addressing.

        Args:
            data: Content to store
            metadata: Optional metadata
            backend: Storage backend (uses default if None)

        Returns:
            StorageLocation with content hash and URI
        """
        backend = backend or self.default_backend
        provider = self.get_provider(backend)

        # Compute content hash
        content_hash = self.compute_hash(data)

        # Check for deduplication
        if await provider.exists(content_hash):
            logger.info(f"Content {content_hash[:16]}... already exists (deduplicated)")
            # Return existing location
            existing_meta = await provider.get_metadata(content_hash)
            if isinstance(data, bytes):
                size = len(data)
            else:
                data.seek(0, 2)
                size = data.tell()
                data.seek(0)

            return StorageLocation(
                backend=backend,
                uri=str(provider._get_path(content_hash).absolute()),
                content_hash=content_hash,
                size_bytes=size,
                stored_at=datetime.now(timezone.utc),
            )

        # Store new content
        return await provider.store(content_hash, data, metadata)

    async def retrieve(
        self,
        content_hash: str,
        backend: Optional[StorageBackend] = None,
        verify: bool = True,
    ) -> RetrievalResult:
        """
        Retrieve content by hash.

        Args:
            content_hash: SHA-256 hash of content
            backend: Storage backend to use
            verify: Whether to verify content integrity

        Returns:
            RetrievalResult with content
        """
        backend = backend or self.default_backend
        provider = self.get_provider(backend)

        result = await provider.retrieve(content_hash)

        if result.success and verify and not result.verified:
            # Content exists but integrity check failed
            result.success = False
            result.error = "Content integrity verification failed"

        return result

    async def exists(
        self,
        content_hash: str,
        backend: Optional[StorageBackend] = None,
    ) -> bool:
        """Check if content exists."""
        backend = backend or self.default_backend
        provider = self.get_provider(backend)
        return await provider.exists(content_hash)

    async def delete(
        self,
        content_hash: str,
        backend: Optional[StorageBackend] = None,
    ) -> bool:
        """Delete content by hash."""
        backend = backend or self.default_backend
        provider = self.get_provider(backend)
        return await provider.delete(content_hash)

    async def verify(
        self,
        content_hash: str,
        backend: Optional[StorageBackend] = None,
    ) -> bool:
        """
        Verify content integrity.

        Args:
            content_hash: Expected SHA-256 hash
            backend: Storage backend

        Returns:
            True if content exists and matches hash
        """
        result = await self.retrieve(content_hash, backend, verify=True)
        return result.success and result.verified

    async def get_metadata(
        self,
        content_hash: str,
        backend: Optional[StorageBackend] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get metadata for content."""
        backend = backend or self.default_backend
        provider = self.get_provider(backend)
        return await provider.get_metadata(content_hash)


# Singleton instance
content_addressed_storage = ContentAddressedStorage()
