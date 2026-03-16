"""
Capture Facet - How/why the capsule was captured.

Describes the capture process:
- Trigger
- Source system
- Environment
- User context
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.schema.base import JobFacet


@dataclass
class UATPCaptureJobFacet(JobFacet):
    """
    Metadata about the capture process (as Job definition).

    This facet describes HOW the capsule was created.
    """

    # Capture mechanism
    capture_type: str = "claude_code"  # claude_code, api_call, manual, etc.
    capture_hook: Optional[str] = None  # auto_capture.sh, etc.
    capture_library: Optional[str] = None  # claude_code_capture.py

    # Trigger
    trigger_event: str = "manual"  # manual, file_modification, api_call, scheduled
    trigger_source: Optional[str] = None  # What triggered capture

    # Source system
    source_platform: str = "claude_code"  # claude_code, api, web
    source_version: Optional[str] = None  # Platform version
    model_used: Optional[str] = None  # claude-3.5-sonnet, etc.

    # Environment
    environment: str = "development"  # development, staging, production
    git_branch: Optional[str] = None
    git_commit: Optional[str] = None
    working_directory: Optional[str] = None

    # User context (hashed for privacy)
    user_id_hash: Optional[str] = None  # Hashed user ID
    organization_id: Optional[str] = None
    session_id: Optional[str] = None

    # Capabilities used
    capabilities: List[str] = field(default_factory=list)  # What features were active

    # Additional context
    extra_context: Dict[str, Any] = field(default_factory=dict)
