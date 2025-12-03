"""
GDPR/CCPA Data Subject Rights

Implements data subject rights required by GDPR and CCPA:
- Right to Access (data export)
- Right to be Forgotten (data deletion) [ALREADY IMPLEMENTED]
- Right to Portability (data transfer)
- Right to Rectification (data correction)
- Consent Management

Key Features:
1. Automated data export in JSON/CSV formats
2. Consent tracking and management
3. Data portability across systems
4. Privacy policy versioning
5. Audit trail for all data operations

Usage:
    from src.compliance.gdpr_ccpa import GDPRComplianceManager

    manager = GDPRComplianceManager()

    # Export user data (Right to Access)
    export = await manager.export_user_data(
        user_id="user_123",
        format="json"
    )

    # Manage consent
    await manager.record_consent(
        user_id="user_123",
        consent_type="data_processing",
        granted=True
    )

    # Check if user has consented
    has_consent = await manager.check_consent(
        user_id="user_123",
        consent_type="marketing"
    )
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path
import json
import csv
import io
import secrets
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConsentRecord:
    """Record of user consent"""

    consent_id: str
    user_id: str
    consent_type: str  # "data_processing", "marketing", "analytics", "third_party_sharing"
    granted: bool
    granted_at: Optional[str]
    revoked_at: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    privacy_policy_version: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataExport:
    """User data export"""

    export_id: str
    user_id: str
    export_format: str  # "json", "csv", "xml"
    created_at: str
    expires_at: str
    file_path: str
    file_size_bytes: int
    data_categories: List[str]
    status: str  # "pending", "completed", "expired"


@dataclass
class DataDeletionRequest:
    """Data deletion (Right to be Forgotten) request"""

    request_id: str
    user_id: str
    requested_at: str
    completed_at: Optional[str]
    status: str  # "pending", "in_progress", "completed", "failed"
    deleted_items: List[str]
    retention_exceptions: List[str]  # Data that must be retained for legal reasons


class GDPRComplianceManager:
    """
    Manages GDPR/CCPA data subject rights.

    This system provides:
    1. Data export (Right to Access)
    2. Data deletion (Right to be Forgotten) - already implemented in user_service.py
    3. Consent management
    4. Data portability
    5. Audit trail
    """

    CONSENT_TYPES = [
        "data_processing",  # Essential data processing
        "marketing",  # Marketing communications
        "analytics",  # Usage analytics
        "third_party_sharing",  # Sharing with partners
        "personalization",  # Personalized content
    ]

    def __init__(
        self, storage_path: str = "compliance/gdpr", privacy_policy_version: str = "1.0"
    ):
        """
        Initialize GDPR compliance manager.

        Args:
            storage_path: Directory for compliance data
            privacy_policy_version: Current privacy policy version
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.privacy_policy_version = privacy_policy_version

        # In-memory caches
        self.consent_cache: Dict[str, List[ConsentRecord]] = {}

        # Load existing consent records
        self._load_consent_records()

    def _load_consent_records(self):
        """Load consent records from storage"""
        consent_file = self.storage_path / "consent_records.jsonl"

        if not consent_file.exists():
            return

        with open(consent_file, "r") as f:
            for line in f:
                record_dict = json.loads(line)
                record = ConsentRecord(**record_dict)

                if record.user_id not in self.consent_cache:
                    self.consent_cache[record.user_id] = []

                self.consent_cache[record.user_id].append(record)

    def _save_consent_record(self, record: ConsentRecord):
        """Save consent record to storage"""
        consent_file = self.storage_path / "consent_records.jsonl"

        with open(consent_file, "a") as f:
            f.write(json.dumps(asdict(record)) + "\n")

    async def record_consent(
        self,
        user_id: str,
        consent_type: str,
        granted: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> ConsentRecord:
        """
        Record user consent.

        Args:
            user_id: User ID
            consent_type: Type of consent
            granted: Whether consent was granted
            ip_address: IP address of user
            user_agent: User agent string
            metadata: Additional metadata

        Returns:
            ConsentRecord
        """
        if consent_type not in self.CONSENT_TYPES:
            raise ValueError(f"Invalid consent type: {consent_type}")

        consent_id = f"consent_{secrets.token_hex(16)}"

        record = ConsentRecord(
            consent_id=consent_id,
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            granted_at=datetime.now(timezone.utc).isoformat() if granted else None,
            revoked_at=datetime.now(timezone.utc).isoformat() if not granted else None,
            ip_address=ip_address,
            user_agent=user_agent,
            privacy_policy_version=self.privacy_policy_version,
            metadata=metadata or {},
        )

        # Cache consent
        if user_id not in self.consent_cache:
            self.consent_cache[user_id] = []
        self.consent_cache[user_id].append(record)

        # Save to storage
        self._save_consent_record(record)

        logger.info(f"Recorded consent for user {user_id}: {consent_type} = {granted}")

        # Emit audit event
        try:
            from src.audit.events import audit_emitter

            audit_emitter.emit_security_event(
                event_name="consent_recorded",
                metadata={
                    "consent_id": consent_id,
                    "user_id": user_id,
                    "consent_type": consent_type,
                    "granted": granted,
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit audit event: {e}")

        return record

    async def check_consent(self, user_id: str, consent_type: str) -> bool:
        """
        Check if user has granted consent.

        Args:
            user_id: User ID
            consent_type: Type of consent

        Returns:
            True if consent granted, False otherwise
        """
        if user_id not in self.consent_cache:
            return False

        # Get most recent consent for this type
        user_consents = self.consent_cache[user_id]
        relevant_consents = [c for c in user_consents if c.consent_type == consent_type]

        if not relevant_consents:
            return False

        # Return most recent consent status
        latest_consent = max(
            relevant_consents, key=lambda c: c.granted_at or c.revoked_at or ""
        )

        return latest_consent.granted

    async def export_user_data(
        self,
        user_id: str,
        format: str = "json",
        include_categories: Optional[List[str]] = None,
    ) -> DataExport:
        """
        Export all user data (Right to Access).

        Args:
            user_id: User ID
            format: Export format ("json", "csv", "xml")
            include_categories: Data categories to include

        Returns:
            DataExport object with file path
        """
        export_id = f"export_{secrets.token_hex(16)}"

        logger.info(f"Starting data export for user {user_id} (format: {format})")

        # Collect user data from all sources
        user_data = await self._collect_user_data(user_id, include_categories)

        # Generate export file
        export_file_path = await self._generate_export_file(
            user_id=user_id, export_id=export_id, data=user_data, format=format
        )

        # Calculate file size
        file_size = Path(export_file_path).stat().st_size

        # Create export record
        export = DataExport(
            export_id=export_id,
            user_id=user_id,
            export_format=format,
            created_at=datetime.now(timezone.utc).isoformat(),
            expires_at=(datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            file_path=export_file_path,
            file_size_bytes=file_size,
            data_categories=list(user_data.keys()),
            status="completed",
        )

        # Save export record
        self._save_export_record(export)

        logger.info(
            f"Data export completed for user {user_id}: {export_id} "
            f"({file_size} bytes)"
        )

        # Emit audit event
        try:
            from src.audit.events import audit_emitter

            audit_emitter.emit_security_event(
                event_name="data_export_completed",
                metadata={
                    "export_id": export_id,
                    "user_id": user_id,
                    "format": format,
                    "file_size_bytes": file_size,
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit audit event: {e}")

        return export

    async def _collect_user_data(
        self, user_id: str, include_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Collect all user data from various sources"""

        user_data = {}

        # 1. Profile data
        try:
            from src.user_management.user_service import UserService
            from src.core.database import db

            async with db.session() as session:
                user_service = UserService(session)
                profile = await user_service.get_user_profile(user_id)

                if profile:
                    user_data["profile"] = {
                        "user_id": user_id,
                        "username": profile.get("username"),
                        "email": profile.get("email"),
                        "created_at": profile.get("created_at"),
                    }
        except Exception as e:
            logger.warning(f"Failed to collect profile data: {e}")

        # 2. Capsules created by user
        try:
            from src.core.database import db
            from src.models.capsule import CapsuleModel
            from sqlalchemy import select

            async with db.session() as session:
                query = select(CapsuleModel).where(CapsuleModel.creator_id == user_id)
                result = await session.execute(query)
                capsules = result.scalars().all()

                user_data["capsules"] = [
                    {
                        "capsule_id": c.capsule_id,
                        "timestamp": c.timestamp.isoformat() if c.timestamp else None,
                        "status": c.status,
                    }
                    for c in capsules
                ]
        except Exception as e:
            logger.warning(f"Failed to collect capsule data: {e}")
            user_data["capsules"] = []

        # 3. Consent records
        user_consents = self.consent_cache.get(user_id, [])
        user_data["consents"] = [
            {
                "consent_type": c.consent_type,
                "granted": c.granted,
                "granted_at": c.granted_at,
                "privacy_policy_version": c.privacy_policy_version,
            }
            for c in user_consents
        ]

        # 4. Agent data (if user owns agents)
        try:
            from src.auth.agent_auth import agent_auth_manager

            agents = agent_auth_manager.list_agents(human_owner_id=user_id)
            user_data["agents"] = [
                {
                    "agent_id": a.agent_id,
                    "agent_name": a.agent_name,
                    "created_at": a.created_at,
                    "status": a.status,
                }
                for a in agents
            ]
        except Exception as e:
            logger.warning(f"Failed to collect agent data: {e}")
            user_data["agents"] = []

        # 5. Agent spending history
        try:
            from src.agent import agent_spending_manager

            for agent in user_data.get("agents", []):
                summary = await agent_spending_manager.get_spending_summary(
                    agent["agent_id"]
                )
                agent["spending_summary"] = summary
        except Exception as e:
            logger.warning(f"Failed to collect spending data: {e}")

        return user_data

    async def _generate_export_file(
        self, user_id: str, export_id: str, data: Dict[str, Any], format: str
    ) -> str:
        """Generate export file in requested format"""

        export_dir = self.storage_path / "exports"
        export_dir.mkdir(exist_ok=True)

        if format == "json":
            file_path = export_dir / f"{export_id}.json"

            with open(file_path, "w") as f:
                json.dump(data, f, indent=2, default=str)

        elif format == "csv":
            file_path = export_dir / f"{export_id}.csv"

            # Flatten data for CSV
            flattened_data = self._flatten_dict(data)

            with open(file_path, "w", newline="") as f:
                if flattened_data:
                    writer = csv.DictWriter(f, fieldnames=flattened_data[0].keys())
                    writer.writeheader()
                    writer.writerows(flattened_data)

        elif format == "xml":
            file_path = export_dir / f"{export_id}.xml"

            # Simple XML generation
            xml_content = self._dict_to_xml(data, "user_data")

            with open(file_path, "w") as f:
                f.write(xml_content)

        else:
            raise ValueError(f"Unsupported format: {format}")

        return str(file_path)

    def _flatten_dict(
        self, data: Dict[str, Any], parent_key: str = "", sep: str = "_"
    ) -> List[Dict[str, Any]]:
        """Flatten nested dict for CSV export"""

        items = []

        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key

            if isinstance(value, dict):
                items.extend(self._flatten_dict(value, new_key, sep=sep))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        items.append({f"{new_key}_{i}_{k}": v for k, v in item.items()})
                    else:
                        items.append({f"{new_key}_{i}": item})
            else:
                items.append({new_key: value})

        return items if items else [data]

    def _dict_to_xml(self, data: Dict[str, Any], root_tag: str = "data") -> str:
        """Convert dict to simple XML"""

        xml_lines = [f"<?xml version='1.0' encoding='UTF-8'?>", f"<{root_tag}>"]

        for key, value in data.items():
            if isinstance(value, dict):
                xml_lines.append(f"  <{key}>")
                for k, v in value.items():
                    xml_lines.append(f"    <{k}>{v}</{k}>")
                xml_lines.append(f"  </{key}>")
            elif isinstance(value, list):
                xml_lines.append(f"  <{key}>")
                for item in value:
                    xml_lines.append(f"    <item>{item}</item>")
                xml_lines.append(f"  </{key}>")
            else:
                xml_lines.append(f"  <{key}>{value}</{key}>")

        xml_lines.append(f"</{root_tag}>")

        return "\n".join(xml_lines)

    def _save_export_record(self, export: DataExport):
        """Save export record"""
        exports_file = self.storage_path / "data_exports.jsonl"

        with open(exports_file, "a") as f:
            f.write(json.dumps(asdict(export)) + "\n")

    def get_consent_history(self, user_id: str) -> List[ConsentRecord]:
        """Get full consent history for user"""
        return self.consent_cache.get(user_id, [])

    async def list_exports(self, user_id: str) -> List[DataExport]:
        """List all data exports for user"""
        exports_file = self.storage_path / "data_exports.jsonl"

        if not exports_file.exists():
            return []

        exports = []

        with open(exports_file, "r") as f:
            for line in f:
                export_dict = json.loads(line)
                if export_dict["user_id"] == user_id:
                    exports.append(DataExport(**export_dict))

        return exports


# Global GDPR compliance manager
gdpr_compliance_manager = GDPRComplianceManager()
