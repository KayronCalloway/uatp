"""
ANE Training Service for UATP 7.3 ANE Training Provenance

This service handles:
- Hardware profile registration
- ANE training session management
- Kernel execution tracking
- Compile artifact management
- Session statistics aggregation
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.capsule_schema import (
    ANETrainingSessionCapsule,
    ANETrainingSessionPayload,
    CapsuleStatus,
    CompileArtifactCapsule,
    CompileArtifactPayload,
    DatasetReference,
    HardwareProfileCapsule,
    HardwareProfilePayload,
    HybridComputeAttribution,
    KernelExecutionCapsule,
    KernelExecutionPayload,
    MILFusionOptimization,
    Verification,
)
from src.models.ane_training_session import (
    ANESessionStatus,
    ANETrainingSessionModel,
    CompileArtifactModel,
    HardwareProfileModel,
    KernelExecutionModel,
    KernelType,
)

logger = logging.getLogger(__name__)


class ANETrainingService:
    """Service for UATP 7.3 ANE training provenance."""

    def __init__(self, session_factory=None):
        """
        Initialize the ANE training service.

        Args:
            session_factory: SQLAlchemy session factory for database access
        """
        self.session_factory = session_factory

    # --- Hardware Profile Methods ---

    async def register_hardware_profile(
        self,
        device_class: str,
        chip_identifier: str,
        device_id_hash: str,
        session: AsyncSession,
        chip_variant: Optional[str] = None,
        ane_available: bool = True,
        ane_version: Optional[str] = None,
        ane_tops: Optional[float] = None,
        ane_compile_limit: Optional[int] = None,
        memory_bandwidth_gbps: Optional[float] = None,
        unified_memory_gb: Optional[float] = None,
        private_apis_used: Optional[List[str]] = None,
        os_version: Optional[str] = None,
        coreml_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register a hardware profile with ANE capabilities.

        Args:
            device_class: Device class (mac, iphone, ipad)
            chip_identifier: Chip identifier (M1, M2, M3, M4, A17)
            device_id_hash: SHA-256 hash of device ID
            session: Database session
            ... additional parameters

        Returns:
            Dict with registration result
        """
        try:
            # Validate device_class
            valid_classes = {"mac", "iphone", "ipad"}
            if device_class not in valid_classes:
                return {
                    "success": False,
                    "error": f"Invalid device_class. Must be one of: {valid_classes}",
                }

            # Check for existing profile with same device_id_hash
            existing = await session.execute(
                select(HardwareProfileModel).where(
                    HardwareProfileModel.device_id_hash == device_id_hash
                )
            )
            existing_profile = existing.scalar_one_or_none()
            if existing_profile:
                # Return existing profile instead of creating duplicate
                return {
                    "success": True,
                    "profile_id": existing_profile.profile_id,
                    "chip_identifier": existing_profile.chip_identifier,
                    "existing": True,
                }

            # Generate profile ID
            profile_id = f"hw_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{uuid.uuid4().hex[:12]}"

            # Create profile
            profile = HardwareProfileModel(
                profile_id=profile_id,
                device_class=device_class,
                chip_identifier=chip_identifier,
                chip_variant=chip_variant,
                device_id_hash=device_id_hash,
                ane_available=ane_available,
                ane_version=ane_version,
                ane_tops=ane_tops,
                ane_compile_limit=ane_compile_limit,
                memory_bandwidth_gbps=memory_bandwidth_gbps,
                unified_memory_gb=unified_memory_gb,
                private_apis_used=private_apis_used or [],
                os_version=os_version,
                coreml_version=coreml_version,
            )

            session.add(profile)
            await session.commit()

            logger.info(f"Registered hardware profile {profile_id} for {chip_identifier}")

            return {
                "success": True,
                "profile_id": profile_id,
                "chip_identifier": chip_identifier,
                "ane_available": ane_available,
                "existing": False,
            }

        except Exception as e:
            logger.error(f"Error registering hardware profile: {e}")
            await session.rollback()
            return {"success": False, "error": "Failed to register hardware profile"}

    async def get_hardware_profile(
        self, profile_id: str, session: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """Get hardware profile by ID."""
        result = await session.execute(
            select(HardwareProfileModel).where(
                HardwareProfileModel.profile_id == profile_id
            )
        )
        profile = result.scalar_one_or_none()
        if profile:
            return profile.to_dict()
        return None

    async def get_profile_stats(self, session: AsyncSession) -> Dict[str, Any]:
        """Get aggregate statistics for hardware profiles."""
        # Count by chip
        chip_query = select(
            HardwareProfileModel.chip_identifier,
            func.count(HardwareProfileModel.id)
        ).group_by(HardwareProfileModel.chip_identifier)
        chip_result = await session.execute(chip_query)
        by_chip = {row[0]: row[1] for row in chip_result.fetchall()}

        # Count by device class
        class_query = select(
            HardwareProfileModel.device_class,
            func.count(HardwareProfileModel.id)
        ).group_by(HardwareProfileModel.device_class)
        class_result = await session.execute(class_query)
        by_class = {row[0]: row[1] for row in class_result.fetchall()}

        # Total
        total_result = await session.execute(
            select(func.count(HardwareProfileModel.id))
        )
        total = total_result.scalar() or 0

        return {
            "total": total,
            "by_chip": by_chip,
            "by_device_class": by_class,
        }

    # --- ANE Training Session Methods ---

    async def create_ane_session(
        self,
        model_id: str,
        hardware_profile_id: str,
        session: AsyncSession,
        model_name: Optional[str] = None,
        total_steps: Optional[int] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        dataset_refs: Optional[List[Dict[str, Any]]] = None,
        private_apis_used: Optional[List[str]] = None,
        dmca_1201f_claim: bool = False,
        research_purpose: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new ANE training session."""
        try:
            # Validate hardware profile exists
            profile_result = await session.execute(
                select(HardwareProfileModel).where(
                    HardwareProfileModel.profile_id == hardware_profile_id
                )
            )
            if not profile_result.scalar_one_or_none():
                return {
                    "success": False,
                    "error": f"Hardware profile {hardware_profile_id} not found",
                }

            # Generate session ID
            session_id = f"ane_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{uuid.uuid4().hex[:12]}"

            # Create session
            ane_session = ANETrainingSessionModel(
                session_id=session_id,
                model_id=model_id,
                model_name=model_name,
                hardware_profile_id=hardware_profile_id,
                status=ANESessionStatus.RUNNING.value,
                total_steps=total_steps,
                hyperparameters=hyperparameters,
                dataset_refs=dataset_refs,
                private_apis_used=private_apis_used or [],
                dmca_1201f_claim=dmca_1201f_claim,
                research_purpose=research_purpose,
                started_at=datetime.now(timezone.utc),
                owner_id=owner_id,
            )

            session.add(ane_session)
            await session.commit()

            logger.info(f"Created ANE session {session_id} for model {model_id}")

            return {
                "success": True,
                "session_id": session_id,
                "model_id": model_id,
                "hardware_profile_id": hardware_profile_id,
                "status": "running",
            }

        except Exception as e:
            logger.error(f"Error creating ANE session: {e}")
            await session.rollback()
            return {"success": False, "error": "Failed to create ANE session"}

    async def get_ane_session(
        self, session_id: str, session: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """Get ANE training session by ID."""
        result = await session.execute(
            select(ANETrainingSessionModel).where(
                ANETrainingSessionModel.session_id == session_id
            )
        )
        ane_session = result.scalar_one_or_none()
        if ane_session:
            return ane_session.to_dict()
        return None

    async def complete_ane_session(
        self,
        session_id: str,
        session: AsyncSession,
        status: str = "completed",
        final_loss: Optional[float] = None,
        avg_ms_per_step: Optional[float] = None,
        avg_ane_utilization: Optional[float] = None,
        total_ane_time_seconds: Optional[float] = None,
        total_cpu_time_seconds: Optional[float] = None,
        session_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Mark an ANE training session as complete."""
        try:
            result = await session.execute(
                select(ANETrainingSessionModel).where(
                    ANETrainingSessionModel.session_id == session_id
                )
            )
            ane_session = result.scalar_one_or_none()

            if not ane_session:
                return {"success": False, "error": f"Session {session_id} not found"}

            # Update session
            ane_session.status = status
            ane_session.completed_at = datetime.now(timezone.utc)
            if final_loss is not None:
                ane_session.final_loss = final_loss
            if avg_ms_per_step is not None:
                ane_session.avg_ms_per_step = avg_ms_per_step
            if avg_ane_utilization is not None:
                ane_session.avg_ane_utilization = avg_ane_utilization
            if total_ane_time_seconds is not None:
                ane_session.total_ane_time_seconds = total_ane_time_seconds
            if total_cpu_time_seconds is not None:
                ane_session.total_cpu_time_seconds = total_cpu_time_seconds
            if session_metadata:
                ane_session.session_metadata = session_metadata

            await session.commit()

            duration = ane_session.get_duration_seconds()

            logger.info(f"Completed ANE session {session_id} with status {status}")

            return {
                "success": True,
                "session_id": session_id,
                "status": status,
                "duration_seconds": duration,
                "final_loss": final_loss,
            }

        except Exception as e:
            logger.error(f"Error completing ANE session: {e}")
            await session.rollback()
            return {"success": False, "error": "Failed to complete ANE session"}

    async def get_session_stats(self, session: AsyncSession) -> Dict[str, Any]:
        """Get aggregate statistics for ANE training sessions."""
        # Count by status
        status_query = select(
            ANETrainingSessionModel.status,
            func.count(ANETrainingSessionModel.id)
        ).group_by(ANETrainingSessionModel.status)
        status_result = await session.execute(status_query)
        by_status = {row[0]: row[1] for row in status_result.fetchall()}

        # Total
        total_result = await session.execute(
            select(func.count(ANETrainingSessionModel.id))
        )
        total = total_result.scalar() or 0

        # Average metrics for completed sessions
        avg_query = select(
            func.avg(ANETrainingSessionModel.avg_ms_per_step),
            func.avg(ANETrainingSessionModel.avg_ane_utilization),
        ).where(ANETrainingSessionModel.status == "completed")
        avg_result = await session.execute(avg_query)
        avg_row = avg_result.fetchone()

        return {
            "total": total,
            "by_status": by_status,
            "avg_ms_per_step": float(avg_row[0]) if avg_row and avg_row[0] else None,
            "avg_ane_utilization": float(avg_row[1]) if avg_row and avg_row[1] else None,
        }

    async def get_session_statistics(
        self, session_id: str, session: AsyncSession
    ) -> Dict[str, Any]:
        """Get aggregate kernel statistics for a session."""
        # Verify session exists
        ane_session_result = await session.execute(
            select(ANETrainingSessionModel).where(
                ANETrainingSessionModel.session_id == session_id
            )
        )
        if not ane_session_result.scalar_one_or_none():
            return {"error": f"Session {session_id} not found"}

        # Count by kernel type
        type_query = select(
            KernelExecutionModel.kernel_type,
            func.count(KernelExecutionModel.id),
            func.avg(KernelExecutionModel.execution_time_us),
        ).where(
            KernelExecutionModel.session_id == session_id
        ).group_by(KernelExecutionModel.kernel_type)

        type_result = await session.execute(type_query)
        by_kernel_type = {}
        for row in type_result.fetchall():
            by_kernel_type[row[0]] = {
                "count": row[1],
                "avg_execution_time_us": float(row[2]) if row[2] else 0,
            }

        # Total execution time
        total_query = select(
            func.count(KernelExecutionModel.id),
            func.sum(KernelExecutionModel.execution_time_us),
        ).where(KernelExecutionModel.session_id == session_id)

        total_result = await session.execute(total_query)
        total_row = total_result.fetchone()

        return {
            "session_id": session_id,
            "total_kernel_executions": total_row[0] if total_row else 0,
            "total_execution_time_us": int(total_row[1]) if total_row and total_row[1] else 0,
            "by_kernel_type": by_kernel_type,
        }

    # --- Kernel Execution Methods ---

    async def record_kernel_execution(
        self,
        session_id: str,
        kernel_type: str,
        step_index: int,
        dispatch_index: int,
        execution_time_us: int,
        session: AsyncSession,
        iosurface_format: Optional[str] = None,
        input_shape: Optional[List[int]] = None,
        output_shape: Optional[List[int]] = None,
        compute_attribution: Optional[Dict[str, Any]] = None,
        ane_program_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record a single kernel execution."""
        try:
            # Validate session exists
            ane_session_result = await session.execute(
                select(ANETrainingSessionModel).where(
                    ANETrainingSessionModel.session_id == session_id
                )
            )
            ane_session = ane_session_result.scalar_one_or_none()
            if not ane_session:
                return {"success": False, "error": f"Session {session_id} not found"}

            # Generate execution ID
            execution_id = f"kern_{uuid.uuid4().hex[:16]}"

            # Create execution record
            execution = KernelExecutionModel(
                execution_id=execution_id,
                session_id=session_id,
                kernel_type=kernel_type,
                step_index=step_index,
                dispatch_index=dispatch_index,
                execution_time_us=execution_time_us,
                iosurface_format=iosurface_format,
                input_shape=input_shape,
                output_shape=output_shape,
                compute_attribution=compute_attribution,
                ane_program_hash=ane_program_hash,
            )

            session.add(execution)

            # Update session kernel count
            ane_session.kernel_execution_count += 1
            ane_session.completed_steps = max(ane_session.completed_steps, step_index + 1)

            await session.commit()

            return {
                "success": True,
                "execution_id": execution_id,
                "session_id": session_id,
                "kernel_type": kernel_type,
            }

        except Exception as e:
            logger.error(f"Error recording kernel execution: {e}")
            await session.rollback()
            return {"success": False, "error": "Failed to record kernel execution"}

    async def batch_record_kernel_executions(
        self,
        executions: List[Dict[str, Any]],
        session: AsyncSession,
    ) -> Dict[str, Any]:
        """Record a batch of kernel executions (optimized for 6 per step)."""
        try:
            if not executions:
                return {"success": False, "error": "No executions provided"}

            session_id = executions[0]["session_id"]

            # Validate session exists
            ane_session_result = await session.execute(
                select(ANETrainingSessionModel).where(
                    ANETrainingSessionModel.session_id == session_id
                )
            )
            ane_session = ane_session_result.scalar_one_or_none()
            if not ane_session:
                return {"success": False, "error": f"Session {session_id} not found"}

            execution_ids = []
            max_step = 0

            for exec_data in executions:
                execution_id = f"kern_{uuid.uuid4().hex[:16]}"
                execution = KernelExecutionModel(
                    execution_id=execution_id,
                    session_id=exec_data["session_id"],
                    kernel_type=exec_data["kernel_type"],
                    step_index=exec_data["step_index"],
                    dispatch_index=exec_data["dispatch_index"],
                    execution_time_us=exec_data["execution_time_us"],
                    iosurface_format=exec_data.get("iosurface_format"),
                    input_shape=exec_data.get("input_shape"),
                    output_shape=exec_data.get("output_shape"),
                    compute_attribution=exec_data.get("compute_attribution"),
                    ane_program_hash=exec_data.get("ane_program_hash"),
                )
                session.add(execution)
                execution_ids.append(execution_id)
                max_step = max(max_step, exec_data["step_index"])

            # Update session
            ane_session.kernel_execution_count += len(executions)
            ane_session.completed_steps = max(ane_session.completed_steps, max_step + 1)

            await session.commit()

            return {
                "success": True,
                "execution_ids": execution_ids,
                "count": len(executions),
                "session_id": session_id,
            }

        except Exception as e:
            logger.error(f"Error batch recording kernel executions: {e}")
            await session.rollback()
            return {"success": False, "error": "Failed to batch record kernel executions"}

    async def list_kernel_executions(
        self,
        session_id: str,
        session: AsyncSession,
        step_index: Optional[int] = None,
        kernel_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List kernel executions for a session."""
        query = select(KernelExecutionModel).where(
            KernelExecutionModel.session_id == session_id
        )

        if step_index is not None:
            query = query.where(KernelExecutionModel.step_index == step_index)
        if kernel_type:
            query = query.where(KernelExecutionModel.kernel_type == kernel_type)

        query = query.order_by(
            KernelExecutionModel.step_index,
            KernelExecutionModel.dispatch_index
        ).offset(offset).limit(limit)

        result = await session.execute(query)
        return [e.to_dict() for e in result.scalars().all()]

    # --- Compile Artifact Methods ---

    async def record_compile_artifact(
        self,
        session_id: str,
        mil_program_hash: str,
        session: AsyncSession,
        weight_blob_hash: Optional[str] = None,
        compiled_model_hash: Optional[str] = None,
        fusion_optimizations: Optional[List[Dict[str, Any]]] = None,
        compile_time_ms: Optional[int] = None,
        target_device: Optional[str] = None,
        coreml_spec_version: Optional[int] = None,
        mlmodel_size_bytes: Optional[int] = None,
        storage_uri: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record a MIL compile artifact."""
        try:
            # Validate session exists
            ane_session_result = await session.execute(
                select(ANETrainingSessionModel).where(
                    ANETrainingSessionModel.session_id == session_id
                )
            )
            ane_session = ane_session_result.scalar_one_or_none()
            if not ane_session:
                return {"success": False, "error": f"Session {session_id} not found"}

            # Generate artifact ID
            artifact_id = f"art_{uuid.uuid4().hex[:16]}"

            # Create artifact
            artifact = CompileArtifactModel(
                artifact_id=artifact_id,
                session_id=session_id,
                mil_program_hash=mil_program_hash,
                weight_blob_hash=weight_blob_hash,
                compiled_model_hash=compiled_model_hash,
                fusion_optimizations=fusion_optimizations or [],
                compile_time_ms=compile_time_ms,
                target_device=target_device,
                coreml_spec_version=coreml_spec_version,
                mlmodel_size_bytes=mlmodel_size_bytes,
                storage_uri=storage_uri,
            )

            session.add(artifact)

            # Update session's compile artifact list
            current_artifacts = ane_session.compile_artifact_ids or []
            current_artifacts.append(artifact_id)
            ane_session.compile_artifact_ids = current_artifacts

            await session.commit()

            logger.info(f"Recorded compile artifact {artifact_id}")

            return {
                "success": True,
                "artifact_id": artifact_id,
                "session_id": session_id,
                "mil_program_hash": mil_program_hash,
            }

        except Exception as e:
            logger.error(f"Error recording compile artifact: {e}")
            await session.rollback()
            return {"success": False, "error": "Failed to record compile artifact"}

    async def list_compile_artifacts(
        self,
        session_id: str,
        session: AsyncSession,
    ) -> List[Dict[str, Any]]:
        """List compile artifacts for a session."""
        result = await session.execute(
            select(CompileArtifactModel)
            .where(CompileArtifactModel.session_id == session_id)
            .order_by(CompileArtifactModel.created_at)
        )
        return [a.to_dict() for a in result.scalars().all()]

    # --- Telemetry Methods ---

    async def record_telemetry_batch(
        self,
        session_id: str,
        measurements: List[Dict[str, Any]],
        session: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Record a batch of telemetry measurements.

        Note: This stores telemetry in the session metadata.
        For production, consider a time-series database.
        """
        try:
            # Validate session exists
            ane_session_result = await session.execute(
                select(ANETrainingSessionModel).where(
                    ANETrainingSessionModel.session_id == session_id
                )
            )
            ane_session = ane_session_result.scalar_one_or_none()
            if not ane_session:
                return {"success": False, "error": f"Session {session_id} not found"}

            # Append to session metadata
            metadata = ane_session.session_metadata or {}
            telemetry = metadata.get("telemetry", [])
            telemetry.extend(measurements)
            metadata["telemetry"] = telemetry[-1000:]  # Keep last 1000
            ane_session.session_metadata = metadata

            await session.commit()

            return {
                "success": True,
                "session_id": session_id,
                "measurements_recorded": len(measurements),
            }

        except Exception as e:
            logger.error(f"Error recording telemetry: {e}")
            await session.rollback()
            return {"success": False, "error": "Failed to record telemetry"}

    # --- Capsule Creation Methods ---

    def create_hardware_profile_capsule(
        self,
        profile_id: str,
        device_class: str,
        chip_identifier: str,
        device_id_hash: str,
        ane_available: bool = True,
        chip_variant: Optional[str] = None,
        ane_version: Optional[str] = None,
        ane_tops: Optional[float] = None,
        ane_compile_limit: Optional[int] = None,
        memory_bandwidth_gbps: Optional[float] = None,
        unified_memory_gb: Optional[float] = None,
        private_apis_used: Optional[List[str]] = None,
        os_version: Optional[str] = None,
        coreml_version: Optional[str] = None,
    ) -> HardwareProfileCapsule:
        """Create a UATP capsule for hardware profile."""
        payload = HardwareProfilePayload(
            device_class=device_class,
            chip_identifier=chip_identifier,
            chip_variant=chip_variant,
            ane_available=ane_available,
            ane_version=ane_version,
            ane_tops=ane_tops,
            ane_compile_limit=ane_compile_limit,
            memory_bandwidth_gbps=memory_bandwidth_gbps,
            unified_memory_gb=unified_memory_gb,
            private_apis_used=private_apis_used or [],
            device_id_hash=device_id_hash,
            os_version=os_version,
            coreml_version=coreml_version,
        )

        capsule_id = f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

        return HardwareProfileCapsule(
            capsule_id=capsule_id,
            version="7.3",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.DRAFT,
            verification=Verification(
                signature=f"ed25519:{'0' * 128}",
                merkle_root=f"sha256:{'0' * 64}",
            ),
            hardware_profile=payload,
        )

    def create_kernel_execution_capsule(
        self,
        session_id: str,
        kernel_type: str,
        step_index: int,
        dispatch_index: int,
        execution_time_us: int,
        iosurface_format: Optional[str] = None,
        input_shape: Optional[List[int]] = None,
        output_shape: Optional[List[int]] = None,
        compute_attribution: Optional[Dict[str, Any]] = None,
        ane_program_hash: Optional[str] = None,
    ) -> KernelExecutionCapsule:
        """Create a UATP capsule for kernel execution."""
        hybrid_attr = None
        if compute_attribution:
            hybrid_attr = HybridComputeAttribution(**compute_attribution)

        payload = KernelExecutionPayload(
            session_id=session_id,
            kernel_type=kernel_type,
            step_index=step_index,
            dispatch_index=dispatch_index,
            execution_time_us=execution_time_us,
            iosurface_format=iosurface_format,
            input_shape=input_shape,
            output_shape=output_shape,
            compute_attribution=hybrid_attr,
            ane_program_hash=ane_program_hash,
        )

        capsule_id = f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

        return KernelExecutionCapsule(
            capsule_id=capsule_id,
            version="7.3",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.DRAFT,
            verification=Verification(
                signature=f"ed25519:{'0' * 128}",
                merkle_root=f"sha256:{'0' * 64}",
            ),
            kernel_execution=payload,
        )


# Global service instance
ane_training_service = ANETrainingService()
