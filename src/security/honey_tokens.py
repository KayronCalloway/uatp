"""
Honey Tokens & Canary Traps for Intrusion Detection

Implements deception-based security through:
1. Fake API keys that trigger alerts when used
2. Canary database records that detect unauthorized access
3. Honeypot endpoints that log intrusion attempts
4. Fake sensitive data that reveals data exfiltration

Key Concepts:
- Honey tokens: Fake credentials scattered throughout the system
- Canary traps: Fake data records that should never be accessed legitimately
- Honeypots: Fake endpoints that look valuable but are actually traps
- When any honey token/canary is accessed → Instant security alert

Usage:
    from src.security.honey_tokens import HoneyTokenManager

    manager = HoneyTokenManager()

    # Generate fake API key
    honey_key = manager.generate_honey_api_key(owner="security_team")

    # Check if API key is honey token
    if manager.is_honey_token(api_key):
        # INTRUSION DETECTED!
        manager.trigger_honey_token_alert(api_key, request_context)
"""

import hashlib
import json
import logging
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class HoneyToken:
    """A honey token (fake credential) for intrusion detection"""

    token_id: str
    token_type: str  # 'api_key', 'database_record', 'file_path', etc.
    token_value: str  # The actual fake credential
    token_hash: str  # Hash for quick lookup
    created_at: str  # ISO 8601
    owner: str  # Who planted this honey token
    description: str  # What this honey token represents
    metadata: Dict[str, Any]  # Additional context


@dataclass
class HoneyTokenAlert:
    """Alert triggered when honey token is accessed"""

    alert_id: str
    token_id: str
    token_type: str
    accessed_at: str  # ISO 8601
    accessor_ip: Optional[str]
    accessor_user_agent: Optional[str]
    accessor_user_id: Optional[str]
    request_path: Optional[str]
    request_method: Optional[str]
    alert_severity: str  # 'critical', 'high', 'medium'
    metadata: Dict[str, Any]


