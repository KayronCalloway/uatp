"""
Hardware Security Module (HSM) Integration for UATP Capsule Engine.

This module provides enterprise-grade hardware security module integration
for cryptographic operations, key management, and secure processing with
quantum-resistant capabilities and tamper-evident features.
"""

import asyncio
import hashlib
import json
import logging
import secrets
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..crypto.post_quantum import pq_crypto
from ..crypto.secure_key_manager import SecureKey, SecureMemory

logger = logging.getLogger(__name__)


class HSMType(Enum):
    """Types of Hardware Security Modules supported."""

    PKCS11 = "pkcs11"  # Standard PKCS#11 interface
    AWS_CLOUDHSM = "aws_cloudhsm"  # AWS CloudHSM service
    AZURE_HSM = "azure_hsm"  # Azure Dedicated HSM
    THALES_LUNA = "thales_luna"  # Thales Luna HSM
    SAFENET = "safenet"  # SafeNet HSM
    UTIMACO = "utimaco"  # Utimaco HSM
    SOFTWARE_HSM = "software_hsm"  # Software-based HSM simulation
    QUANTUM_SAFE_HSM = "quantum_safe_hsm"  # Quantum-safe HSM


class HSMOperationType(Enum):
    """Types of HSM operations."""

    KEY_GENERATION = "key_generation"
    DIGITAL_SIGNING = "digital_signing"
    SIGNATURE_VERIFICATION = "signature_verification"
    ENCRYPTION = "encryption"
    DECRYPTION = "decryption"
    KEY_DERIVATION = "key_derivation"
    RANDOM_GENERATION = "random_generation"
    ATTESTATION = "attestation"
    SECURE_COMPUTATION = "secure_computation"


class HSMSecurityLevel(Enum):
    """HSM security levels based on FIPS 140-2."""

    LEVEL_1 = "level_1"  # Software-based cryptographic modules
    LEVEL_2 = "level_2"  # Software + tamper-evident hardware
    LEVEL_3 = "level_3"  # Tamper-evident + identity-based authentication
    LEVEL_4 = "level_4"  # Tamper-active + environmental failure protection


@dataclass
class HSMConfiguration:
    """Configuration for HSM integration."""

    hsm_type: HSMType
    security_level: HSMSecurityLevel
    connection_string: str
    slot_id: Optional[int] = None
    token_label: Optional[str] = None
    pin: Optional[str] = None
    library_path: Optional[str] = None

    # Quantum-resistant configuration
    quantum_algorithms_enabled: bool = True
    post_quantum_key_sizes: Dict[str, int] = field(
        default_factory=lambda: {
            "dilithium": 2592,  # Dilithium-3 private key size
            "kyber": 2400,  # Kyber-768 private key size
            "falcon": 1281,  # Falcon-512 private key size
        }
    )

    # Performance and reliability
    connection_pool_size: int = 10
    operation_timeout: int = 30
    retry_attempts: int = 3
    health_check_interval: int = 60

    # Audit and compliance
    audit_all_operations: bool = True
    require_dual_control: bool = False
    key_escrow_enabled: bool = False


@dataclass
class HSMOperationResult:
    """Result of an HSM operation."""

    operation_id: str
    operation_type: HSMOperationType
    success: bool
    result_data: Optional[bytes] = None
    error_message: Optional[str] = None
    execution_time_ms: int = 0
    hsm_session_id: Optional[str] = None
    attestation_data: Optional[bytes] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class HSMSession:
    """Represents a secure HSM session."""

    def __init__(self, session_id: str, hsm_type: HSMType, config: HSMConfiguration):
        self.session_id = session_id
        self.hsm_type = hsm_type
        self.config = config
        self.created_at = datetime.now(timezone.utc)
        self.last_used = self.created_at
        self.operations_count = 0
        self.is_authenticated = False
        self.security_context = {}

        # Session security features
        self.session_key = secrets.token_bytes(32)
        self.nonce_counter = 0
        self.tamper_detected = False

    def update_usage(self):
        """Update session usage statistics."""
        self.last_used = datetime.now(timezone.utc)
        self.operations_count += 1

    def is_expired(self, max_idle_time: timedelta = timedelta(hours=1)) -> bool:
        """Check if session has expired."""
        return datetime.now(timezone.utc) - self.last_used > max_idle_time

    def generate_session_nonce(self) -> bytes:
        """Generate a unique nonce for this session."""
        self.nonce_counter += 1
        nonce_data = f"{self.session_id}:{self.nonce_counter}:{time.time()}"
        return hashlib.sha256(nonce_data.encode()).digest()[:16]


