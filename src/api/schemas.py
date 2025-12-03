from typing import Any, Dict, List, Optional

from src.capsule_schema import (
    AnyCapsule,
    ReasoningTracePayload,
    CapsuleType,
    CapsuleStatus,
)
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Schema for a generic error response."""

    error: str
    details: Optional[str] = None


class CapsuleListResponse(BaseModel):
    """Schema for the response of the list_capsules endpoint."""

    capsules: List[AnyCapsule]


class CompressedCapsuleListResponse(BaseModel):
    """Schema for the compressed response of the list_capsules endpoint."""

    capsules: List[Dict[str, Any]]


class ListCapsulesQuery(BaseModel):
    """Schema for the query parameters of the list_capsules endpoint."""

    page: int = 1
    per_page: int = 10
    compress: bool = False


class GetCapsuleQuery(BaseModel):
    """Schema for the query parameters of the get_capsule endpoint."""

    include_raw: bool = False


class CapsuleDetailResponse(BaseModel):
    """Schema for a single capsule response, with optional raw data."""

    capsule: AnyCapsule
    raw_data: Optional[Dict[str, Any]] = None


class CapsuleStatsResponse(BaseModel):
    """Schema for the response of the get_capsule_stats endpoint."""

    total_capsules: int
    types: Dict[str, int]
    unique_agents: int


class VerificationResponse(BaseModel):
    """Schema for the response of the verify_capsule endpoint."""

    capsule_id: str
    verified: bool
    from_cache: bool = False
    metadata_has_verify_key: Optional[bool] = None
    verification_error: Optional[str] = None
    error: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Schema for the response of the health_check endpoint."""

    status: str
    timestamp: str
    version: str
    engine: Dict[str, Any]
    features: Dict[str, bool]


# New schemas for proper capsule creation
class CreateReasoningCapsuleRequest(BaseModel):
    """Schema for creating a reasoning trace capsule."""

    reasoning_trace: ReasoningTracePayload
    status: Optional[CapsuleStatus] = CapsuleStatus.ACTIVE


class CapsuleCreationResponse(BaseModel):
    """Schema for capsule creation response."""

    capsule_id: str
    status: str
    message: str
    capsule: AnyCapsule


class IndexResponse(BaseModel):
    """Schema for the response of the index endpoint."""

    service: str
    version: str
    documentation: str


# Mobile API Schemas


class MobileHealthResponse(BaseModel):
    """Schema for mobile health check response."""

    status: str
    timestamp: str
    capabilities: Dict[str, Any]
    server_version: str
    min_client_version: str


class MobileCapsuleRequest(BaseModel):
    """Schema for single mobile capsule creation request."""

    device_id: str
    platform: str  # "ios", "android", "web"
    messages: List[Dict[str, Any]]
    parent_capsule_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MobileCapsuleResponse(BaseModel):
    """Schema for single mobile capsule creation response."""

    success: bool
    capsule_id: str
    status: str
    timestamp: str
    verification_hash: Optional[str] = None
    sync_token: str
    server_timestamp: str


class BatchCapsuleRequest(BaseModel):
    """Schema for batch capsule submission."""

    device_id: str
    capsules: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None


class BatchCapsuleResponse(BaseModel):
    """Schema for batch capsule submission response."""

    success: bool
    total_submitted: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]
    sync_token: str
    server_timestamp: str


class SyncRequest(BaseModel):
    """Schema for device synchronization request."""

    device_id: str
    last_sync_timestamp: str
    platform: str


class SyncResponse(BaseModel):
    """Schema for device synchronization response."""

    success: bool
    capsules: List[Dict[str, Any]]
    sync_token: str
    server_timestamp: str
    has_more: bool


class AIGenerateRequest(BaseModel):
    """Schema for the /ai/generate endpoint request."""

    prompt: str
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 150
    temperature: Optional[float] = None


class AIGenerateResponse(BaseModel):
    """Schema for the /ai/generate endpoint response."""

    status: str
    generated_text: str


class ChainForksResponse(BaseModel):
    """Schema for the /chain/forks endpoint."""

    fork_count: int
    forks: Dict[str, List[str]]


class ChainSeal(BaseModel):
    """Schema for a single chain seal."""

    seal_id: str
    chain_id: str
    chain_state_hash: str
    signer_id: str
    timestamp: str
    note: str
    version: str
    signature: str
    verify_key: str


class ChainSealListResponse(BaseModel):
    """Schema for a list of chain seals."""

    seals: List[ChainSeal]


class SealChainRequest(BaseModel):
    """Schema for the /chain/seal endpoint request."""

    chain_id: str
    note: Optional[str] = ""


class SealChainResponse(BaseModel):
    """Schema for the /chain/seal endpoint response."""

    status: str
    seal: ChainSeal


class VerifySealQuery(BaseModel):
    """Schema for the /chain/verify-seal query parameters."""

    verify_key: str
    seal_id: Optional[str] = None


class VerifySealResponse(BaseModel):
    """Schema for the /chain/verify-seal endpoint response."""

    verified: bool
    chain_id: str
    seal_id: Optional[str]
    signer_id: Optional[str] = None
    timestamp: Optional[str] = None
    chain_unchanged: Optional[bool] = None
    note: Optional[str] = None
    error: Optional[str] = None


# --- Capsule Creation Request Schemas ---


class CreateCapsuleRequest(BaseModel):
    """Schema for creating any type of capsule with minimal required fields."""

    capsule_type: CapsuleType
    payload: Dict[str, Any]
    status: Optional[CapsuleStatus] = CapsuleStatus.ACTIVE