class HoneyTokenManager:
    """
    Manages honey tokens and canary traps for intrusion detection.

    Honey tokens are fake credentials scattered throughout the system.
    When accessed, they trigger instant security alerts.

    Types of honey tokens:
    1. Fake API keys
    2. Canary database records
    3. Fake file paths
    4. Fake configuration values
    5. Fake sensitive data fields
    """

    def __init__(self, storage_path: str = "security/honey_tokens"):
        """
        Initialize honey token manager.

        Args:
            storage_path: Directory to store honey token registry
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Registry of all honey tokens
        self.tokens: Dict[str, HoneyToken] = {}

        # Quick lookup by hash
        self.token_hashes: Dict[str, str] = {}  # hash -> token_id

        # Load existing honey tokens
        self._load_tokens()

    def _load_tokens(self):
        """Load existing honey tokens from storage"""
        registry_file = self.storage_path / "honey_token_registry.jsonl"

        if not registry_file.exists():
            return

        with open(registry_file) as f:
            for line in f:
                token_dict = json.loads(line)
                token = HoneyToken(**token_dict)
                self.tokens[token.token_id] = token
                self.token_hashes[token.token_hash] = token.token_id

    def _save_token(self, token: HoneyToken):
        """Save honey token to registry"""
        registry_file = self.storage_path / "honey_token_registry.jsonl"

        with open(registry_file, "a") as f:
            f.write(json.dumps(asdict(token)) + "\n")

    def _hash_token(self, token_value: str) -> str:
        """Hash token value for quick lookup"""
        return hashlib.sha256(token_value.encode("utf-8")).hexdigest()

    def generate_honey_api_key(
        self,
        owner: str = "security_team",
        description: str = "Fake API key for intrusion detection",
    ) -> str:
        """
        Generate a fake API key (honey token).

        This looks like a real API key but triggers an alert when used.

        Args:
            owner: Who planted this honey token
            description: What this represents

        Returns:
            Fake API key string
        """
        # Generate realistic-looking API key
        # Format: "sk_honey_" + random hex (looks like real key)
        random_part = secrets.token_hex(32)
        fake_api_key = f"sk_honey_{random_part}"

        token_id = f"honey_api_{secrets.token_hex(8)}"
        token_hash = self._hash_token(fake_api_key)

        honey_token = HoneyToken(
            token_id=token_id,
            token_type="api_key",
            token_value=fake_api_key,
            token_hash=token_hash,
            created_at=datetime.now(timezone.utc).isoformat(),
            owner=owner,
            description=description,
            metadata={"alert_severity": "critical"},
        )

        # Store honey token
        self.tokens[token_id] = honey_token
        self.token_hashes[token_hash] = token_id
        self._save_token(honey_token)

        logger.info(f"Generated honey API key: {token_id}")

        return fake_api_key

    def generate_canary_database_record(
        self, table_name: str, record_data: Dict[str, Any], owner: str = "security_team"
    ) -> str:
        """
        Generate a canary database record (fake data).

        This is a fake record that should never be accessed legitimately.
        If accessed, it indicates unauthorized database access.

        Args:
            table_name: Database table name
            record_data: Fake record data
            owner: Who planted this canary

        Returns:
            Canary record ID
        """
        # Create unique identifier for this canary
        canary_id = f"canary_{table_name}_{secrets.token_hex(8)}"

        # Hash the record data for detection
        record_json = json.dumps(record_data, sort_keys=True)
        record_hash = self._hash_token(record_json)

        honey_token = HoneyToken(
            token_id=canary_id,
            token_type="database_canary",
            token_value=canary_id,
            token_hash=record_hash,
            created_at=datetime.now(timezone.utc).isoformat(),
            owner=owner,
            description=f"Canary record in {table_name} table",
            metadata={
                "table_name": table_name,
                "record_data": record_data,
                "alert_severity": "high",
            },
        )

        self.tokens[canary_id] = honey_token
        self.token_hashes[record_hash] = canary_id
        self._save_token(honey_token)

        logger.info(f"Generated canary database record: {canary_id} in {table_name}")

        return canary_id

    def generate_honey_file_path(
        self, file_path: str, owner: str = "security_team"
    ) -> str:
        """
        Generate a honey file path (fake sensitive file).

        This is a fake file path that looks valuable (e.g., "credentials.json").
        If accessed, it indicates file system intrusion.

        Args:
            file_path: Fake file path
            owner: Who planted this honey token

        Returns:
            Honey token ID
        """
        token_id = f"honey_file_{secrets.token_hex(8)}"
        token_hash = self._hash_token(file_path)

        honey_token = HoneyToken(
            token_id=token_id,
            token_type="file_path",
            token_value=file_path,
            token_hash=token_hash,
            created_at=datetime.now(timezone.utc).isoformat(),
            owner=owner,
            description=f"Fake sensitive file: {file_path}",
            metadata={"file_path": file_path, "alert_severity": "critical"},
        )

        self.tokens[token_id] = honey_token
        self.token_hashes[token_hash] = token_id
        self._save_token(honey_token)

        logger.info(f"Generated honey file path: {file_path}")

        return token_id

    def is_honey_token(self, token_value: str) -> bool:
        """
        Check if a token is a honey token.

        Args:
            token_value: Token to check (API key, file path, etc.)

        Returns:
            True if honey token, False otherwise
        """
        token_hash = self._hash_token(token_value)
        return token_hash in self.token_hashes

    def get_honey_token(self, token_value: str) -> Optional[HoneyToken]:
        """
        Get honey token details by value.

        Args:
            token_value: Token value to look up

        Returns:
            HoneyToken if found, None otherwise
        """
        token_hash = self._hash_token(token_value)
        token_id = self.token_hashes.get(token_hash)

        if token_id:
            return self.tokens.get(token_id)

        return None

    def trigger_honey_token_alert(
        self, token_value: str, request_context: Optional[Dict[str, Any]] = None
    ) -> HoneyTokenAlert:
        """
        Trigger alert when honey token is accessed.

        This is called when a honey token is detected in use.
        It logs the incident and can trigger various alerting mechanisms.

        Args:
            token_value: The honey token that was accessed
            request_context: Context about the request (IP, user agent, etc.)

        Returns:
            HoneyTokenAlert object
        """
        request_context = request_context or {}

        # Get honey token details
        honey_token = self.get_honey_token(token_value)

        if not honey_token:
            logger.error(f"Honey token not found: {token_value[:20]}...")
            raise ValueError("Honey token not in registry")

        # Create alert
        alert_id = f"alert_{secrets.token_hex(16)}"

        alert = HoneyTokenAlert(
            alert_id=alert_id,
            token_id=honey_token.token_id,
            token_type=honey_token.token_type,
            accessed_at=datetime.now(timezone.utc).isoformat(),
            accessor_ip=request_context.get("ip_address"),
            accessor_user_agent=request_context.get("user_agent"),
            accessor_user_id=request_context.get("user_id"),
            request_path=request_context.get("request_path"),
            request_method=request_context.get("request_method"),
            alert_severity=honey_token.metadata.get("alert_severity", "high"),
            metadata={
                "honey_token_description": honey_token.description,
                "honey_token_owner": honey_token.owner,
                **request_context,
            },
        )

        # Log alert
        self._save_alert(alert)

        # Emit critical security alert
        logger.critical(
            f" INTRUSION DETECTED  "
            f"Honey token accessed: {honey_token.token_type} "
            f"from IP: {alert.accessor_ip} "
            f"by user: {alert.accessor_user_id}"
        )

        # Integrate with audit system
        try:
            from src.audit.events import audit_emitter

            audit_emitter.emit_security_event(
                event_name="honey_token_triggered",
                metadata={
                    "alert_id": alert.alert_id,
                    "token_id": honey_token.token_id,
                    "token_type": honey_token.token_type,
                    "severity": alert.alert_severity,
                    "ip_address": alert.accessor_ip,
                    "user_id": alert.accessor_user_id,
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit audit event for honey token alert: {e}")

        return alert

    def _save_alert(self, alert: HoneyTokenAlert):
        """Save honey token alert to storage"""
        alerts_file = self.storage_path / "honey_token_alerts.jsonl"

        with open(alerts_file, "a") as f:
            f.write(json.dumps(asdict(alert)) + "\n")

    def get_recent_alerts(self, count: int = 100) -> List[HoneyTokenAlert]:
        """Get recent honey token alerts"""
        alerts_file = self.storage_path / "honey_token_alerts.jsonl"

        if not alerts_file.exists():
            return []

        with open(alerts_file) as f:
            lines = f.readlines()

        recent_lines = lines[-count:]
        alerts = [HoneyTokenAlert(**json.loads(line)) for line in recent_lines]

        return alerts

    def list_honey_tokens(self, token_type: Optional[str] = None) -> List[HoneyToken]:
        """
        List all honey tokens.

        Args:
            token_type: Filter by type (optional)

        Returns:
            List of honey tokens
        """
        tokens = list(self.tokens.values())

        if token_type:
            tokens = [t for t in tokens if t.token_type == token_type]

        return tokens


class HoneypotEndpoints:
    """
    Collection of honeypot endpoints to detect intrusions.

    These are fake API endpoints that look valuable but are actually traps.
    Any access to these endpoints triggers a security alert.
    """

    @staticmethod
    def create_honeypot_routes():
        """
        Create honeypot routes to add to your API.

        Returns list of (path, handler) tuples.
        """
        from quart import jsonify, request

        honey_manager = HoneyTokenManager()

        async def honeypot_admin_endpoint():
            """Fake admin endpoint"""
            request_context = {
                "ip_address": request.remote_addr,
                "user_agent": request.headers.get("User-Agent"),
                "request_path": request.path,
                "request_method": request.method,
            }

            honey_manager.trigger_honey_token_alert(
                token_value=f"honeypot_admin_{request.path}",
                request_context=request_context,
            )

            # Return fake error to not reveal it's a honeypot
            return jsonify({"error": "Unauthorized"}), 401

        async def honeypot_credentials_endpoint():
            """Fake credentials endpoint"""
            request_context = {
                "ip_address": request.remote_addr,
                "user_agent": request.headers.get("User-Agent"),
                "request_path": request.path,
                "request_method": request.method,
            }

            honey_manager.trigger_honey_token_alert(
                token_value=f"honeypot_credentials_{request.path}",
                request_context=request_context,
            )

            return jsonify({"error": "Not found"}), 404

        # Return honeypot routes
        return [
            ("/api/v1/admin/users", honeypot_admin_endpoint),
            ("/api/v1/admin/keys", honeypot_admin_endpoint),
            ("/api/v1/credentials", honeypot_credentials_endpoint),
            ("/api/v1/secrets", honeypot_credentials_endpoint),
            ("/.env", honeypot_credentials_endpoint),
            ("/config.json", honeypot_credentials_endpoint),
        ]


# Global honey token manager
honey_token_manager = HoneyTokenManager()