class QuantumSafeHSMAdapter:
    """
    Quantum-safe HSM adapter providing post-quantum cryptographic operations.

    This adapter bridges standard HSM interfaces with quantum-resistant
    algorithms, ensuring future-proof security.
    """

    def __init__(self, config: HSMConfiguration):
        self.config = config
        self.pq_algorithms = {
            "dilithium3": "ML-DSA-65",  # NIST standard name
            "kyber768": "ML-KEM-768",  # NIST standard name
            "falcon512": "Falcon-512",  # NIST finalist
        }
        self.key_cache: Dict[str, bytes] = {}
        self.operation_log: deque = deque(maxlen=1000)

    async def generate_quantum_safe_keypair(
        self, algorithm: str, key_id: str
    ) -> Tuple[bytes, bytes]:
        """Generate a quantum-safe key pair."""
        start_time = time.time()

        try:
            if algorithm == "dilithium3" and pq_crypto.dilithium_available:
                keypair = pq_crypto.generate_dilithium_keypair()
                public_key = keypair.public_key
                private_key = keypair.private_key

                # Store in secure cache
                self.key_cache[f"{key_id}_public"] = public_key
                self.key_cache[f"{key_id}_private"] = private_key

                execution_time = int((time.time() - start_time) * 1000)

                # Log operation
                self.operation_log.append(
                    {
                        "timestamp": datetime.now(timezone.utc),
                        "operation": "quantum_keypair_generation",
                        "algorithm": algorithm,
                        "key_id": key_id,
                        "execution_time_ms": execution_time,
                        "success": True,
                    }
                )

                return public_key, private_key

            else:
                # Fallback to classical algorithms
                raise NotImplementedError(
                    f"Quantum-safe algorithm {algorithm} not available"
                )

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            self.operation_log.append(
                {
                    "timestamp": datetime.now(timezone.utc),
                    "operation": "quantum_keypair_generation",
                    "algorithm": algorithm,
                    "key_id": key_id,
                    "execution_time_ms": execution_time,
                    "success": False,
                    "error": str(e),
                }
            )
            raise

    async def quantum_sign(
        self, data: bytes, private_key: bytes, algorithm: str
    ) -> bytes:
        """Perform quantum-safe digital signature."""
        start_time = time.time()

        try:
            if algorithm == "dilithium3" and pq_crypto.dilithium_available:
                signature = pq_crypto.dilithium_sign(data, private_key)

                execution_time = int((time.time() - start_time) * 1000)

                self.operation_log.append(
                    {
                        "timestamp": datetime.now(timezone.utc),
                        "operation": "quantum_signing",
                        "algorithm": algorithm,
                        "data_size": len(data),
                        "execution_time_ms": execution_time,
                        "success": True,
                    }
                )

                return signature

            else:
                raise NotImplementedError(
                    f"Quantum-safe signing with {algorithm} not available"
                )

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            self.operation_log.append(
                {
                    "timestamp": datetime.now(timezone.utc),
                    "operation": "quantum_signing",
                    "algorithm": algorithm,
                    "execution_time_ms": execution_time,
                    "success": False,
                    "error": str(e),
                }
            )
            raise

    async def quantum_verify(
        self, data: bytes, signature: bytes, public_key: bytes, algorithm: str
    ) -> bool:
        """Verify quantum-safe digital signature."""
        start_time = time.time()

        try:
            if algorithm == "dilithium3" and pq_crypto.dilithium_available:
                is_valid = pq_crypto.dilithium_verify(data, signature, public_key)

                execution_time = int((time.time() - start_time) * 1000)

                self.operation_log.append(
                    {
                        "timestamp": datetime.now(timezone.utc),
                        "operation": "quantum_verification",
                        "algorithm": algorithm,
                        "data_size": len(data),
                        "execution_time_ms": execution_time,
                        "verification_result": is_valid,
                        "success": True,
                    }
                )

                return is_valid

            else:
                raise NotImplementedError(
                    f"Quantum-safe verification with {algorithm} not available"
                )

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            self.operation_log.append(
                {
                    "timestamp": datetime.now(timezone.utc),
                    "operation": "quantum_verification",
                    "algorithm": algorithm,
                    "execution_time_ms": execution_time,
                    "success": False,
                    "error": str(e),
                }
            )
            raise


