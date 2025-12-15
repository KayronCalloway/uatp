"""
Replay protection policy interfaces for signature validator.

Provides abstraction for different replay protection policies (production vs testing).
"""

from abc import ABC, abstractmethod


class ReplayProtectionPolicy(ABC):
    """Abstract interface for replay protection policies."""

    @abstractmethod
    def should_check_replay(self) -> bool:
        """
        Determine if replay protection checks should be performed.

        Returns:
            True if replay checks should be performed, False otherwise
        """
        pass

    @abstractmethod
    def should_record_signature(self) -> bool:
        """
        Determine if signature usage should be recorded for replay tracking.

        Returns:
            True if signature should be recorded, False otherwise
        """
        pass


class RealReplayProtectionPolicy(ReplayProtectionPolicy):
    """Production replay protection policy that enforces replay attack prevention."""

    def should_check_replay(self) -> bool:
        """Always enforce replay protection in production."""
        return True

    def should_record_signature(self) -> bool:
        """Always record signatures for replay tracking in production."""
        return True


class TestReplayProtectionPolicy(ReplayProtectionPolicy):
    """Test replay protection policy that skips replay checks.

    Used in testing to verify signature validation without actually tracking replays.
    Allows tests to use the same signature multiple times without replay detection.
    """

    def should_check_replay(self) -> bool:
        """Skip replay checks in test mode."""
        return False

    def should_record_signature(self) -> bool:
        """Skip signature recording in test mode."""
        return False


class MockReplayProtectionPolicy(ReplayProtectionPolicy):
    """Mock replay protection policy for testing specific replay scenarios.

    Allows tests to control exact replay behavior for specific test cases.
    """

    def __init__(self, check_replay: bool = True, record_signature: bool = True):
        """
        Initialize mock replay protection policy.

        Args:
            check_replay: Whether this policy should check for replays (default True)
            record_signature: Whether this policy should record signatures (default True)
        """
        self._check_replay = check_replay
        self._record_signature = record_signature

    def should_check_replay(self) -> bool:
        """Return configured replay check decision."""
        return self._check_replay

    def should_record_signature(self) -> bool:
        """Return configured signature recording decision."""
        return self._record_signature

    def set_check_replay(self, check_replay: bool):
        """Change the replay check decision dynamically."""
        self._check_replay = check_replay

    def set_record_signature(self, record_signature: bool):
        """Change the signature recording decision dynamically."""
        self._record_signature = record_signature
