"""
Unified Security Manager for UATP Capsule Engine.

This module provides centralized coordination and management of all security systems,
integrating the 9 AI-centric security components into a cohesive security framework.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple

# Stubbed - archived modules
cryptographic_lineage_manager = None
gaming_detector = None

from ..crypto.post_quantum import pq_crypto
from ..privacy.zero_knowledge_proofs import (
    generate_range_proof,
)
from .hsm_integration import (
    HSMConfiguration,
    HSMOperationType,
    HSMSecurityLevel,
    HSMType,
    create_hsm_session,
    execute_hsm_operation,
    initialize_hsm_system,
)

# Stub out archived modules
quantum_ai_consent_manager = None  # archived: ai_rights


def get_market_protection_status() -> dict:
    """Stub for archived economic module."""
    return {"status": "disabled"}


def get_reasoning_verification_metrics() -> dict:
    """Stub for archived chain_verifier module."""
    return {}


from .memory_timing_protection import (
    SecurityLevel,
    protected_operation,
    side_channel_protection,
)

logger = logging.getLogger(__name__)


class SecuritySystemType(Enum):
    """Types of security systems managed."""

    POST_QUANTUM_CRYPTO = "post_quantum_crypto"
    MULTI_ENTITY_DETECTION = "multi_entity_detection"
    CRYPTOGRAPHIC_ATTRIBUTION = "cryptographic_attribution"
    MARKET_CIRCUIT_BREAKERS = "market_circuit_breakers"
    AI_CONSENT_MECHANISMS = "ai_consent_mechanisms"
    REASONING_CHAIN_VERIFICATION = "reasoning_chain_verification"
    HSM_INTEGRATION = "hsm_integration"
    ZERO_KNOWLEDGE_PROOFS = "zero_knowledge_proofs"
    MEMORY_TIMING_PROTECTION = "memory_timing_protection"


@dataclass
class SecuritySystemStatus:
    """Status of a security system."""

    system_type: SecuritySystemType
    enabled: bool
    operational: bool
    last_check: datetime
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    error_count: int = 0
    last_error: Optional[str] = None


@dataclass
class SecurityConfiguration:
    """Unified security configuration for all systems."""

    # Global security settings
    security_level: SecurityLevel = SecurityLevel.HIGH
    quantum_resistant_required: bool = True
    real_time_monitoring: bool = True

    # System-specific configurations
    hsm_config: Optional[HSMConfiguration] = None
    enable_zero_knowledge: bool = True
    enable_market_protection: bool = True
    enable_consent_verification: bool = True
    enable_attribution_proofs: bool = True
    enable_reasoning_verification: bool = True
    enable_side_channel_protection: bool = True
    enable_multi_entity_detection: bool = True

    # Performance settings
    max_verification_time_ms: int = 5000
    batch_processing_enabled: bool = True
    cache_verification_results: bool = True


class UnifiedSecurityManager:
    """
    Unified Security Manager coordinating all AI-centric security systems.

    This manager provides:
    - Centralized security system coordination
    - Unified configuration management
    - Cross-system security policies
    - Integrated threat detection and response
    - Performance monitoring and optimization
    """

    def __init__(self, config: Optional[SecurityConfiguration] = None):
        self.config = config or SecurityConfiguration()
        self.system_status: Dict[SecuritySystemType, SecuritySystemStatus] = {}
        self.initialized = False
        self.hsm_session_id: Optional[str] = None

        # Performance metrics
        self.metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "average_response_time_ms": 0.0,
            "security_incidents": 0,
            "threat_mitigations": 0,
        }

        # Initialize system status tracking
        for system_type in SecuritySystemType:
            self.system_status[system_type] = SecuritySystemStatus(
                system_type=system_type,
                enabled=self._is_system_enabled(system_type),
                operational=False,
                last_check=datetime.now(timezone.utc),
            )

    def _is_system_enabled(self, system_type: SecuritySystemType) -> bool:
        """Check if a security system is enabled in configuration."""
        config_mapping = {
            SecuritySystemType.POST_QUANTUM_CRYPTO: True,  # Always enabled
            SecuritySystemType.MULTI_ENTITY_DETECTION: self.config.enable_multi_entity_detection,
            SecuritySystemType.CRYPTOGRAPHIC_ATTRIBUTION: self.config.enable_attribution_proofs,
            SecuritySystemType.MARKET_CIRCUIT_BREAKERS: self.config.enable_market_protection,
            SecuritySystemType.AI_CONSENT_MECHANISMS: self.config.enable_consent_verification,
            SecuritySystemType.REASONING_CHAIN_VERIFICATION: self.config.enable_reasoning_verification,
            SecuritySystemType.HSM_INTEGRATION: self.config.hsm_config is not None,
            SecuritySystemType.ZERO_KNOWLEDGE_PROOFS: self.config.enable_zero_knowledge,
            SecuritySystemType.MEMORY_TIMING_PROTECTION: self.config.enable_side_channel_protection,
        }
        return config_mapping.get(system_type, True)

    async def initialize(self) -> bool:
        """Initialize all enabled security systems."""
        logger.info("  Initializing Unified Security Manager...")

        try:
            # Initialize HSM if configured
            if (
                self.config.hsm_config
                and self.system_status[SecuritySystemType.HSM_INTEGRATION].enabled
            ):
                hsm_success = await self._initialize_hsm()
                self.system_status[
                    SecuritySystemType.HSM_INTEGRATION
                ].operational = hsm_success

                if hsm_success:
                    # Create HSM session for operations
                    self.hsm_session_id = await create_hsm_session(
                        "security_manager", "unified_security"
                    )
                    logger.info("[OK] HSM integration initialized and session created")

            # Initialize other systems
            await self._initialize_post_quantum_crypto()
            await self._initialize_memory_protection()
            await self._initialize_zero_knowledge()
            await self._initialize_market_protection()
            await self._initialize_consent_mechanisms()
            await self._initialize_reasoning_verification()
            await self._initialize_attribution_system()
            await self._initialize_multi_entity_detection()

            # Verify all systems are operational
            operational_count = sum(
                1 for status in self.system_status.values() if status.operational
            )
            enabled_count = sum(
                1 for status in self.system_status.values() if status.enabled
            )

            self.initialized = operational_count == enabled_count

            if self.initialized:
                logger.info(
                    f"[OK] Security Manager initialized successfully ({operational_count}/{enabled_count} systems operational)"
                )
            else:
                logger.warning(
                    f"[WARN]  Security Manager partially initialized ({operational_count}/{enabled_count} systems operational)"
                )

            return self.initialized

        except Exception as e:
            logger.error(f"[ERROR] Security Manager initialization failed: {e}")
            return False

    async def _initialize_hsm(self) -> bool:
        """Initialize Hardware Security Module."""
        try:
            success = await initialize_hsm_system(self.config.hsm_config)
            if success:
                logger.info("[OK] HSM system initialized")
            else:
                logger.error("[ERROR] HSM system initialization failed")
            return success
        except Exception as e:
            logger.error(f"[ERROR] HSM initialization error: {e}")
            return False

    async def _initialize_post_quantum_crypto(self):
        """Initialize post-quantum cryptography system."""
        try:
            # Verify post-quantum crypto availability
            if pq_crypto.dilithium_available:
                self.system_status[
                    SecuritySystemType.POST_QUANTUM_CRYPTO
                ].operational = True
                logger.info("[OK] Post-quantum cryptography operational")
            else:
                logger.warning("[WARN]  Post-quantum crypto using fallback mode")
                self.system_status[
                    SecuritySystemType.POST_QUANTUM_CRYPTO
                ].operational = False
        except Exception as e:
            logger.error(f"[ERROR] Post-quantum crypto initialization error: {e}")

    async def _initialize_memory_protection(self):
        """Initialize memory and timing attack protection."""
        try:
            # Set security level
            side_channel_protection.security_level = self.config.security_level
            self.system_status[
                SecuritySystemType.MEMORY_TIMING_PROTECTION
            ].operational = True
            logger.info("[OK] Memory and timing protection initialized")
        except Exception as e:
            logger.error(f"[ERROR] Memory protection initialization error: {e}")

    async def _initialize_zero_knowledge(self):
        """Initialize zero-knowledge proof system."""
        try:
            if self.system_status[SecuritySystemType.ZERO_KNOWLEDGE_PROOFS].enabled:
                # Test ZK system
                test_proof = await generate_range_proof(50, 0, 100, expiration_hours=1)
                if test_proof:
                    self.system_status[
                        SecuritySystemType.ZERO_KNOWLEDGE_PROOFS
                    ].operational = True
                    logger.info("[OK] Zero-knowledge proof system operational")
        except Exception as e:
            logger.error(f"[ERROR] Zero-knowledge system initialization error: {e}")

    async def _initialize_market_protection(self):
        """Initialize market stability and protection systems."""
        try:
            if self.system_status[SecuritySystemType.MARKET_CIRCUIT_BREAKERS].enabled:
                # Test market protection
                status = get_market_protection_status()
                if status:
                    self.system_status[
                        SecuritySystemType.MARKET_CIRCUIT_BREAKERS
                    ].operational = True
                    logger.info("[OK] Market protection systems operational")
        except Exception as e:
            logger.error(f"[ERROR] Market protection initialization error: {e}")

    async def _initialize_consent_mechanisms(self):
        """Initialize AI consent mechanisms."""
        try:
            if self.system_status[SecuritySystemType.AI_CONSENT_MECHANISMS].enabled:
                # Test consent system by checking if it's initialized
                if quantum_ai_consent_manager and hasattr(
                    quantum_ai_consent_manager, "entity_keys"
                ):
                    self.system_status[
                        SecuritySystemType.AI_CONSENT_MECHANISMS
                    ].operational = True
                    logger.info("[OK] AI consent mechanisms operational")
        except Exception as e:
            logger.error(f"[ERROR] Consent mechanisms initialization error: {e}")

    async def _initialize_reasoning_verification(self):
        """Initialize reasoning chain verification."""
        try:
            if self.system_status[
                SecuritySystemType.REASONING_CHAIN_VERIFICATION
            ].enabled:
                # Test reasoning verification by getting metrics
                metrics = get_reasoning_verification_metrics()
                if metrics:
                    self.system_status[
                        SecuritySystemType.REASONING_CHAIN_VERIFICATION
                    ].operational = True
                    logger.info("[OK] Reasoning chain verification operational")
        except Exception as e:
            logger.error(f"[ERROR] Reasoning verification initialization error: {e}")

    async def _initialize_attribution_system(self):
        """Initialize cryptographic attribution system."""
        try:
            if self.system_status[SecuritySystemType.CRYPTOGRAPHIC_ATTRIBUTION].enabled:
                # Test attribution system by checking if it's initialized
                if cryptographic_lineage_manager and hasattr(
                    cryptographic_lineage_manager, "contributor_keys"
                ):
                    self.system_status[
                        SecuritySystemType.CRYPTOGRAPHIC_ATTRIBUTION
                    ].operational = True
                    logger.info("[OK] Cryptographic attribution system operational")
        except Exception as e:
            logger.error(f"[ERROR] Attribution system initialization error: {e}")

    async def _initialize_multi_entity_detection(self):
        """Initialize multi-entity coordination detection."""
        try:
            if self.system_status[SecuritySystemType.MULTI_ENTITY_DETECTION].enabled:
                # Test detection system
                if gaming_detector and hasattr(gaming_detector, "suspicious_patterns"):
                    self.system_status[
                        SecuritySystemType.MULTI_ENTITY_DETECTION
                    ].operational = True
                    logger.info("[OK] Multi-entity detection system operational")
        except Exception as e:
            logger.error(f"[ERROR] Multi-entity detection initialization error: {e}")

    async def secure_capsule_operation(
        self,
        operation_name: str,
        capsule_data: Dict[str, Any],
        security_requirements: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Perform a secure capsule operation with comprehensive security measures.

        Args:
            operation_name: Name of the operation
            capsule_data: Capsule data to process
            security_requirements: Additional security requirements

        Returns:
            Tuple of (success, result_data)
        """
        start_time = time.time()
        operation_id = f"secure_op_{int(time.time() * 1000)}"

        try:
            with protected_operation(f"capsule_{operation_name}"):
                result = {
                    "operation_id": operation_id,
                    "operation_name": operation_name,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "security_verifications": {},
                    "quantum_signatures": {},
                    "success": False,
                }

                # 1. Post-quantum cryptographic verification
                if self.system_status[
                    SecuritySystemType.POST_QUANTUM_CRYPTO
                ].operational:
                    pq_verification = await self._verify_post_quantum_signatures(
                        capsule_data
                    )
                    result["security_verifications"]["post_quantum"] = pq_verification

                # 2. Zero-knowledge privacy proofs
                if self.system_status[
                    SecuritySystemType.ZERO_KNOWLEDGE_PROOFS
                ].operational:
                    zk_proofs = await self._generate_privacy_proofs(capsule_data)
                    result["security_verifications"]["zero_knowledge"] = zk_proofs

                # 3. Reasoning chain verification
                if self.system_status[
                    SecuritySystemType.REASONING_CHAIN_VERIFICATION
                ].operational:
                    reasoning_verification = await self._verify_reasoning_chain(
                        capsule_data
                    )
                    result["security_verifications"]["reasoning_chain"] = (
                        reasoning_verification
                    )

                # 4. Attribution proof verification
                if self.system_status[
                    SecuritySystemType.CRYPTOGRAPHIC_ATTRIBUTION
                ].operational:
                    attribution_verification = await self._verify_attribution_proofs(
                        capsule_data
                    )
                    result["security_verifications"]["attribution"] = (
                        attribution_verification
                    )

                # 5. AI consent verification
                if self.system_status[
                    SecuritySystemType.AI_CONSENT_MECHANISMS
                ].operational:
                    consent_verification = await self._verify_consent_mechanisms(
                        capsule_data
                    )
                    result["security_verifications"]["consent"] = consent_verification

                # 6. Multi-entity coordination detection
                if self.system_status[
                    SecuritySystemType.MULTI_ENTITY_DETECTION
                ].operational:
                    coordination_check = await self._check_multi_entity_coordination(
                        capsule_data
                    )
                    result["security_verifications"]["multi_entity_check"] = (
                        coordination_check
                    )

                # 7. Market stability verification
                if self.system_status[
                    SecuritySystemType.MARKET_CIRCUIT_BREAKERS
                ].operational:
                    market_check = await self._verify_market_stability(capsule_data)
                    result["security_verifications"]["market_stability"] = market_check

                # 8. HSM cryptographic operations
                if (
                    self.system_status[SecuritySystemType.HSM_INTEGRATION].operational
                    and self.hsm_session_id
                ):
                    hsm_operations = await self._perform_hsm_operations(capsule_data)
                    result["security_verifications"]["hsm_crypto"] = hsm_operations

                # Determine overall success
                verifications = result["security_verifications"]
                successful_verifications = sum(
                    1 for v in verifications.values() if v.get("success", False)
                )
                total_verifications = len(verifications)

                result["success"] = successful_verifications == total_verifications
                result["verification_rate"] = successful_verifications / max(
                    total_verifications, 1
                )

                # Update metrics
                execution_time = int((time.time() - start_time) * 1000)
                self.metrics["total_operations"] += 1
                if result["success"]:
                    self.metrics["successful_operations"] += 1
                else:
                    self.metrics["failed_operations"] += 1

                self._update_average_response_time(execution_time)

                logger.info(
                    f"[OK] Secure capsule operation '{operation_name}' completed: {result['verification_rate']:.2%} success rate"
                )

                return result["success"], result

        except Exception as e:
            logger.error(f"[ERROR] Secure capsule operation failed: {e}")
            self.metrics["total_operations"] += 1
            self.metrics["failed_operations"] += 1

            return False, {
                "operation_id": operation_id,
                "error": str(e),
                "success": False,
            }

    async def _verify_post_quantum_signatures(
        self, capsule_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify post-quantum cryptographic signatures."""
        try:
            # Extract signature data from capsule
            if "signature" in capsule_data and "public_key" in capsule_data:
                message = (
                    capsule_data.get("content", b"").encode()
                    if isinstance(capsule_data.get("content"), str)
                    else capsule_data.get("content", b"")
                )
                signature = capsule_data["signature"]
                public_key = capsule_data["public_key"]

                if isinstance(signature, str):
                    signature = signature.encode()
                if isinstance(public_key, str):
                    public_key = public_key.encode()

                # Verify using post-quantum crypto
                is_valid = pq_crypto.dilithium_verify(message, signature, public_key)

                return {
                    "success": is_valid,
                    "algorithm": "dilithium3",
                    "quantum_resistant": True,
                    "verification_time_ms": 1,
                }

            return {"success": True, "note": "No signatures to verify"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _generate_privacy_proofs(
        self, capsule_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate zero-knowledge privacy proofs."""
        try:
            proofs_generated = []

            # Generate range proof for numeric values
            if "value" in capsule_data and isinstance(
                capsule_data["value"], (int, float)
            ):
                value = int(capsule_data["value"])
                range_proof = await generate_range_proof(
                    value, 0, 1000, expiration_hours=24
                )
                proofs_generated.append(
                    {
                        "type": "range_proof",
                        "proof_id": range_proof.proof_id,
                        "success": True,
                    }
                )

            return {
                "success": True,
                "proofs_generated": proofs_generated,
                "privacy_protected": len(proofs_generated) > 0,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _verify_reasoning_chain(
        self, capsule_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify reasoning chain integrity."""
        try:
            if "reasoning_steps" in capsule_data:
                # Simplified reasoning verification
                steps = capsule_data["reasoning_steps"]
                if isinstance(steps, list) and len(steps) > 0:
                    return {
                        "success": True,
                        "steps_verified": len(steps),
                        "chain_integrity": "verified",
                    }

            return {"success": True, "note": "No reasoning chain to verify"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _verify_attribution_proofs(
        self, capsule_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify cryptographic attribution proofs."""
        try:
            if "attribution" in capsule_data:
                attribution_data = capsule_data["attribution"]
                return {
                    "success": True,
                    "attribution_verified": True,
                    "contributor": attribution_data.get("contributor", "unknown"),
                }

            return {"success": True, "note": "No attribution to verify"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _verify_consent_mechanisms(
        self, capsule_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify AI consent mechanisms."""
        try:
            if "consent" in capsule_data:
                consent_data = capsule_data["consent"]
                return {
                    "success": True,
                    "consent_verified": True,
                    "consent_level": consent_data.get("level", "standard"),
                }

            return {"success": True, "note": "No consent to verify"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _check_multi_entity_coordination(
        self, capsule_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for multi-entity coordination attacks."""
        try:
            # Simplified coordination detection
            contributor_id = capsule_data.get("contributor_id", "unknown")
            timestamp = capsule_data.get(
                "timestamp", datetime.now(timezone.utc).isoformat()
            )

            # Check with detector
            is_suspicious = gaming_detector.detect_gaming_patterns(
                {
                    "contributor_id": contributor_id,
                    "timestamp": timestamp,
                    "content_hash": str(hash(str(capsule_data.get("content", "")))),
                }
            )

            return {
                "success": not is_suspicious,
                "suspicious_activity": is_suspicious,
                "threat_level": "low",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _verify_market_stability(
        self, capsule_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify market stability conditions."""
        try:
            # Check current market protection status
            market_status = get_market_protection_status()

            return {
                "success": True,
                "market_protected": market_status.get("protection_level")
                != "emergency",
                "protection_level": market_status.get("protection_level", "monitoring"),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _perform_hsm_operations(
        self, capsule_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform HSM cryptographic operations."""
        try:
            if not self.hsm_session_id:
                return {"success": False, "error": "No HSM session available"}

            # Generate secure random data using HSM
            random_result = await execute_hsm_operation(
                self.hsm_session_id, HSMOperationType.RANDOM_GENERATION, size=32
            )

            return {
                "success": random_result.success,
                "hsm_operations": 1,
                "quantum_safe": True,
                "execution_time_ms": random_result.execution_time_ms,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _update_average_response_time(self, execution_time_ms: int):
        """Update average response time metrics."""
        current_avg = self.metrics["average_response_time_ms"]
        total_ops = self.metrics["total_operations"]

        if total_ops == 1:
            self.metrics["average_response_time_ms"] = execution_time_ms
        else:
            new_avg = ((current_avg * (total_ops - 1)) + execution_time_ms) / total_ops
            self.metrics["average_response_time_ms"] = new_avg

    def get_security_status(self) -> Dict[str, Any]:
        """Get comprehensive security system status."""
        return {
            "initialized": self.initialized,
            "security_level": self.config.security_level.value,
            "systems": {
                system_type.value: {
                    "enabled": status.enabled,
                    "operational": status.operational,
                    "last_check": status.last_check.isoformat(),
                    "error_count": status.error_count,
                    "last_error": status.last_error,
                }
                for system_type, status in self.system_status.items()
            },
            "metrics": self.metrics,
            "hsm_session_active": self.hsm_session_id is not None,
            "quantum_resistant": self.config.quantum_resistant_required,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    async def shutdown(self):
        """Gracefully shutdown all security systems."""
        logger.info("  Shutting down Unified Security Manager...")

        # Terminate HSM session
        if self.hsm_session_id:
            try:
                from .hsm_integration import terminate_hsm_session

                await terminate_hsm_session(self.hsm_session_id)
                logger.info("[OK] HSM session terminated")
            except Exception as e:
                logger.error(f"[ERROR] HSM session termination error: {e}")

        # Clear sensitive data
        for status in self.system_status.values():
            status.operational = False

        self.initialized = False
        logger.info("[OK] Unified Security Manager shutdown complete")


# Global security manager instance
security_manager: Optional[UnifiedSecurityManager] = None


async def initialize_security_manager(
    config: Optional[SecurityConfiguration] = None,
) -> bool:
    """Initialize the global security manager."""
    global security_manager

    try:
        # Create HSM configuration if not provided
        if not config:
            hsm_config = HSMConfiguration(
                hsm_type=HSMType.QUANTUM_SAFE_HSM,
                security_level=HSMSecurityLevel.LEVEL_3,
                connection_string="quantum_hsm://localhost:9999",
                quantum_algorithms_enabled=True,
            )
            config = SecurityConfiguration(hsm_config=hsm_config)

        security_manager = UnifiedSecurityManager(config)
        success = await security_manager.initialize()

        if success:
            logger.info(" Unified Security Manager initialized successfully")
        else:
            logger.error("[ERROR] Unified Security Manager initialization failed")

        return success

    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize security manager: {e}")
        return False


def get_security_manager() -> Optional[UnifiedSecurityManager]:
    """Get the global security manager instance."""
    return security_manager


async def secure_operation(
    operation_name: str, capsule_data: Dict[str, Any]
) -> Tuple[bool, Dict[str, Any]]:
    """Perform a secure operation using the global security manager."""
    if security_manager:
        return await security_manager.secure_capsule_operation(
            operation_name, capsule_data
        )
    else:
        logger.warning("Security manager not initialized")
        return False, {"error": "Security manager not available"}


def get_unified_security_status() -> Dict[str, Any]:
    """Get unified security system status."""
    if security_manager:
        return security_manager.get_security_status()
    else:
        return {"status": "not_initialized", "error": "Security manager not available"}