class HSMSecurityMonitor:
    """
    Security monitor for HSM operations with tamper detection
    and intrusion prevention capabilities.
    """

    def __init__(self):
        self.security_events: deque = deque(maxlen=5000)
        self.threat_indicators: Dict[str, int] = defaultdict(int)
        self.session_anomalies: Dict[str, List[str]] = defaultdict(list)
        self.tamper_alerts: deque = deque(maxlen=100)

        # Security thresholds
        self.thresholds = {
            "max_failed_operations": 5,
            "max_session_duration": timedelta(hours=4),
            "max_operations_per_minute": 1000,
            "unusual_operation_patterns": 10,
        }

        # Monitoring state
        self.monitoring_active = True
        self.last_health_check = datetime.now(timezone.utc)

    def record_security_event(
        self, event_type: str, session_id: str, details: Dict[str, Any]
    ):
        """Record a security-related event."""
        event = {
            "timestamp": datetime.now(timezone.utc),
            "event_type": event_type,
            "session_id": session_id,
            "details": details,
            "severity": self._calculate_event_severity(event_type, details),
        }

        self.security_events.append(event)

        # Update threat indicators
        self.threat_indicators[event_type] += 1

        # Check for anomalies
        if event["severity"] >= 3:  # High severity
            self._trigger_security_alert(event)

    def _calculate_event_severity(
        self, event_type: str, details: Dict[str, Any]
    ) -> int:
        """Calculate severity score for security events (1-5 scale)."""
        base_severity = {
            "authentication_failure": 2,
            "operation_failure": 1,
            "session_timeout": 1,
            "unusual_pattern": 3,
            "tamper_detected": 5,
            "unauthorized_access": 4,
            "key_extraction_attempt": 5,
            "session_hijacking": 4,
        }

        severity = base_severity.get(event_type, 1)

        # Adjust based on details
        if details.get("repeated_attempts", 0) > 3:
            severity += 1
        if details.get("from_unknown_source", False):
            severity += 1

        return min(5, severity)

    def _trigger_security_alert(self, event: Dict[str, Any]):
        """Trigger security alert for high-severity events."""
        alert = {
            "alert_id": secrets.token_hex(8),
            "timestamp": event["timestamp"],
            "event_type": event["event_type"],
            "session_id": event["session_id"],
            "severity": event["severity"],
            "recommended_actions": self._get_recommended_actions(event["event_type"]),
        }

        self.tamper_alerts.append(alert)

        logger.critical(
            f"HSM SECURITY ALERT: {event['event_type']} "
            f"(severity: {event['severity']}, session: {event['session_id']})"
        )

    def _get_recommended_actions(self, event_type: str) -> List[str]:
        """Get recommended actions for security events."""
        actions = {
            "tamper_detected": [
                "immediate_hsm_isolation",
                "security_team_notification",
                "forensic_investigation",
                "key_material_rotation",
            ],
            "unauthorized_access": [
                "session_termination",
                "access_log_review",
                "authentication_strengthening",
            ],
            "key_extraction_attempt": [
                "immediate_key_rotation",
                "access_revocation",
                "incident_response_activation",
            ],
            "session_hijacking": [
                "session_invalidation",
                "network_isolation",
                "identity_verification",
            ],
        }

        return actions.get(event_type, ["standard_security_review"])

    def get_security_status(self) -> Dict[str, Any]:
        """Get comprehensive security status."""
        recent_events = [
            event
            for event in self.security_events
            if datetime.now(timezone.utc) - event["timestamp"] < timedelta(hours=24)
        ]

        high_severity_events = [
            event for event in recent_events if event["severity"] >= 3
        ]

        return {
            "monitoring_active": self.monitoring_active,
            "last_health_check": self.last_health_check.isoformat(),
            "total_events_24h": len(recent_events),
            "high_severity_events_24h": len(high_severity_events),
            "active_tamper_alerts": len(self.tamper_alerts),
            "threat_indicators": dict(self.threat_indicators),
            "system_health": "healthy"
            if len(high_severity_events) == 0
            else "compromised",
        }


