"""
UATP Python SDK - Official Developer Kit

The complete Python SDK for integrating with UATP's civilization-grade infrastructure.

 Features:
- Simple attribution tracking for AI interactions
- Real-time economic attribution and payments
- Constitutional governance participation
- Zero-knowledge privacy proofs
- C2PA content credentials generation
- World Economic Forum Top 10 2025 watermarking
- Multi-platform AI integration (OpenAI, Anthropic, HuggingFace)

 Getting Started:
```python
from uatp_sdk import UATP

# Initialize UATP client
client = UATP(api_key="your-api-key")

# Track AI interaction with attribution
result = client.track_ai_interaction(
    prompt="Explain quantum computing",
    response="Quantum computing uses quantum mechanics...",
    platform="openai",
    model="gpt-4"
)

# Get attribution rewards
rewards = client.get_attribution_rewards(user_id="your-user-id")
```
"""

from .attribution import AttributionResult, AttributionTracker
from .client import UATP, UATPConfig
from .economics import EconomicEngine, RewardCalculator
from .federation import FederationClient, Node
from .governance import GovernanceClient, Proposal, Vote
from .privacy import PrivacyEngine, ZKProof
from .watermarking import WatermarkEngine, WatermarkResult

__version__ = "1.0.0"
__author__ = "UATP Foundation"
__description__ = (
    "Official Python SDK for UATP civilization-grade AI attribution infrastructure"
)

__all__ = [
    # Main client
    "UATP",
    "UATPConfig",
    # Attribution tracking
    "AttributionTracker",
    "AttributionResult",
    # Economic systems
    "EconomicEngine",
    "RewardCalculator",
    # Governance participation
    "GovernanceClient",
    "Proposal",
    "Vote",
    # Privacy and security
    "PrivacyEngine",
    "ZKProof",
    # Watermarking
    "WatermarkEngine",
    "WatermarkResult",
    # Federation
    "FederationClient",
    "Node",
]
