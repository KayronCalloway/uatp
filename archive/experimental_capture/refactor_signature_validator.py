#!/usr/bin/env python3
"""
Script to refactor SignatureValidator from boolean flag to dependency injection.
"""


def refactor_signature_validator():
    """Apply all refactoring changes to signature_validator.py"""

    file_path = "src/security/signature_validator.py"

    with open(file_path) as f:
        content = f.read()

    # 1. Update imports
    old_imports = """import hashlib
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, Optional, Set, Tuple"""

    new_imports = """import hashlib
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING, Dict, Optional, Set, Tuple

if TYPE_CHECKING:
    from src.security.replay_protection_policy import ReplayProtectionPolicy"""

    content = content.replace(old_imports, new_imports)

    # 2. Update constructor signature
    old_constructor = """    def __init__(self, enable_replay_protection: bool = True):
        \"\"\"Initialize signature validator.\"\"\"
        self.enable_replay_protection = enable_replay_protection
        self.replay_store = ReplayProtectionStore() if enable_replay_protection else None"""

    new_constructor = """    def __init__(self, replay_protection_policy: Optional["ReplayProtectionPolicy"] = None):
        \"\"\"Initialize signature validator with dependency injection.

        Args:
            replay_protection_policy: ReplayProtectionPolicy implementation for replay attack protection.
                                     Defaults to RealReplayProtectionPolicy() for production.
                                     Tests can inject TestReplayProtectionPolicy() or MockReplayProtectionPolicy().
        \"\"\"
        # Import here to avoid circular dependencies
        from src.security.replay_protection_policy import RealReplayProtectionPolicy

        self.replay_protection_policy = replay_protection_policy or RealReplayProtectionPolicy()
        self.replay_store = ReplayProtectionStore() if self.replay_protection_policy.should_check_replay() else None"""

    content = content.replace(old_constructor, new_constructor)

    # 3. Update logger line
    content = content.replace(
        'logger.info(f"Signature validator initialized (replay protection: {enable_replay_protection})")',
        'logger.info(f"Signature validator initialized (policy={type(self.replay_protection_policy).__name__})")',
    )

    # 4. Update replay protection check logic
    old_replay_check = """            # Check for replay attacks
            if self.enable_replay_protection and self.replay_store:
                if self.replay_store.is_signature_used(metadata.signature_hash):
                    return False, "SECURITY ERROR: Signature replay attack detected"

                # Record signature use
                if not self.replay_store.record_signature_use(metadata):
                    return False, "SECURITY ERROR: Failed to record signature use\""""

    new_replay_check = """            # Check for replay attacks using injected policy
            if self.replay_protection_policy.should_check_replay() and self.replay_store:
                if self.replay_store.is_signature_used(metadata.signature_hash):
                    return False, "SECURITY ERROR: Signature replay attack detected"

                # Record signature use if policy requires it
                if self.replay_protection_policy.should_record_signature():
                    if not self.replay_store.record_signature_use(metadata):
                        return False, "SECURITY ERROR: Failed to record signature use\""""

    content = content.replace(old_replay_check, new_replay_check)

    # 5. Update get_validation_statistics method
    old_stats = """    def get_validation_statistics(self) -> Dict[str, int]:
        \"\"\"Get validation statistics.\"\"\"
        stats = {
            "replay_protection_enabled": int(self.enable_replay_protection),
            "total_signatures_tracked": 0,
            "active_signatures": 0
        }"""

    new_stats = """    def get_validation_statistics(self) -> Dict[str, int]:
        \"\"\"Get validation statistics.\"\"\"
        stats = {
            "replay_protection_policy": type(self.replay_protection_policy).__name__,
            "replay_checks_enabled": int(self.replay_protection_policy.should_check_replay()),
            "total_signatures_tracked": 0,
            "active_signatures": 0
        }"""

    content = content.replace(old_stats, new_stats)

    # 6. Update global singleton
    content = content.replace(
        "signature_validator = SignatureValidator(enable_replay_protection=True)",
        "# Global validator instance - uses RealReplayProtectionPolicy by default\nsignature_validator = SignatureValidator()",
    )

    # 7. Update test example at bottom
    content = content.replace(
        "validator = SignatureValidator(enable_replay_protection=True)",
        "from src.security.replay_protection_policy import RealReplayProtectionPolicy\n        \n        validator = SignatureValidator(replay_protection_policy=RealReplayProtectionPolicy())",
    )

    # Write the refactored content
    with open(file_path, "w") as f:
        f.write(content)

    print("✅ Successfully refactored signature_validator.py")
    print("   - Updated imports to include TYPE_CHECKING and ReplayProtectionPolicy")
    print("   - Refactored constructor from boolean flag to dependency injection")
    print("   - Updated replay protection check logic to use injected policy")
    print("   - Updated statistics method to show policy type")
    print("   - Updated global singleton to use RealReplayProtectionPolicy")
    print("   - Updated test example to use injected policy")


if __name__ == "__main__":
    refactor_signature_validator()