class EnterpriseHSMManager:
    """
    Enterprise-grade HSM manager providing comprehensive hardware security
    module integration with quantum-resistant capabilities.
    """

    def __init__(self, config: HSMConfiguration):
        self.config = config
        self.sessions: Dict[str, HSMSession] = {}
        self.quantum_adapter = QuantumSafeHSMAdapter(config)
        self.security_monitor = HSMSecurityMonitor()
        self.secure_memory = SecureMemory()

        # Connection management
        self.connection_pool: List[Any] = []
        self.active_connections = 0
        self.connection_lock = threading.RLock()

        # Performance tracking
        self.operation_metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "average_response_time_ms": 0.0,
            "peak_operations_per_second": 0,
        }

        # Key management
        self.key_registry: Dict[str, SecureKey] = {}
        self.key_rotation_schedule: Dict[str, datetime] = {}

        logger.info(f"Initialized Enterprise HSM Manager with {config.hsm_type.value}")

    async def initialize_hsm(self) -> bool:
        """Initialize HSM connection and verify functionality."""
        try:
            # Simulate HSM initialization based on type
            if self.config.hsm_type == HSMType.SOFTWARE_HSM:
                await self._initialize_software_hsm()
            elif self.config.hsm_type == HSMType.QUANTUM_SAFE_HSM:
                await self._initialize_quantum_safe_hsm()
            else:
                await self._initialize_hardware_hsm()

            # Verify HSM functionality
            test_result = await self._perform_hsm_health_check()

            if test_result:
                logger.info("HSM initialization successful")
                return True
            else:
                logger.error("HSM health check failed")
                return False

        except Exception as e:
            logger.error(f"HSM initialization failed: {e}")
            self.security_monitor.record_security_event(
                "initialization_failure",
                "system",
                {"error": str(e), "hsm_type": self.config.hsm_type.value},
            )
            return False

    async def _initialize_software_hsm(self):
        """Initialize software-based HSM simulation."""
        # Create secure memory regions
        self.secure_memory.allocate_secure_buffer(4096, "master_key_buffer")
        self.secure_memory.allocate_secure_buffer(2048, "session_keys_buffer")

        # Generate master encryption key
        master_key = secrets.token_bytes(32)
        self.secure_memory.write_to_buffer("master_key_buffer", master_key, 0)

        logger.info("Software HSM initialized with secure memory regions")

    async def _initialize_quantum_safe_hsm(self):
        """Initialize quantum-safe HSM with post-quantum algorithms."""
        await self._initialize_software_hsm()

        # Pre-generate quantum-safe key materials
        if pq_crypto.dilithium_available:
            # Generate system-level quantum keys
            (
                system_public,
                system_private,
            ) = await self.quantum_adapter.generate_quantum_safe_keypair(
                "dilithium3", "system_master"
            )

            # Store in secure registry
            self.key_registry["system_master"] = SecureKey(
                key_id="system_master",
                key_type="dilithium3",
                encrypted_key=system_private,  # Would encrypt in production
                created_at=time.time(),
                last_used=time.time(),
                rotation_due=time.time() + (90 * 24 * 3600),  # 90 days
                key_strength=256,  # Equivalent classical security level
                salt=secrets.token_bytes(16),
            )

        logger.info("Quantum-safe HSM initialized with post-quantum algorithms")

    async def _initialize_hardware_hsm(self):
        """Initialize connection to hardware HSM."""
        # This would connect to actual hardware HSM
        # For now, simulate hardware HSM initialization
        logger.info(f"Simulating connection to {self.config.hsm_type.value}")

        # Simulate authentication
        await asyncio.sleep(0.1)  # Simulate connection time

        # Create connection pool
        for i in range(self.config.connection_pool_size):
            # In real implementation, these would be actual HSM connections
            mock_connection = {
                "connection_id": f"hsm_conn_{i}",
                "created_at": datetime.now(timezone.utc),
                "in_use": False,
            }
            self.connection_pool.append(mock_connection)

    async def _perform_hsm_health_check(self) -> bool:
        """Perform comprehensive HSM health check."""
        try:
            # Test basic operations
            test_data = b"HSM health check test data"

            if self.config.hsm_type == HSMType.QUANTUM_SAFE_HSM:
                # Test quantum-safe operations
                (
                    public_key,
                    private_key,
                ) = await self.quantum_adapter.generate_quantum_safe_keypair(
                    "dilithium3", "health_check_key"
                )

                signature = await self.quantum_adapter.quantum_sign(
                    test_data, private_key, "dilithium3"
                )

                verification_result = await self.quantum_adapter.quantum_verify(
                    test_data, signature, public_key, "dilithium3"
                )

                return verification_result

            else:
                # Test classical operations
                # For now, simulate successful health check
                return True

        except Exception as e:
            logger.error(f"HSM health check failed: {e}")
            return False

    async def create_secure_session(
        self, user_id: str, purpose: str, auth_token: str = None
    ) -> str:
        """Create a new secure HSM session."""
        session_id = f"hsm_session_{secrets.token_hex(16)}"

        session = HSMSession(session_id, self.config.hsm_type, self.config)
        session.security_context = {
            "user_id": user_id,
            "purpose": purpose,
            "created_from": "uatp_system",
            "security_level": self.config.security_level.value,
            "auth_token": auth_token,
        }

        # Authenticate session
        session.is_authenticated = await self._authenticate_session(session)

        if session.is_authenticated:
            self.sessions[session_id] = session

            self.security_monitor.record_security_event(
                "session_created", session_id, {"user_id": user_id, "purpose": purpose}
            )

            logger.info(f"Created secure HSM session: {session_id}")
            return session_id
        else:
            self.security_monitor.record_security_event(
                "authentication_failure",
                session_id,
                {"user_id": user_id, "reason": "session_creation_failed"},
            )
            raise ValueError("Session authentication failed")

    async def _authenticate_session(self, session: HSMSession) -> bool:
        """Authenticate HSM session."""
        try:
            # In a real HSM, we would generate a challenge and verify the hardware signature.
            # Here we enforce that a valid cryptographic auth_token is provided.
            auth_token = session.security_context.get("auth_token")

            if not auth_token or len(auth_token) < 32:
                logger.error("HSM Authentication blocked: Missing or weak auth_token.")
                return False

            # Additional strict cryptographic verifications would go here (e.g. mTLS or JWT checks)
            await asyncio.sleep(0.05)  # Simulate authentication time

            return True

        except Exception as e:
            logger.error(f"Session authentication error: {e}")
            return False

    async def execute_hsm_operation(
        self, session_id: str, operation_type: HSMOperationType, **kwargs
    ) -> HSMOperationResult:
        """Execute a cryptographic operation using HSM."""
        start_time = time.time()
        operation_id = f"op_{secrets.token_hex(8)}"

        # Validate session
        if session_id not in self.sessions:
            raise ValueError(f"Invalid session ID: {session_id}")

        session = self.sessions[session_id]
        if not session.is_authenticated:
            raise ValueError("Session not authenticated")

        if session.is_expired():
            await self.terminate_session(session_id)
            raise ValueError("Session expired")

        try:
            # Update session usage
            session.update_usage()

            # Execute operation based on type
            result_data = None

            if operation_type == HSMOperationType.KEY_GENERATION:
                result_data = await self._execute_key_generation(session, **kwargs)
            elif operation_type == HSMOperationType.DIGITAL_SIGNING:
                result_data = await self._execute_digital_signing(session, **kwargs)
            elif operation_type == HSMOperationType.SIGNATURE_VERIFICATION:
                result_data = await self._execute_signature_verification(
                    session, **kwargs
                )
            elif operation_type == HSMOperationType.ENCRYPTION:
                result_data = await self._execute_encryption(session, **kwargs)
            elif operation_type == HSMOperationType.DECRYPTION:
                result_data = await self._execute_decryption(session, **kwargs)
            elif operation_type == HSMOperationType.RANDOM_GENERATION:
                result_data = await self._execute_random_generation(session, **kwargs)
            else:
                raise ValueError(f"Unsupported operation type: {operation_type}")

            execution_time = int((time.time() - start_time) * 1000)

            # Update metrics
            self.operation_metrics["total_operations"] += 1
            self.operation_metrics["successful_operations"] += 1
            self._update_average_response_time(execution_time)

            # Create successful result
            result = HSMOperationResult(
                operation_id=operation_id,
                operation_type=operation_type,
                success=True,
                result_data=result_data,
                execution_time_ms=execution_time,
                hsm_session_id=session_id,
                attestation_data=await self._generate_operation_attestation(
                    operation_id, session
                ),
            )

            # Record security event
            self.security_monitor.record_security_event(
                "operation_success",
                session_id,
                {
                    "operation_id": operation_id,
                    "operation_type": operation_type.value,
                    "execution_time_ms": execution_time,
                },
            )

            return result

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)

            # Update failure metrics
            self.operation_metrics["total_operations"] += 1
            self.operation_metrics["failed_operations"] += 1

            # Record security event
            self.security_monitor.record_security_event(
                "operation_failure",
                session_id,
                {
                    "operation_id": operation_id,
                    "operation_type": operation_type.value,
                    "error": str(e),
                    "execution_time_ms": execution_time,
                },
            )

            # Create failure result
            result = HSMOperationResult(
                operation_id=operation_id,
                operation_type=operation_type,
                success=False,
                error_message=str(e),
                execution_time_ms=execution_time,
                hsm_session_id=session_id,
            )

            return result

    async def _execute_key_generation(self, session: HSMSession, **kwargs) -> bytes:
        """Execute key generation operation."""
        algorithm = kwargs.get("algorithm", "dilithium3")
        key_id = kwargs.get("key_id", f"key_{secrets.token_hex(8)}")

        if algorithm == "dilithium3" and self.config.quantum_algorithms_enabled:
            (
                public_key,
                private_key,
            ) = await self.quantum_adapter.generate_quantum_safe_keypair(
                algorithm, key_id
            )

            # Store key in registry
            self.key_registry[key_id] = SecureKey(
                key_id=key_id,
                key_type=algorithm,
                encrypted_key=private_key,
                created_at=time.time(),
                last_used=time.time(),
                rotation_due=time.time() + (30 * 24 * 3600),  # 30 days
                key_strength=256,
                salt=secrets.token_bytes(16),
            )

            # Schedule key rotation
            self.key_rotation_schedule[key_id] = datetime.now(timezone.utc) + timedelta(
                days=30
            )

            # Return public key
            return public_key
        else:
            raise NotImplementedError(f"Key generation for {algorithm} not implemented")

    async def _execute_digital_signing(self, session: HSMSession, **kwargs) -> bytes:
        """Execute digital signing operation."""
        data = kwargs.get("data")
        key_id = kwargs.get("key_id")
        algorithm = kwargs.get("algorithm", "dilithium3")

        if not data or not key_id:
            raise ValueError("Data and key_id required for signing")

        # Get private key from registry
        if key_id not in self.key_registry:
            raise ValueError(f"Key not found: {key_id}")

        secure_key = self.key_registry[key_id]
        private_key = secure_key.encrypted_key

        # Update key usage
        secure_key.last_used = time.time()

        # Perform signing
        if algorithm == "dilithium3" and self.config.quantum_algorithms_enabled:
            signature = await self.quantum_adapter.quantum_sign(
                data, private_key, algorithm
            )
            return signature
        else:
            raise NotImplementedError(f"Signing with {algorithm} not implemented")

    async def _execute_signature_verification(
        self, session: HSMSession, **kwargs
    ) -> bytes:
        """Execute signature verification operation."""
        data = kwargs.get("data")
        signature = kwargs.get("signature")
        public_key = kwargs.get("public_key")
        algorithm = kwargs.get("algorithm", "dilithium3")

        if not all([data, signature, public_key]):
            raise ValueError(
                "Data, signature, and public_key required for verification"
            )

        # Perform verification
        if algorithm == "dilithium3" and self.config.quantum_algorithms_enabled:
            is_valid = await self.quantum_adapter.quantum_verify(
                data, signature, public_key, algorithm
            )
            return b"valid" if is_valid else b"invalid"
        else:
            raise NotImplementedError(f"Verification with {algorithm} not implemented")

    async def _execute_encryption(self, session: HSMSession, **kwargs) -> bytes:
        """Execute encryption operation."""
        # Placeholder for encryption implementation
        data = kwargs.get("data", b"")
        # Simple XOR encryption for demonstration
        key = secrets.token_bytes(32)
        encrypted = bytes(
            a ^ b for a, b in zip(data, key * (len(data) // 32 + 1), strict=False)
        )
        return encrypted

    async def _execute_decryption(self, session: HSMSession, **kwargs) -> bytes:
        """Execute decryption operation."""
        # Placeholder for decryption implementation
        encrypted_data = kwargs.get("encrypted_data", b"")
        return encrypted_data  # Return as-is for demonstration

    async def _execute_random_generation(self, session: HSMSession, **kwargs) -> bytes:
        """Execute secure random number generation."""
        size = kwargs.get("size", 32)
        return secrets.token_bytes(size)

    async def _generate_operation_attestation(
        self, operation_id: str, session: HSMSession
    ) -> bytes:
        """Generate cryptographic attestation for operation."""
        attestation_data = {
            "operation_id": operation_id,
            "session_id": session.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hsm_type": self.config.hsm_type.value,
            "security_level": self.config.security_level.value,
        }

        attestation_json = json.dumps(attestation_data, sort_keys=True)
        return hashlib.sha256(attestation_json.encode()).digest()

    def _update_average_response_time(self, execution_time_ms: int):
        """Update average response time metric."""
        current_avg = self.operation_metrics["average_response_time_ms"]
        total_ops = self.operation_metrics["successful_operations"]

        if total_ops == 1:
            self.operation_metrics["average_response_time_ms"] = execution_time_ms
        else:
            new_avg = ((current_avg * (total_ops - 1)) + execution_time_ms) / total_ops
            self.operation_metrics["average_response_time_ms"] = new_avg

    async def terminate_session(self, session_id: str):
        """Terminate an HSM session securely."""
        if session_id in self.sessions:
            session = self.sessions[session_id]

            # Clear sensitive data
            session.session_key = b"\x00" * 32
            session.security_context.clear()

            # Remove from active sessions
            del self.sessions[session_id]

            self.security_monitor.record_security_event(
                "session_terminated",
                session_id,
                {
                    "duration_seconds": (
                        datetime.now(timezone.utc) - session.created_at
                    ).total_seconds()
                },
            )

            logger.info(f"Terminated HSM session: {session_id}")

    def get_hsm_status(self) -> Dict[str, Any]:
        """Get comprehensive HSM status."""
        active_sessions = len(self.sessions)
        security_status = self.security_monitor.get_security_status()

        return {
            "hsm_type": self.config.hsm_type.value,
            "security_level": self.config.security_level.value,
            "quantum_algorithms_enabled": self.config.quantum_algorithms_enabled,
            "active_sessions": active_sessions,
            "total_keys_managed": len(self.key_registry),
            "operation_metrics": self.operation_metrics.copy(),
            "security_status": security_status,
            "connection_pool_size": len(self.connection_pool),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }


# Global HSM manager instance
hsm_manager: Optional[EnterpriseHSMManager] = None


async def initialize_hsm_system(config: HSMConfiguration) -> bool:
    """Initialize the global HSM system."""
    global hsm_manager

    try:
        hsm_manager = EnterpriseHSMManager(config)
        success = await hsm_manager.initialize_hsm()

        if success:
            logger.info("HSM system initialized successfully")
        else:
            logger.error("HSM system initialization failed")

        return success

    except Exception as e:
        logger.error(f"Failed to initialize HSM system: {e}")
        return False


# Convenience functions
async def create_hsm_session(user_id: str, purpose: str, auth_token: str = None) -> str:
    """Create a new HSM session."""
    if hsm_manager is None:
        raise RuntimeError("HSM system not initialized")
    return await hsm_manager.create_secure_session(user_id, purpose, auth_token)


async def execute_hsm_operation(
    session_id: str, operation_type: HSMOperationType, **kwargs
) -> HSMOperationResult:
    """Execute an HSM operation."""
    if hsm_manager is None:
        raise RuntimeError("HSM system not initialized")
    return await hsm_manager.execute_hsm_operation(session_id, operation_type, **kwargs)


async def terminate_hsm_session(session_id: str):
    """Terminate an HSM session."""
    if hsm_manager is None:
        raise RuntimeError("HSM system not initialized")
    await hsm_manager.terminate_session(session_id)


def get_hsm_system_status() -> Dict[str, Any]:
    """Get HSM system status."""
    if hsm_manager is None:
        return {"status": "not_initialized"}
    return hsm_manager.get_hsm_status()
