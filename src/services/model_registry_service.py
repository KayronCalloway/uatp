"""
Model Registry Service for UATP 7.2 Training Provenance

This service handles:
- Model registration with provenance metadata
- Training session tracking
- Model lineage queries
- License verification integration
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.capsule_schema import (
    CapsuleStatus,
    DatasetReference,
    ModelRegistrationCapsule,
    ModelRegistrationPayload,
    TrainingProvenanceCapsule,
    TrainingProvenancePayload,
    Verification,
)
from src.models.model_registry import ModelRegistryModel
from src.models.training_session import SessionStatus, SessionType, TrainingSessionModel

logger = logging.getLogger(__name__)


class ModelRegistryService:
    """Service for UATP 7.2 model registration and training provenance."""

    def __init__(self, session_factory=None):
        """
        Initialize the model registry service.

        Args:
            session_factory: SQLAlchemy session factory for database access
        """
        self.session_factory = session_factory

    async def register_model(
        self,
        model_id: str,
        model_hash: str,
        model_type: str,
        version: str,
        session: AsyncSession,
        name: Optional[str] = None,
        description: Optional[str] = None,
        base_model_id: Optional[str] = None,
        training_config: Optional[Dict[str, Any]] = None,
        dataset_provenance: Optional[List[Dict[str, Any]]] = None,
        license_info: Optional[Dict[str, Any]] = None,
        capabilities: Optional[List[str]] = None,
        safety_evaluations: Optional[Dict[str, Any]] = None,
        owner_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register a new model with provenance metadata.

        Args:
            model_id: Unique identifier for the model
            model_hash: SHA-256 hash of model weights
            model_type: Type (base, fine_tune, adapter, merged)
            version: Model version string
            session: Database session
            name: Human-readable model name
            description: Model description
            base_model_id: Parent model ID for lineage
            training_config: Training configuration
            dataset_provenance: List of dataset references
            license_info: License information
            capabilities: Declared model capabilities
            safety_evaluations: Safety benchmark results
            owner_id: Owner user ID

        Returns:
            Dict with registration result
        """
        try:
            # Validate model_type
            valid_types = {"base", "fine_tune", "adapter", "merged", "distilled"}
            if model_type not in valid_types:
                return {
                    "success": False,
                    "error": f"Invalid model_type. Must be one of: {valid_types}",
                }

            # Check if model already exists
            existing = await session.execute(
                select(ModelRegistryModel).where(
                    ModelRegistryModel.model_id == model_id
                )
            )
            if existing.scalar_one_or_none():
                return {
                    "success": False,
                    "error": f"Model {model_id} already registered",
                }

            # Validate base_model_id exists if provided
            if base_model_id:
                base_model = await session.execute(
                    select(ModelRegistryModel).where(
                        ModelRegistryModel.model_id == base_model_id
                    )
                )
                if not base_model.scalar_one_or_none():
                    return {
                        "success": False,
                        "error": f"Base model {base_model_id} not found",
                    }

            # Create model registry entry
            model = ModelRegistryModel(
                model_id=model_id,
                model_hash=model_hash,
                model_type=model_type,
                version=version,
                name=name,
                description=description,
                base_model_id=base_model_id,
                training_config=training_config,
                dataset_provenance=dataset_provenance,
                license_info=license_info,
                capabilities={"list": capabilities} if capabilities else None,
                safety_evaluations=safety_evaluations,
                owner_id=owner_id,
            )

            session.add(model)
            await session.commit()

            logger.info(f"Registered model {model_id} (type: {model_type})")

            return {
                "success": True,
                "model_id": model_id,
                "model_hash": model_hash,
                "model_type": model_type,
                "version": version,
                "has_base_model": base_model_id is not None,
            }

        except (ValueError, TypeError) as e:
            # Input validation errors
            logger.warning(f"Invalid input for model {model_id}: {e}")
            await session.rollback()
            return {"success": False, "error": f"Invalid input: {e}"}
        except Exception as e:
            # Database errors and unexpected issues
            # SECURITY: Log the full error for debugging but return a generic message
            # to avoid leaking internal details
            from sqlalchemy.exc import IntegrityError, SQLAlchemyError

            if isinstance(e, IntegrityError):
                logger.error(f"Database integrity error for model {model_id}: {e}")
                await session.rollback()
                return {"success": False, "error": "Database constraint violation"}
            elif isinstance(e, SQLAlchemyError):
                logger.error(f"Database error for model {model_id}: {e}")
                await session.rollback()
                return {"success": False, "error": "Database error occurred"}
            else:
                logger.error(f"Unexpected error registering model {model_id}: {e}")
                await session.rollback()
                return {"success": False, "error": "An unexpected error occurred"}

    async def get_model(
        self, model_id: str, session: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        Get model details by ID.

        Args:
            model_id: Model identifier
            session: Database session

        Returns:
            Model dict or None if not found
        """
        result = await session.execute(
            select(ModelRegistryModel).where(ModelRegistryModel.model_id == model_id)
        )
        model = result.scalar_one_or_none()

        if model:
            return model.to_dict()
        return None

    async def get_model_lineage(
        self, model_id: str, session: AsyncSession, max_depth: int = 10
    ) -> Dict[str, Any]:
        """
        Get the lineage tree for a model.

        Args:
            model_id: Starting model identifier
            session: Database session
            max_depth: Maximum depth to traverse

        Returns:
            Lineage tree with ancestors and descendants
        """
        # Get the starting model
        result = await session.execute(
            select(ModelRegistryModel).where(ModelRegistryModel.model_id == model_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            return {"error": f"Model {model_id} not found"}

        # Build ancestor chain
        ancestors = []
        current_model = model
        depth = 0

        while current_model.base_model_id and depth < max_depth:
            ancestor_result = await session.execute(
                select(ModelRegistryModel).where(
                    ModelRegistryModel.model_id == current_model.base_model_id
                )
            )
            ancestor = ancestor_result.scalar_one_or_none()
            if ancestor:
                ancestors.append(
                    {
                        "model_id": ancestor.model_id,
                        "model_type": ancestor.model_type,
                        "version": ancestor.version,
                        "depth": depth + 1,
                    }
                )
                current_model = ancestor
                depth += 1
            else:
                break

        # Get descendants (models that have this as base)
        descendants_result = await session.execute(
            select(ModelRegistryModel).where(
                ModelRegistryModel.base_model_id == model_id
            )
        )
        descendants = [
            {
                "model_id": d.model_id,
                "model_type": d.model_type,
                "version": d.version,
            }
            for d in descendants_result.scalars().all()
        ]

        return {
            "model_id": model_id,
            "model_type": model.model_type,
            "version": model.version,
            "ancestors": ancestors,
            "descendants": descendants,
            "lineage_depth": len(ancestors),
            "root_model": ancestors[-1]["model_id"] if ancestors else model_id,
        }

    async def create_training_session(
        self,
        model_id: str,
        session_type: str,
        dataset_refs: List[Dict[str, Any]],
        session: AsyncSession,
        hyperparameters: Optional[Dict[str, Any]] = None,
        compute_resources: Optional[Dict[str, Any]] = None,
        owner_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new training session.

        Args:
            model_id: Model being trained
            session_type: Type of training (fine_tuning, rlhf, etc.)
            dataset_refs: List of dataset references
            session: Database session
            hyperparameters: Training hyperparameters
            compute_resources: GPU/TPU configuration
            owner_id: Owner user ID

        Returns:
            Dict with session creation result
        """
        try:
            # Validate model exists
            model_result = await session.execute(
                select(ModelRegistryModel).where(
                    ModelRegistryModel.model_id == model_id
                )
            )
            if not model_result.scalar_one_or_none():
                return {"success": False, "error": f"Model {model_id} not found"}

            # Validate session_type
            valid_types = {t.value for t in SessionType}
            if session_type not in valid_types:
                return {
                    "success": False,
                    "error": f"Invalid session_type. Must be one of: {valid_types}",
                }

            # Generate session ID
            session_id = f"train_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{uuid.uuid4().hex[:12]}"

            # Create training session
            training_session = TrainingSessionModel(
                session_id=session_id,
                model_id=model_id,
                session_type=session_type,
                status=SessionStatus.RUNNING.value,
                dataset_refs=dataset_refs,
                hyperparameters=hyperparameters,
                compute_resources=compute_resources,
                started_at=datetime.now(timezone.utc),
                owner_id=owner_id,
            )

            session.add(training_session)
            await session.commit()

            logger.info(f"Created training session {session_id} for model {model_id}")

            return {
                "success": True,
                "session_id": session_id,
                "model_id": model_id,
                "session_type": session_type,
                "status": "running",
            }

        except (ValueError, TypeError) as e:
            # Input validation errors
            logger.warning(f"Invalid input for training session: {e}")
            await session.rollback()
            return {"success": False, "error": f"Invalid input: {e}"}
        except Exception as e:
            # Database errors and unexpected issues
            from sqlalchemy.exc import IntegrityError, SQLAlchemyError

            if isinstance(e, IntegrityError):
                logger.error(f"Database integrity error creating training session: {e}")
                await session.rollback()
                return {"success": False, "error": "Database constraint violation"}
            elif isinstance(e, SQLAlchemyError):
                logger.error(f"Database error creating training session: {e}")
                await session.rollback()
                return {"success": False, "error": "Database error occurred"}
            else:
                logger.error(f"Unexpected error creating training session: {e}")
                await session.rollback()
                return {"success": False, "error": "An unexpected error occurred"}

    async def complete_training_session(
        self,
        session_id: str,
        session: AsyncSession,
        status: str = "completed",
        metrics: Optional[Dict[str, Any]] = None,
        checkpoints: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Mark a training session as complete.

        Args:
            session_id: Training session ID
            session: Database session
            status: Final status (completed, failed, cancelled)
            metrics: Training metrics and evaluation results
            checkpoints: List of checkpoint references

        Returns:
            Dict with completion result
        """
        try:
            result = await session.execute(
                select(TrainingSessionModel).where(
                    TrainingSessionModel.session_id == session_id
                )
            )
            training_session = result.scalar_one_or_none()

            if not training_session:
                return {"success": False, "error": f"Session {session_id} not found"}

            # Update session
            training_session.status = status
            training_session.completed_at = datetime.now(timezone.utc)
            if metrics:
                training_session.metrics = metrics
            if checkpoints:
                training_session.checkpoints = checkpoints

            await session.commit()

            duration = training_session.get_duration_seconds()

            logger.info(f"Completed training session {session_id} with status {status}")

            return {
                "success": True,
                "session_id": session_id,
                "status": status,
                "duration_seconds": duration,
                "has_metrics": metrics is not None,
            }

        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid input completing training session: {e}")
            await session.rollback()
            return {"success": False, "error": f"Invalid input: {e}"}
        except Exception as e:
            from sqlalchemy.exc import IntegrityError, SQLAlchemyError

            if isinstance(e, IntegrityError):
                logger.error(
                    f"Database integrity error completing training session: {e}"
                )
                await session.rollback()
                return {"success": False, "error": "Database constraint violation"}
            elif isinstance(e, SQLAlchemyError):
                logger.error(f"Database error completing training session: {e}")
                await session.rollback()
                return {"success": False, "error": "Database error occurred"}
            else:
                logger.error(f"Unexpected error completing training session: {e}")
                await session.rollback()
                return {"success": False, "error": "An unexpected error occurred"}

    async def get_training_session(
        self, session_id: str, session: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        Get training session details.

        Args:
            session_id: Training session ID
            session: Database session

        Returns:
            Session dict or None if not found
        """
        result = await session.execute(
            select(TrainingSessionModel).where(
                TrainingSessionModel.session_id == session_id
            )
        )
        training_session = result.scalar_one_or_none()

        if training_session:
            return training_session.to_dict()
        return None

    async def list_model_sessions(
        self, model_id: str, session: AsyncSession, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List training sessions for a model.

        Args:
            model_id: Model identifier
            session: Database session
            limit: Maximum number of sessions to return

        Returns:
            List of session dicts
        """
        result = await session.execute(
            select(TrainingSessionModel)
            .where(TrainingSessionModel.model_id == model_id)
            .order_by(TrainingSessionModel.started_at.desc())
            .limit(limit)
        )
        sessions = result.scalars().all()
        return [s.to_dict() for s in sessions]

    def create_model_registration_capsule(
        self,
        model_id: str,
        model_hash: str,
        model_type: str,
        version: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        base_model_id: Optional[str] = None,
        training_config: Optional[Dict[str, Any]] = None,
        dataset_provenance: Optional[List[Dict[str, Any]]] = None,
        license_info: Optional[Dict[str, Any]] = None,
        capabilities: Optional[List[str]] = None,
        safety_evaluations: Optional[Dict[str, Any]] = None,
    ) -> ModelRegistrationCapsule:
        """
        Create a UATP capsule for model registration.

        Args:
            All model registration parameters

        Returns:
            ModelRegistrationCapsule instance
        """
        # Convert dataset_provenance to DatasetReference list
        dataset_refs = None
        if dataset_provenance:
            dataset_refs = [
                DatasetReference(**ds) if isinstance(ds, dict) else ds
                for ds in dataset_provenance
            ]

        payload = ModelRegistrationPayload(
            model_id=model_id,
            model_hash=model_hash,
            model_type=model_type,
            version=version,
            name=name,
            description=description,
            base_model_id=base_model_id,
            training_config=training_config,
            dataset_provenance=dataset_refs,
            license_info=license_info,
            capabilities=capabilities,
            safety_evaluations=safety_evaluations,
        )

        capsule_id = f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

        return ModelRegistrationCapsule(
            capsule_id=capsule_id,
            version="7.2",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.DRAFT,
            verification=Verification(
                signature=f"ed25519:{'0' * 128}",
                merkle_root=f"sha256:{'0' * 64}",
            ),
            model_registration=payload,
        )

    def create_training_provenance_capsule(
        self,
        session_id: str,
        model_id: str,
        session_type: str,
        dataset_refs: List[Dict[str, Any]],
        started_at: datetime,
        completed_at: Optional[datetime] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        compute_resources: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        status: str = "completed",
    ) -> TrainingProvenanceCapsule:
        """
        Create a UATP capsule for training provenance.

        Args:
            All training session parameters

        Returns:
            TrainingProvenanceCapsule instance
        """
        # Convert dataset_refs to DatasetReference list
        ds_refs = [
            DatasetReference(**ds) if isinstance(ds, dict) else ds
            for ds in dataset_refs
        ]

        payload = TrainingProvenancePayload(
            session_id=session_id,
            model_id=model_id,
            session_type=session_type,
            dataset_refs=ds_refs,
            hyperparameters=hyperparameters,
            compute_resources=compute_resources,
            started_at=started_at,
            completed_at=completed_at,
            metrics=metrics,
            status=status,
        )

        capsule_id = f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

        return TrainingProvenanceCapsule(
            capsule_id=capsule_id,
            version="7.2",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.DRAFT,
            verification=Verification(
                signature=f"ed25519:{'0' * 128}",
                merkle_root=f"sha256:{'0' * 64}",
            ),
            training_provenance=payload,
        )


# Global service instance
model_registry_service = ModelRegistryService()
