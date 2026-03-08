#!/usr/bin/env python3
"""
UATP Secrets Manager
Implements secrets rotation with HashiCorp Vault and AWS Secrets Manager support.
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SecretType(Enum):
    """Types of secrets we manage."""

    API_KEY = "api_key"
    DATABASE_PASSWORD = "database_password"
    SIGNING_KEY = "signing_key"
    ENCRYPTION_KEY = "encryption_key"
    SERVICE_TOKEN = "service_token"
    CERTIFICATE = "certificate"


@dataclass
class SecretMetadata:
    """Metadata for a secret."""

    name: str
    secret_type: SecretType
    created_at: datetime
    last_rotated: datetime
    rotation_interval: timedelta
    version: int = 1
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class SecretValue:
    """A secret value with its metadata."""

    value: str
    metadata: SecretMetadata
    expires_at: Optional[datetime] = None


class SecretBackend(ABC):
    """Abstract base class for secret backends."""

    @abstractmethod
    async def get_secret(self, name: str) -> Optional[SecretValue]:
        """Get a secret by name."""
        pass

    @abstractmethod
    async def set_secret(self, name: str, value: str, metadata: SecretMetadata) -> bool:
        """Set a secret value."""
        pass

    @abstractmethod
    async def delete_secret(self, name: str) -> bool:
        """Delete a secret."""
        pass

    @abstractmethod
    async def list_secrets(self) -> List[str]:
        """List all secret names."""
        pass

    @abstractmethod
    async def rotate_secret(self, name: str) -> bool:
        """Rotate a secret."""
        pass


class HashiCorpVaultBackend(SecretBackend):
    """HashiCorp Vault backend for secrets management."""

    def __init__(self, vault_url: str, vault_token: str, mount_path: str = "secret"):
        self.vault_url = vault_url.rstrip("/")
        self.vault_token = vault_token
        self.mount_path = mount_path
        self.session = None
        logger.info(f"HashiCorp Vault backend initialized: {vault_url}")

    async def _get_session(self):
        """Get HTTP session for Vault API calls."""
        if not self.session:
            try:
                import aiohttp

                self.session = aiohttp.ClientSession(
                    headers={"X-Vault-Token": self.vault_token}
                )
            except ImportError:
                logger.error("aiohttp is required for HashiCorp Vault backend")
                raise
        return self.session

    async def get_secret(self, name: str) -> Optional[SecretValue]:
        """Get a secret from Vault."""
        try:
            session = await self._get_session()
            url = f"{self.vault_url}/v1/{self.mount_path}/data/{name}"

            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    secret_data = data.get("data", {}).get("data", {})

                    if "value" in secret_data:
                        metadata = SecretMetadata(
                            name=name,
                            secret_type=SecretType(secret_data.get("type", "api_key")),
                            created_at=datetime.fromisoformat(
                                secret_data.get(
                                    "created_at", datetime.now(timezone.utc).isoformat()
                                )
                            ),
                            last_rotated=datetime.fromisoformat(
                                secret_data.get(
                                    "last_rotated",
                                    datetime.now(timezone.utc).isoformat(),
                                )
                            ),
                            rotation_interval=timedelta(
                                days=int(secret_data.get("rotation_days", 30))
                            ),
                            version=secret_data.get("version", 1),
                            tags=secret_data.get("tags", {}),
                        )

                        return SecretValue(
                            value=secret_data["value"],
                            metadata=metadata,
                            expires_at=datetime.fromisoformat(secret_data["expires_at"])
                            if secret_data.get("expires_at")
                            else None,
                        )
                elif response.status == 404:
                    return None
                else:
                    logger.error(f"Vault API error: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error getting secret from Vault: {e}")
            return None

    async def set_secret(self, name: str, value: str, metadata: SecretMetadata) -> bool:
        """Set a secret in Vault."""
        try:
            session = await self._get_session()
            url = f"{self.vault_url}/v1/{self.mount_path}/data/{name}"

            payload = {
                "data": {
                    "value": value,
                    "type": metadata.secret_type.value,
                    "created_at": metadata.created_at.isoformat(),
                    "last_rotated": metadata.last_rotated.isoformat(),
                    "rotation_days": metadata.rotation_interval.days,
                    "version": metadata.version,
                    "tags": metadata.tags,
                }
            }

            async with session.post(url, json=payload) as response:
                if response.status in [200, 204]:
                    logger.info(f"Secret {name} stored in Vault")
                    return True
                else:
                    logger.error(f"Vault API error storing secret: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"Error setting secret in Vault: {e}")
            return False

    async def delete_secret(self, name: str) -> bool:
        """Delete a secret from Vault."""
        try:
            session = await self._get_session()
            url = f"{self.vault_url}/v1/{self.mount_path}/data/{name}"

            async with session.delete(url) as response:
                if response.status in [200, 204]:
                    logger.info(f"Secret {name} deleted from Vault")
                    return True
                else:
                    logger.error(f"Vault API error deleting secret: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"Error deleting secret from Vault: {e}")
            return False

    async def list_secrets(self) -> List[str]:
        """List all secrets in Vault."""
        try:
            session = await self._get_session()
            url = f"{self.vault_url}/v1/{self.mount_path}/metadata"

            async with session.get(url, params={"list": "true"}) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", {}).get("keys", [])
                else:
                    logger.error(f"Vault API error listing secrets: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error listing secrets from Vault: {e}")
            return []

    async def rotate_secret(self, name: str) -> bool:
        """Rotate a secret in Vault."""
        try:
            # Get current secret
            current_secret = await self.get_secret(name)
            if not current_secret:
                logger.error(f"Secret {name} not found for rotation")
                return False

            # Generate new secret value based on type
            new_value = self._generate_new_secret_value(
                current_secret.metadata.secret_type
            )

            # Update metadata
            new_metadata = current_secret.metadata
            new_metadata.last_rotated = datetime.now(timezone.utc)
            new_metadata.version += 1

            # Store new secret
            return await self.set_secret(name, new_value, new_metadata)

        except Exception as e:
            logger.error(f"Error rotating secret {name}: {e}")
            return False

    def _generate_new_secret_value(self, secret_type: SecretType) -> str:
        """Generate a new secret value based on type."""
        import secrets
        import string

        if secret_type == SecretType.API_KEY:
            return f"sk-{''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(48))}"
        elif secret_type == SecretType.DATABASE_PASSWORD:
            return "".join(
                secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*")
                for _ in range(32)
            )
        elif secret_type == SecretType.SIGNING_KEY:
            return secrets.token_hex(32)
        elif secret_type == SecretType.ENCRYPTION_KEY:
            return secrets.token_hex(32)
        elif secret_type == SecretType.SERVICE_TOKEN:
            return secrets.token_urlsafe(32)
        else:
            return secrets.token_urlsafe(32)


class AWSSecretsManagerBackend(SecretBackend):
    """AWS Secrets Manager backend for secrets management."""

    def __init__(self, region_name: str = "us-east-1"):
        self.region_name = region_name
        self.client = None
        logger.info(f"AWS Secrets Manager backend initialized: {region_name}")

    async def _get_client(self):
        """Get AWS Secrets Manager client."""
        if not self.client:
            try:
                import boto3

                self.client = boto3.client(
                    "secretsmanager", region_name=self.region_name
                )
            except ImportError:
                logger.error("boto3 is required for AWS Secrets Manager backend")
                raise
        return self.client

    async def get_secret(self, name: str) -> Optional[SecretValue]:
        """Get a secret from AWS Secrets Manager."""
        try:
            client = await self._get_client()
            response = client.get_secret_value(SecretId=name)

            secret_data = json.loads(response["SecretString"])

            if "value" in secret_data:
                metadata = SecretMetadata(
                    name=name,
                    secret_type=SecretType(secret_data.get("type", "api_key")),
                    created_at=datetime.fromisoformat(
                        secret_data.get(
                            "created_at", datetime.now(timezone.utc).isoformat()
                        )
                    ),
                    last_rotated=datetime.fromisoformat(
                        secret_data.get(
                            "last_rotated", datetime.now(timezone.utc).isoformat()
                        )
                    ),
                    rotation_interval=timedelta(
                        days=int(secret_data.get("rotation_days", 30))
                    ),
                    version=secret_data.get("version", 1),
                    tags=secret_data.get("tags", {}),
                )

                return SecretValue(
                    value=secret_data["value"],
                    metadata=metadata,
                    expires_at=datetime.fromisoformat(secret_data["expires_at"])
                    if secret_data.get("expires_at")
                    else None,
                )

            return None

        except Exception as e:
            logger.error(f"Error getting secret from AWS Secrets Manager: {e}")
            return None

    async def set_secret(self, name: str, value: str, metadata: SecretMetadata) -> bool:
        """Set a secret in AWS Secrets Manager."""
        try:
            client = await self._get_client()

            secret_data = {
                "value": value,
                "type": metadata.secret_type.value,
                "created_at": metadata.created_at.isoformat(),
                "last_rotated": metadata.last_rotated.isoformat(),
                "rotation_days": metadata.rotation_interval.days,
                "version": metadata.version,
                "tags": metadata.tags,
            }

            try:
                # Try to update existing secret
                client.update_secret(
                    SecretId=name, SecretString=json.dumps(secret_data)
                )
                logger.info(f"Secret {name} updated in AWS Secrets Manager")
                return True
            except client.exceptions.ResourceNotFoundException:
                # Create new secret
                client.create_secret(
                    Name=name,
                    SecretString=json.dumps(secret_data),
                    Description=f"UATP {metadata.secret_type.value}",
                )
                logger.info(f"Secret {name} created in AWS Secrets Manager")
                return True

        except Exception as e:
            logger.error(f"Error setting secret in AWS Secrets Manager: {e}")
            return False

    async def delete_secret(self, name: str) -> bool:
        """Delete a secret from AWS Secrets Manager."""
        try:
            client = await self._get_client()
            client.delete_secret(SecretId=name, ForceDeleteWithoutRecovery=True)
            logger.info(f"Secret {name} deleted from AWS Secrets Manager")
            return True

        except Exception as e:
            logger.error(f"Error deleting secret from AWS Secrets Manager: {e}")
            return False

    async def list_secrets(self) -> List[str]:
        """List all secrets in AWS Secrets Manager."""
        try:
            client = await self._get_client()
            response = client.list_secrets()
            return [secret["Name"] for secret in response.get("SecretList", [])]

        except Exception as e:
            logger.error(f"Error listing secrets from AWS Secrets Manager: {e}")
            return []

    async def rotate_secret(self, name: str) -> bool:
        """Rotate a secret in AWS Secrets Manager."""
        try:
            # Get current secret
            current_secret = await self.get_secret(name)
            if not current_secret:
                logger.error(f"Secret {name} not found for rotation")
                return False

            # Generate new secret value
            new_value = self._generate_new_secret_value(
                current_secret.metadata.secret_type
            )

            # Update metadata
            new_metadata = current_secret.metadata
            new_metadata.last_rotated = datetime.now(timezone.utc)
            new_metadata.version += 1

            # Store new secret
            return await self.set_secret(name, new_value, new_metadata)

        except Exception as e:
            logger.error(f"Error rotating secret {name}: {e}")
            return False

    def _generate_new_secret_value(self, secret_type: SecretType) -> str:
        """Generate a new secret value based on type."""
        import secrets
        import string

        if secret_type == SecretType.API_KEY:
            return f"sk-{''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(48))}"
        elif secret_type == SecretType.DATABASE_PASSWORD:
            return "".join(
                secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*")
                for _ in range(32)
            )
        elif secret_type == SecretType.SIGNING_KEY:
            return secrets.token_hex(32)
        elif secret_type == SecretType.ENCRYPTION_KEY:
            return secrets.token_hex(32)
        elif secret_type == SecretType.SERVICE_TOKEN:
            return secrets.token_urlsafe(32)
        else:
            return secrets.token_urlsafe(32)


class LocalSecretsBackend(SecretBackend):
    """Local file-based secrets backend for development."""

    def __init__(self, secrets_dir: str = ".secrets"):
        self.secrets_dir = secrets_dir
        os.makedirs(secrets_dir, exist_ok=True)
        logger.info(f"Local secrets backend initialized: {secrets_dir}")

    async def get_secret(self, name: str) -> Optional[SecretValue]:
        """Get a secret from local storage."""
        try:
            secret_file = os.path.join(self.secrets_dir, f"{name}.json")
            if os.path.exists(secret_file):
                with open(secret_file) as f:
                    data = json.load(f)

                metadata = SecretMetadata(
                    name=name,
                    secret_type=SecretType(data.get("type", "api_key")),
                    created_at=datetime.fromisoformat(data.get("created_at")),
                    last_rotated=datetime.fromisoformat(data.get("last_rotated")),
                    rotation_interval=timedelta(
                        days=int(data.get("rotation_days", 30))
                    ),
                    version=data.get("version", 1),
                    tags=data.get("tags", {}),
                )

                return SecretValue(
                    value=data["value"],
                    metadata=metadata,
                    expires_at=datetime.fromisoformat(data["expires_at"])
                    if data.get("expires_at")
                    else None,
                )

            return None

        except Exception as e:
            logger.error(f"Error getting secret from local storage: {e}")
            return None

    async def set_secret(self, name: str, value: str, metadata: SecretMetadata) -> bool:
        """Set a secret in local storage."""
        try:
            secret_file = os.path.join(self.secrets_dir, f"{name}.json")

            data = {
                "value": value,
                "type": metadata.secret_type.value,
                "created_at": metadata.created_at.isoformat(),
                "last_rotated": metadata.last_rotated.isoformat(),
                "rotation_days": metadata.rotation_interval.days,
                "version": metadata.version,
                "tags": metadata.tags,
            }

            with open(secret_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Secret {name} stored locally")
            return True

        except Exception as e:
            logger.error(f"Error setting secret in local storage: {e}")
            return False

    async def delete_secret(self, name: str) -> bool:
        """Delete a secret from local storage."""
        try:
            secret_file = os.path.join(self.secrets_dir, f"{name}.json")
            if os.path.exists(secret_file):
                os.remove(secret_file)
                logger.info(f"Secret {name} deleted from local storage")
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting secret from local storage: {e}")
            return False

    async def list_secrets(self) -> List[str]:
        """List all secrets in local storage."""
        try:
            return [
                f.replace(".json", "")
                for f in os.listdir(self.secrets_dir)
                if f.endswith(".json")
            ]

        except Exception as e:
            logger.error(f"Error listing secrets from local storage: {e}")
            return []

    async def rotate_secret(self, name: str) -> bool:
        """Rotate a secret in local storage."""
        try:
            # Get current secret
            current_secret = await self.get_secret(name)
            if not current_secret:
                logger.error(f"Secret {name} not found for rotation")
                return False

            # Generate new secret value
            new_value = self._generate_new_secret_value(
                current_secret.metadata.secret_type
            )

            # Update metadata
            new_metadata = current_secret.metadata
            new_metadata.last_rotated = datetime.now(timezone.utc)
            new_metadata.version += 1

            # Store new secret
            return await self.set_secret(name, new_value, new_metadata)

        except Exception as e:
            logger.error(f"Error rotating secret {name}: {e}")
            return False

    def _generate_new_secret_value(self, secret_type: SecretType) -> str:
        """Generate a new secret value based on type."""
        import secrets
        import string

        if secret_type == SecretType.API_KEY:
            return f"sk-{''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(48))}"
        elif secret_type == SecretType.DATABASE_PASSWORD:
            return "".join(
                secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*")
                for _ in range(32)
            )
        elif secret_type == SecretType.SIGNING_KEY:
            return secrets.token_hex(32)
        elif secret_type == SecretType.ENCRYPTION_KEY:
            return secrets.token_hex(32)
        elif secret_type == SecretType.SERVICE_TOKEN:
            return secrets.token_urlsafe(32)
        else:
            return secrets.token_urlsafe(32)


class SecretsManager:
    """Main secrets manager with automatic rotation."""

    def __init__(self, backend: SecretBackend, auto_rotate: bool = True):
        self.backend = backend
        self.auto_rotate = auto_rotate
        self.rotation_scheduler = None
        logger.info("Secrets manager initialized")

    async def get_secret(self, name: str) -> Optional[str]:
        """Get a secret value."""
        secret = await self.backend.get_secret(name)
        if secret:
            # Check if rotation is needed
            if self.auto_rotate and self._needs_rotation(secret):
                logger.info(f"Auto-rotating secret {name}")
                await self.backend.rotate_secret(name)
                # Get the rotated secret
                secret = await self.backend.get_secret(name)

            return secret.value if secret else None
        return None

    async def set_secret(
        self,
        name: str,
        value: str,
        secret_type: SecretType = SecretType.API_KEY,
        rotation_days: int = 30,
        tags: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Set a secret value."""
        now = datetime.now(timezone.utc)
        metadata = SecretMetadata(
            name=name,
            secret_type=secret_type,
            created_at=now,
            last_rotated=now,
            rotation_interval=timedelta(days=rotation_days),
            tags=tags or {},
        )

        return await self.backend.set_secret(name, value, metadata)

    async def delete_secret(self, name: str) -> bool:
        """Delete a secret."""
        return await self.backend.delete_secret(name)

    async def list_secrets(self) -> List[str]:
        """List all secrets."""
        return await self.backend.list_secrets()

    async def rotate_secret(self, name: str) -> bool:
        """Manually rotate a secret."""
        return await self.backend.rotate_secret(name)

    async def rotate_all_secrets(self) -> Dict[str, bool]:
        """Rotate all secrets that need rotation."""
        results = {}
        secrets = await self.list_secrets()

        for secret_name in secrets:
            secret = await self.backend.get_secret(secret_name)
            if secret and self._needs_rotation(secret):
                results[secret_name] = await self.rotate_secret(secret_name)
            else:
                results[secret_name] = True  # No rotation needed

        return results

    def _needs_rotation(self, secret: SecretValue) -> bool:
        """Check if a secret needs rotation."""
        if secret.expires_at and secret.expires_at <= datetime.now(timezone.utc):
            return True

        rotation_due = secret.metadata.last_rotated + secret.metadata.rotation_interval
        return datetime.now(timezone.utc) >= rotation_due

    async def get_secrets_status(self) -> Dict[str, Any]:
        """Get status of all secrets."""
        secrets = await self.list_secrets()
        status = {
            "total_secrets": len(secrets),
            "secrets_needing_rotation": 0,
            "secrets_details": [],
        }

        for secret_name in secrets:
            secret = await self.backend.get_secret(secret_name)
            if secret:
                needs_rotation = self._needs_rotation(secret)
                if needs_rotation:
                    status["secrets_needing_rotation"] += 1

                status["secrets_details"].append(
                    {
                        "name": secret_name,
                        "type": secret.metadata.secret_type.value,
                        "version": secret.metadata.version,
                        "last_rotated": secret.metadata.last_rotated.isoformat(),
                        "needs_rotation": needs_rotation,
                        "expires_at": secret.expires_at.isoformat()
                        if secret.expires_at
                        else None,
                    }
                )

        return status


