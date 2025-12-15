"""
Automated Data Retention Enforcer
GDPR Article 17 compliant automated data deletion and retention management
"""

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class DataCategory(Enum):
    """Data categories for retention policies"""

    PERSONAL_DATA = "personal_data"
    CONVERSATION_DATA = "conversation_data"
    ATTRIBUTION_DATA = "attribution_data"
    FINANCIAL_DATA = "financial_data"
    SYSTEM_LOGS = "system_logs"
    AUDIT_LOGS = "audit_logs"
    BACKUP_DATA = "backup_data"
    CACHE_DATA = "cache_data"
    TEMPORARY_DATA = "temporary_data"
    ANALYTICS_DATA = "analytics_data"


class RetentionReason(Enum):
    """Legal reasons for data retention"""

    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"
    LITIGATION_HOLD = "litigation_hold"
    REGULATORY_REQUIREMENT = "regulatory_requirement"


class DeletionStatus(Enum):
    """Data deletion status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    EXEMPT = "exempt"


class StorageLocation(Enum):
    """Data storage locations"""

    PRIMARY_DATABASE = "primary_database"
    BACKUP_STORAGE = "backup_storage"
    CACHE_LAYER = "cache_layer"
    LOG_FILES = "log_files"
    ARCHIVE_STORAGE = "archive_storage"
    EXTERNAL_SYSTEM = "external_system"
    CDN = "cdn"
    SEARCH_INDEX = "search_index"


class RetentionPeriod(Enum):
    """Standard retention periods for regulatory compliance"""

    DAYS_30 = 30
    DAYS_90 = 90
    DAYS_180 = 180
    YEAR_1 = 365
    YEARS_2 = 730
    YEARS_3 = 1095
    YEARS_5 = 1825
    YEARS_7 = 2555
    YEARS_10 = 3650
    INDEFINITE = -1


@dataclass
class ErasureRequest:
    """Request for data erasure"""

    request_id: str
    user_id: str
    data_categories: List[DataCategory]
    requested_at: datetime
    deadline: datetime
    status: DeletionStatus = DeletionStatus.PENDING
    completion_date: Optional[datetime] = None


@dataclass
class LitigationHold:
    """Legal hold on data deletion"""

    hold_id: str
    case_reference: str
    affected_users: List[str]
    data_categories: List[DataCategory]
    imposed_at: datetime
    expires_at: Optional[datetime] = None
    reason: str = ""
    active: bool = True


@dataclass
class RetentionPolicy:
    """Data retention policy definition"""

    policy_id: str
    policy_name: str
    data_category: DataCategory
    retention_period_days: int
    retention_reason: RetentionReason

    # Policy details
    description: str
    legal_basis: str
    regulatory_reference: Optional[str] = None

    # Scope and conditions
    applies_to_users: Optional[List[str]] = None  # None = all users
    applies_to_countries: Optional[List[str]] = None  # None = all countries
    minimum_retention_days: Optional[int] = None
    maximum_retention_days: Optional[int] = None

    # Deletion configuration
    soft_delete: bool = True  # Soft delete before hard delete
    soft_delete_period_days: int = 30
    backup_before_deletion: bool = True
    require_approval: bool = False

    # Exemptions
    litigation_hold_exempt: bool = False
    regulatory_hold_exempt: bool = False

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "system"
    is_active: bool = True


@dataclass
class DataRecord:
    """Individual data record for retention tracking"""

    record_id: str
    user_id: str
    data_category: DataCategory
    storage_locations: List[StorageLocation]

    # Retention tracking
    created_at: datetime
    last_accessed_at: Optional[datetime] = None
    retention_policy_id: str = ""
    scheduled_deletion_date: Optional[datetime] = None

    # Data details
    data_size_bytes: int = 0
    data_hash: Optional[str] = None
    encryption_status: bool = False

    # Deletion tracking
    deletion_status: DeletionStatus = DeletionStatus.PENDING
    deletion_scheduled_at: Optional[datetime] = None
    deletion_started_at: Optional[datetime] = None
    deletion_completed_at: Optional[datetime] = None
    deletion_attempts: int = 0
    deletion_error: Optional[str] = None

    # Legal holds
    litigation_hold: bool = False
    regulatory_hold: bool = False
    hold_reason: Optional[str] = None
    hold_expiry: Optional[datetime] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeletionJob:
    """Automated deletion job"""

    job_id: str
    job_name: str
    scheduled_time: datetime

    # Job configuration
    data_category: Optional[DataCategory] = None
    user_ids: Optional[List[str]] = None
    storage_locations: Optional[List[StorageLocation]] = None
    retention_policy_ids: Optional[List[str]] = None

    # Execution details
    status: DeletionStatus = DeletionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Results
    records_processed: int = 0
    records_deleted: int = 0
    records_failed: int = 0
    records_skipped: int = 0

    # Error handling
    errors: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "system"


@dataclass
class DataSubjectRequest:
    """GDPR Article 17 data subject erasure request"""

    request_id: str
    user_id: str
    request_type: str  # "erasure", "rectification", "access"
    requested_at: datetime

    # Request details
    reason: str
    specific_data_categories: Optional[List[DataCategory]] = None
    legal_basis: str = "Article 17 - Right to erasure"

    # Processing
    status: str = "pending"  # pending, processing, completed, rejected
    processed_by: Optional[str] = None
    processed_at: Optional[datetime] = None

    # Response
    response_sent_at: Optional[datetime] = None
    data_deleted: List[str] = field(default_factory=list)
    data_retained: List[str] = field(default_factory=list)
    retention_reasons: Dict[str, str] = field(default_factory=dict)

    # Audit trail
    audit_log: List[str] = field(default_factory=list)


class DataRetentionEnforcer:
    """Automated data retention and deletion system"""

    def __init__(self):
        self.retention_policies: Dict[str, RetentionPolicy] = {}
        self.data_records: Dict[str, DataRecord] = {}
        self.deletion_jobs: Dict[str, DeletionJob] = {}
        self.erasure_requests: Dict[str, DataSubjectRequest] = {}

        # Deletion handlers for different storage types
        self.deletion_handlers: Dict[StorageLocation, Callable] = {}

        # Statistics
        self.stats = {
            "total_records_tracked": 0,
            "records_deleted_today": 0,
            "records_scheduled_for_deletion": 0,
            "active_policies": 0,
            "pending_erasure_requests": 0,
        }

        # Initialize default policies
        self._initialize_default_policies()

        # Schedule automated cleanup
        self.cleanup_running = False

    def _initialize_default_policies(self):
        """Initialize default retention policies"""

        default_policies = [
            RetentionPolicy(
                policy_id="gdpr_personal_data",
                policy_name="GDPR Personal Data Retention",
                data_category=DataCategory.PERSONAL_DATA,
                retention_period_days=2555,  # 7 years
                retention_reason=RetentionReason.LEGAL_OBLIGATION,
                description="GDPR compliant retention for personal data",
                legal_basis="GDPR Article 5(1)(e) - storage limitation principle",
                regulatory_reference="GDPR Article 17",
                soft_delete_period_days=30,
                require_approval=False,
            ),
            RetentionPolicy(
                policy_id="conversation_data",
                policy_name="Conversation Data Retention",
                data_category=DataCategory.CONVERSATION_DATA,
                retention_period_days=365,  # 1 year
                retention_reason=RetentionReason.LEGITIMATE_INTERESTS,
                description="Attribution analysis conversation data",
                legal_basis="Legitimate interest for attribution tracking",
                soft_delete_period_days=7,
                require_approval=False,
            ),
            RetentionPolicy(
                policy_id="attribution_data",
                policy_name="Attribution Data Retention",
                data_category=DataCategory.ATTRIBUTION_DATA,
                retention_period_days=2555,  # 7 years for financial records
                retention_reason=RetentionReason.LEGAL_OBLIGATION,
                description="Attribution tracking for payment purposes",
                legal_basis="Contract performance and legal obligation",
                regulatory_reference="Financial record keeping requirements",
                soft_delete_period_days=30,
                require_approval=True,  # Financial data requires approval
            ),
            RetentionPolicy(
                policy_id="financial_data",
                policy_name="Financial Data Retention",
                data_category=DataCategory.FINANCIAL_DATA,
                retention_period_days=2555,  # 7 years
                retention_reason=RetentionReason.LEGAL_OBLIGATION,
                description="Financial transaction and payment data",
                legal_basis="Legal obligation for financial record keeping",
                regulatory_reference="SOX, AML regulations",
                soft_delete_period_days=90,  # Longer soft delete for financial data
                require_approval=True,
            ),
            RetentionPolicy(
                policy_id="system_logs",
                policy_name="System Logs Retention",
                data_category=DataCategory.SYSTEM_LOGS,
                retention_period_days=90,  # 3 months
                retention_reason=RetentionReason.LEGITIMATE_INTERESTS,
                description="System operation and security logs",
                legal_basis="Legitimate interest for system security",
                soft_delete_period_days=7,
                require_approval=False,
            ),
            RetentionPolicy(
                policy_id="audit_logs",
                policy_name="Audit Logs Retention",
                data_category=DataCategory.AUDIT_LOGS,
                retention_period_days=2555,  # 7 years
                retention_reason=RetentionReason.LEGAL_OBLIGATION,
                description="Compliance and security audit logs",
                legal_basis="Legal obligation for audit trail",
                regulatory_reference="SOX, GDPR Article 30",
                soft_delete_period_days=90,
                require_approval=True,
            ),
            RetentionPolicy(
                policy_id="cache_data",
                policy_name="Cache Data Retention",
                data_category=DataCategory.CACHE_DATA,
                retention_period_days=7,  # 1 week
                retention_reason=RetentionReason.LEGITIMATE_INTERESTS,
                description="Temporary cache data for performance",
                legal_basis="Legitimate interest for system performance",
                soft_delete_period_days=1,
                require_approval=False,
            ),
            RetentionPolicy(
                policy_id="temporary_data",
                policy_name="Temporary Data Retention",
                data_category=DataCategory.TEMPORARY_DATA,
                retention_period_days=1,  # 1 day
                retention_reason=RetentionReason.LEGITIMATE_INTERESTS,
                description="Temporary processing data",
                legal_basis="Legitimate interest for processing",
                soft_delete_period_days=0,  # Immediate hard delete
                require_approval=False,
            ),
        ]

        for policy in default_policies:
            self.retention_policies[policy.policy_id] = policy

        self.stats["active_policies"] = len(self.retention_policies)

    def generate_record_id(self) -> str:
        """Generate unique record ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"rec_{timestamp}_{hash(timestamp) % 10000:04d}"

    def generate_job_id(self) -> str:
        """Generate unique deletion job ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"job_{timestamp}_{hash(timestamp) % 10000:04d}"

    def generate_request_id(self) -> str:
        """Generate unique erasure request ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"req_{timestamp}_{hash(timestamp) % 10000:04d}"

    async def register_data_record(
        self,
        user_id: str,
        data_category: DataCategory,
        storage_locations: List[StorageLocation],
        data_size_bytes: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Register data record for retention tracking"""

        record_id = self.generate_record_id()
        now = datetime.now(timezone.utc)

        # Find applicable retention policy
        retention_policy = self._find_applicable_policy(data_category, user_id)
        if not retention_policy:
            logger.warning(f"No retention policy found for {data_category.value}")
            return ""

        # Calculate scheduled deletion date
        scheduled_deletion = now + timedelta(
            days=retention_policy.retention_period_days
        )

        # Create data record
        data_record = DataRecord(
            record_id=record_id,
            user_id=user_id,
            data_category=data_category,
            storage_locations=storage_locations,
            created_at=now,
            retention_policy_id=retention_policy.policy_id,
            scheduled_deletion_date=scheduled_deletion,
            data_size_bytes=data_size_bytes,
            metadata=metadata or {},
        )

        # Generate data hash for integrity
        data_record.data_hash = hashlib.sha256(
            f"{record_id}{user_id}{data_category.value}".encode()
        ).hexdigest()

        # Store record
        self.data_records[record_id] = data_record
        self.stats["total_records_tracked"] += 1

        logger.info(
            f"Data record registered: {record_id} - Deletion scheduled: {scheduled_deletion}"
        )

        return record_id

    def _find_applicable_policy(
        self, data_category: DataCategory, user_id: str
    ) -> Optional[RetentionPolicy]:
        """Find applicable retention policy for data"""

        # Find policies for this data category
        applicable_policies = [
            policy
            for policy in self.retention_policies.values()
            if (
                policy.data_category == data_category
                and policy.is_active
                and (
                    policy.applies_to_users is None
                    or user_id in policy.applies_to_users
                )
            )
        ]

        if not applicable_policies:
            return None

        # Return the most restrictive policy (longest retention)
        return max(applicable_policies, key=lambda p: p.retention_period_days)

    async def schedule_automated_cleanup(self):
        """Schedule automated data cleanup job"""

        job_id = self.generate_job_id()
        now = datetime.now(timezone.utc)

        # Find all records scheduled for deletion
        due_records = [
            record
            for record in self.data_records.values()
            if (
                record.scheduled_deletion_date
                and record.scheduled_deletion_date <= now
                and record.deletion_status == DeletionStatus.PENDING
                and not record.litigation_hold
                and not record.regulatory_hold
            )
        ]

        if not due_records:
            logger.info("No records due for deletion")
            return None

        # Create deletion job
        deletion_job = DeletionJob(
            job_id=job_id,
            job_name=f"Automated Cleanup - {now.strftime('%Y-%m-%d')}",
            scheduled_time=now,
        )

        self.deletion_jobs[job_id] = deletion_job

        # Execute deletion job
        await self._execute_deletion_job(job_id)

        return job_id

    async def _execute_deletion_job(self, job_id: str):
        """Execute automated deletion job"""

        if job_id not in self.deletion_jobs:
            logger.error(f"Deletion job not found: {job_id}")
            return

        job = self.deletion_jobs[job_id]
        now = datetime.now(timezone.utc)

        try:
            job.status = DeletionStatus.IN_PROGRESS
            job.started_at = now

            logger.info(f"Starting deletion job: {job_id}")

            # Find records to process
            records_to_process = [
                record
                for record in self.data_records.values()
                if (
                    record.scheduled_deletion_date
                    and record.scheduled_deletion_date <= now
                    and record.deletion_status == DeletionStatus.PENDING
                    and not record.litigation_hold
                    and not record.regulatory_hold
                )
            ]

            job.records_processed = len(records_to_process)

            # Process each record
            for record in records_to_process:
                try:
                    success = await self._delete_data_record(record)
                    if success:
                        job.records_deleted += 1
                        self.stats["records_deleted_today"] += 1
                    else:
                        job.records_failed += 1
                except Exception as e:
                    logger.error(f"Failed to delete record {record.record_id}: {e}")
                    job.records_failed += 1
                    job.errors.append(f"Record {record.record_id}: {str(e)}")

            # Update job status
            job.status = DeletionStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)

            logger.info(
                f"Deletion job completed: {job_id} - Deleted: {job.records_deleted}, Failed: {job.records_failed}"
            )

        except Exception as e:
            job.status = DeletionStatus.FAILED
            job.errors.append(f"Job execution failed: {str(e)}")
            logger.error(f"Deletion job failed: {job_id} - {e}")

    async def _delete_data_record(self, record: DataRecord) -> bool:
        """Delete data record from all storage locations"""

        try:
            record.deletion_status = DeletionStatus.IN_PROGRESS
            record.deletion_started_at = datetime.now(timezone.utc)
            record.deletion_attempts += 1

            # Get retention policy
            policy = self.retention_policies.get(record.retention_policy_id)
            if not policy:
                record.deletion_error = "Retention policy not found"
                record.deletion_status = DeletionStatus.FAILED
                return False

            # Check if soft delete period has passed
            if policy.soft_delete and record.deletion_attempts == 1:
                # Schedule hard deletion after soft delete period
                soft_delete_until = datetime.now(timezone.utc) + timedelta(
                    days=policy.soft_delete_period_days
                )
                record.scheduled_deletion_date = soft_delete_until
                record.deletion_status = DeletionStatus.PENDING
                logger.info(
                    f"Soft delete applied to {record.record_id}, hard delete scheduled for {soft_delete_until}"
                )
                return True

            # Perform hard deletion
            deletion_success = True

            for storage_location in record.storage_locations:
                try:
                    # Get deletion handler for storage location
                    handler = self.deletion_handlers.get(storage_location)
                    if handler:
                        await handler(record)
                    else:
                        # Mock deletion for demo
                        logger.info(
                            f"Mock deletion from {storage_location.value} for record {record.record_id}"
                        )
                        await asyncio.sleep(0.1)  # Simulate deletion time

                except Exception as e:
                    logger.error(f"Failed to delete from {storage_location.value}: {e}")
                    deletion_success = False

            if deletion_success:
                record.deletion_status = DeletionStatus.COMPLETED
                record.deletion_completed_at = datetime.now(timezone.utc)
                logger.info(f"Data record deleted successfully: {record.record_id}")
                return True
            else:
                record.deletion_status = DeletionStatus.FAILED
                record.deletion_error = "Partial deletion failure"
                return False

        except Exception as e:
            record.deletion_status = DeletionStatus.FAILED
            record.deletion_error = str(e)
            logger.error(f"Failed to delete data record {record.record_id}: {e}")
            return False

    async def process_erasure_request(
        self,
        user_id: str,
        reason: str,
        specific_categories: Optional[List[DataCategory]] = None,
    ) -> str:
        """Process GDPR Article 17 erasure request"""

        request_id = self.generate_request_id()
        now = datetime.now(timezone.utc)

        # Create erasure request
        erasure_request = DataSubjectRequest(
            request_id=request_id,
            user_id=user_id,
            request_type="erasure",
            requested_at=now,
            reason=reason,
            specific_data_categories=specific_categories,
        )

        self.erasure_requests[request_id] = erasure_request
        self.stats["pending_erasure_requests"] += 1

        # Process request
        await self._process_erasure_request(request_id)

        logger.info(f"Erasure request processed: {request_id} for user {user_id}")

        return request_id

    async def _process_erasure_request(self, request_id: str):
        """Process individual erasure request"""

        if request_id not in self.erasure_requests:
            logger.error(f"Erasure request not found: {request_id}")
            return

        request = self.erasure_requests[request_id]

        try:
            request.status = "processing"
            request.processed_at = datetime.now(timezone.utc)
            request.processed_by = "automated_system"

            # Find user's data records
            user_records = [
                record
                for record in self.data_records.values()
                if record.user_id == request.user_id
            ]

            # Filter by specific categories if requested
            if request.specific_data_categories:
                user_records = [
                    record
                    for record in user_records
                    if record.data_category in request.specific_data_categories
                ]

            # Process each record
            for record in user_records:
                # Check if record can be deleted (no legal holds)
                if record.litigation_hold or record.regulatory_hold:
                    request.data_retained.append(record.record_id)
                    request.retention_reasons[record.record_id] = (
                        record.hold_reason or "Legal hold"
                    )
                    request.audit_log.append(
                        f"Record {record.record_id} retained due to legal hold"
                    )
                    continue

                # Check retention policy exemptions
                policy = self.retention_policies.get(record.retention_policy_id)
                if policy and (
                    policy.litigation_hold_exempt or policy.regulatory_hold_exempt
                ):
                    request.data_retained.append(record.record_id)
                    request.retention_reasons[record.record_id] = (
                        f"Policy exemption: {policy.legal_basis}"
                    )
                    request.audit_log.append(
                        f"Record {record.record_id} retained due to policy exemption"
                    )
                    continue

                # Schedule immediate deletion
                record.scheduled_deletion_date = datetime.now(timezone.utc)
                record.deletion_status = DeletionStatus.PENDING
                request.data_deleted.append(record.record_id)
                request.audit_log.append(
                    f"Record {record.record_id} scheduled for immediate deletion"
                )

            # Update request status
            request.status = "completed"
            request.response_sent_at = datetime.now(timezone.utc)

            # Trigger immediate cleanup for deleted records
            await self.schedule_automated_cleanup()

            logger.info(
                f"Erasure request completed: {request_id} - Deleted: {len(request.data_deleted)}, Retained: {len(request.data_retained)}"
            )

        except Exception as e:
            request.status = "failed"
            request.audit_log.append(f"Processing failed: {str(e)}")
            logger.error(f"Failed to process erasure request {request_id}: {e}")

    async def apply_litigation_hold(
        self,
        user_id: Optional[str] = None,
        data_categories: Optional[List[DataCategory]] = None,
        hold_reason: str = "Litigation hold",
        hold_expiry: Optional[datetime] = None,
    ) -> int:
        """Apply litigation hold to prevent data deletion"""

        # Find records to hold
        records_to_hold = []

        for record in self.data_records.values():
            if user_id and record.user_id != user_id:
                continue
            if data_categories and record.data_category not in data_categories:
                continue
            records_to_hold.append(record)

        # Apply hold
        for record in records_to_hold:
            record.litigation_hold = True
            record.hold_reason = hold_reason
            record.hold_expiry = hold_expiry
            record.deletion_status = DeletionStatus.BLOCKED

        logger.info(f"Litigation hold applied to {len(records_to_hold)} records")

        return len(records_to_hold)

    async def release_litigation_hold(
        self,
        user_id: Optional[str] = None,
        data_categories: Optional[List[DataCategory]] = None,
    ) -> int:
        """Release litigation hold and resume normal retention"""

        # Find records to release
        records_to_release = []

        for record in self.data_records.values():
            if not record.litigation_hold:
                continue
            if user_id and record.user_id != user_id:
                continue
            if data_categories and record.data_category not in data_categories:
                continue
            records_to_release.append(record)

        # Release hold
        for record in records_to_release:
            record.litigation_hold = False
            record.hold_reason = None
            record.hold_expiry = None
            record.deletion_status = DeletionStatus.PENDING

        logger.info(f"Litigation hold released from {len(records_to_release)} records")

        return len(records_to_release)

    async def get_retention_report(
        self,
        user_id: Optional[str] = None,
        data_category: Optional[DataCategory] = None,
    ) -> Dict[str, Any]:
        """Generate comprehensive retention report"""

        # Filter records
        records = list(self.data_records.values())

        if user_id:
            records = [r for r in records if r.user_id == user_id]

        if data_category:
            records = [r for r in records if r.data_category == data_category]

        # Calculate statistics
        total_records = len(records)
        records_due_deletion = len(
            [
                r
                for r in records
                if r.scheduled_deletion_date
                and r.scheduled_deletion_date <= datetime.now(timezone.utc)
            ]
        )
        records_on_hold = len(
            [r for r in records if r.litigation_hold or r.regulatory_hold]
        )
        records_deleted = len(
            [r for r in records if r.deletion_status == DeletionStatus.COMPLETED]
        )

        # Category breakdown
        category_breakdown = {}
        for category in DataCategory:
            category_records = [r for r in records if r.data_category == category]
            category_breakdown[category.value] = {
                "total": len(category_records),
                "due_deletion": len(
                    [
                        r
                        for r in category_records
                        if r.scheduled_deletion_date
                        and r.scheduled_deletion_date <= datetime.now(timezone.utc)
                    ]
                ),
                "on_hold": len(
                    [
                        r
                        for r in category_records
                        if r.litigation_hold or r.regulatory_hold
                    ]
                ),
                "deleted": len(
                    [
                        r
                        for r in category_records
                        if r.deletion_status == DeletionStatus.COMPLETED
                    ]
                ),
            }

        # Policy breakdown
        policy_breakdown = {}
        for policy_id, policy in self.retention_policies.items():
            policy_records = [r for r in records if r.retention_policy_id == policy_id]
            policy_breakdown[policy_id] = {
                "policy_name": policy.policy_name,
                "total_records": len(policy_records),
                "retention_period_days": policy.retention_period_days,
                "records_due": len(
                    [
                        r
                        for r in policy_records
                        if r.scheduled_deletion_date
                        and r.scheduled_deletion_date <= datetime.now(timezone.utc)
                    ]
                ),
            }

        return {
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
            "scope": {
                "user_id": user_id,
                "data_category": data_category.value if data_category else None,
            },
            "summary": {
                "total_records": total_records,
                "records_due_deletion": records_due_deletion,
                "records_on_hold": records_on_hold,
                "records_deleted": records_deleted,
                "compliance_rate": (records_deleted / total_records * 100)
                if total_records > 0
                else 0,
            },
            "category_breakdown": category_breakdown,
            "policy_breakdown": policy_breakdown,
            "statistics": self.stats,
            "recent_deletions": len(
                [
                    r
                    for r in records
                    if r.deletion_completed_at
                    and (datetime.now(timezone.utc) - r.deletion_completed_at).days <= 7
                ]
            ),
        }

    async def get_erasure_request_status(self, request_id: str) -> Dict[str, Any]:
        """Get status of erasure request"""

        if request_id not in self.erasure_requests:
            return {"error": "Request not found"}

        request = self.erasure_requests[request_id]

        return {
            "request_id": request.request_id,
            "user_id": request.user_id,
            "status": request.status,
            "requested_at": request.requested_at.isoformat(),
            "processed_at": request.processed_at.isoformat()
            if request.processed_at
            else None,
            "data_deleted_count": len(request.data_deleted),
            "data_retained_count": len(request.data_retained),
            "retention_reasons": request.retention_reasons,
            "audit_log": request.audit_log,
        }

    async def start_automated_cleanup_scheduler(self):
        """Start automated cleanup scheduler"""

        if self.cleanup_running:
            logger.warning("Cleanup scheduler already running")
            return

        self.cleanup_running = True
        logger.info("Starting automated cleanup scheduler")

        try:
            while self.cleanup_running:
                # Run cleanup every hour
                await self.schedule_automated_cleanup()
                await asyncio.sleep(3600)  # 1 hour

        except asyncio.CancelledError:
            logger.info("Cleanup scheduler cancelled")
        except Exception as e:
            logger.error(f"Cleanup scheduler error: {e}")
        finally:
            self.cleanup_running = False

    async def stop_automated_cleanup_scheduler(self):
        """Stop automated cleanup scheduler"""

        self.cleanup_running = False
        logger.info("Stopping automated cleanup scheduler")

    def register_deletion_handler(
        self, storage_location: StorageLocation, handler: Callable
    ):
        """Register custom deletion handler for storage location"""

        self.deletion_handlers[storage_location] = handler
        logger.info(f"Deletion handler registered for {storage_location.value}")

    async def update_retention_policy(
        self,
        policy_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Update retention policy"""

        if policy_id not in self.retention_policies:
            logger.error(f"Retention policy not found: {policy_id}")
            return False

        policy = self.retention_policies[policy_id]

        # Update policy fields
        for key, value in updates.items():
            if hasattr(policy, key):
                setattr(policy, key, value)

        policy.updated_at = datetime.now(timezone.utc)

        # Recalculate scheduled deletion dates for affected records
        affected_records = [
            record
            for record in self.data_records.values()
            if record.retention_policy_id == policy_id
        ]

        for record in affected_records:
            new_deletion_date = record.created_at + timedelta(
                days=policy.retention_period_days
            )
            record.scheduled_deletion_date = new_deletion_date

        logger.info(
            f"Retention policy updated: {policy_id} - Affected records: {len(affected_records)}"
        )

        return True


# Factory function
def create_data_retention_enforcer() -> DataRetentionEnforcer:
    """Create data retention enforcer instance"""
    return DataRetentionEnforcer()