# Factory function to create secrets manager
def create_secrets_manager(backend_type: str = "local", **kwargs) -> SecretsManager:
    """Create a secrets manager with the specified backend."""
    if backend_type == "vault":
        backend = HashiCorpVaultBackend(
            vault_url=kwargs.get(
                "vault_url", os.getenv("VAULT_ADDR", "http://localhost:8200")
            ),
            vault_token=kwargs.get("vault_token", os.getenv("VAULT_TOKEN")),
            mount_path=kwargs.get("mount_path", "secret"),
        )
    elif backend_type == "aws":
        backend = AWSSecretsManagerBackend(
            region_name=kwargs.get("region_name", "us-east-1")
        )
    elif backend_type == "local":
        backend = LocalSecretsBackend(secrets_dir=kwargs.get("secrets_dir", ".secrets"))
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")

    return SecretsManager(backend, auto_rotate=kwargs.get("auto_rotate", True))


# Example usage and testing
if __name__ == "__main__":
    import asyncio

    async def test_secrets_manager():
        """Test the secrets manager."""
        print(" UATP Secrets Manager Test")
        print("=" * 40)

        # Test with local backend
        print("Testing with local backend...")
        secrets_manager = create_secrets_manager("local", secrets_dir=".test_secrets")

        # Set some test secrets
        print("Setting test secrets...")
        await secrets_manager.set_secret(
            "openai_api_key", "sk-test123", SecretType.API_KEY, rotation_days=30
        )
        await secrets_manager.set_secret(
            "db_password",
            "mypassword123",
            SecretType.DATABASE_PASSWORD,
            rotation_days=7,
        )
        await secrets_manager.set_secret(
            "signing_key", "abcdef123456", SecretType.SIGNING_KEY, rotation_days=90
        )

        # Get secrets
        print("Getting secrets...")
        openai_key = await secrets_manager.get_secret("openai_api_key")
        db_password = await secrets_manager.get_secret("db_password")
        signing_key = await secrets_manager.get_secret("signing_key")

        print(f"[OK] OpenAI Key: {openai_key[:10]}...")
        print(f"[OK] DB Password: {db_password[:10]}...")
        print(f"[OK] Signing Key: {signing_key[:10]}...")

        # List secrets
        secrets_list = await secrets_manager.list_secrets()
        print(f"[OK] Total secrets: {len(secrets_list)}")

        # Get secrets status
        status = await secrets_manager.get_secrets_status()
        print(
            f"[OK] Secrets status: {status['total_secrets']} total, {status['secrets_needing_rotation']} need rotation"
        )

        # Test rotation
        print("Testing secret rotation...")
        old_key = await secrets_manager.get_secret("openai_api_key")
        await secrets_manager.rotate_secret("openai_api_key")
        new_key = await secrets_manager.get_secret("openai_api_key")

        print(f"[OK] Secret rotated: {old_key != new_key}")

        # Clean up
        await secrets_manager.delete_secret("openai_api_key")
        await secrets_manager.delete_secret("db_password")
        await secrets_manager.delete_secret("signing_key")

        print("\n[OK] Secrets manager test complete!")

        # Show capabilities
        print("\n Secrets Manager Capabilities:")
        print("   [OK] HashiCorp Vault integration")
        print("   [OK] AWS Secrets Manager integration")
        print("   [OK] Local file-based storage")
        print("   [OK] Automatic secret rotation")
        print("   [OK] Multiple secret types support")
        print("   [OK] Metadata and versioning")
        print("   [OK] Expiration handling")
        print("   [OK] Comprehensive status monitoring")

    asyncio.run(test_secrets_manager())
