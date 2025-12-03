"""
Capsule Dividend Engine for UATP Capsule Engine.

This module implements the Capsule Dividend Engine, which distributes value
across capsule ancestry chains, ensuring that all contributors in a capsule's
lineage receive fair compensation based on their influence and contribution.
"""

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union
import hashlib

from src.capsule_schema import CapsuleStatus
from src.engine.capsule_engine import CapsuleEngine
from src.integrations.economic.common_attribution_fund import (
    CommonAttributionFund,
    ContributionType,
)

logger = logging.getLogger(__name__)


class DistributionModel(Enum):
    """Distribution models for dividing value along ancestry chains."""

    LINEAR = auto()  # Equal distribution across generations
    EXPONENTIAL = auto()  # More recent generations get higher proportion
    LOGARITHMIC = auto()  # Earlier generations get higher proportion
    CUSTOM = auto()  # Custom distribution defined by weights


@dataclass
class AncestryNode:
    """Represents a node in the capsule ancestry tree."""

    capsule_id: str
    parent_ids: List[str] = field(default_factory=list)
    child_ids: List[str] = field(default_factory=list)
    depth: int = 0
    contribution_weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValueDistribution:
    """Records how value is distributed across a capsule's ancestry."""

    distribution_id: str
    source_capsule_id: str
    total_value: Decimal
    currency: str = "USD"
    distributions: Dict[str, Decimal] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    model: DistributionModel = DistributionModel.LINEAR
    metadata: Dict[str, Any] = field(default_factory=dict)


class CapsuleDividendEngine:
    """
    Capsule Dividend Engine implementation for UATP Capsule Engine.

    The Capsule Dividend Engine distributes value across capsule ancestry chains,
    ensuring fair compensation for all contributors in a capsule's lineage based on
    their influence and contribution to the final outcome.
    """

    def __init__(
        self,
        engine_id: str = None,
        capsule_engine: Optional[CapsuleEngine] = None,
        attribution_fund: Optional[CommonAttributionFund] = None,
        registry_path: str = None,
    ):
        """
        Initialize the Capsule Dividend Engine.

        Args:
            engine_id: Unique identifier for this engine instance
            capsule_engine: CapsuleEngine instance for accessing capsules
            attribution_fund: CommonAttributionFund instance for attribution
            registry_path: Path to store engine data
        """
        self.engine_id = engine_id or str(uuid.uuid4())
        self.capsule_engine = capsule_engine
        self.attribution_fund = attribution_fund
        self.registry_path = registry_path or os.path.join(
            os.getcwd(), "dividend_engine"
        )

        # Create registry directory if it doesn't exist
        os.makedirs(self.registry_path, exist_ok=True)

        # Cache for ancestry trees
        self.ancestry_cache: Dict[str, Dict[str, AncestryNode]] = {}

        # Distribution history
        self.distributions: Dict[str, ValueDistribution] = {}

        # Default distribution weights by model
        self.model_weights = {
            DistributionModel.LINEAR: self._linear_weights,
            DistributionModel.EXPONENTIAL: self._exponential_weights,
            DistributionModel.LOGARITHMIC: self._logarithmic_weights,
            DistributionModel.CUSTOM: self._custom_weights,
        }

        # SECURITY: Initialize atomic locking and security components for flash loan protection
        self._distribution_locks: Dict[str, asyncio.Lock] = {}
        self._global_distribution_lock = asyncio.Lock()
        self._state_snapshots: Dict[str, Dict] = {}
        self._distribution_timestamps: Dict[str, datetime] = {}

        # SECURITY: Flash loan attack detection
        self.min_distribution_interval = timedelta(
            minutes=5
        )  # Minimum 5 minutes between distributions
        self.high_value_threshold = Decimal(
            "1000.0"
        )  # Threshold for high-value confirmations
        self.distribution_confirmations: Dict[str, Dict] = {}

        # SECURITY: Rate limiting for distributions
        self.distribution_rate_limits: Dict[str, List[datetime]] = {}
        self.max_distributions_per_hour = 10
        self.max_distributions_per_day = 50
        self.min_distribution_interval = timedelta(
            minutes=10
        )  # Minimum 10 minutes between distributions
        self.last_distribution_time = {}  # Track last distribution time per capsule
        self.distribution_confirmations = {}  # Track confirmation requirements
        self.ancestry_checksums = {}  # Track ancestry integrity
        self.high_value_threshold = Decimal(
            "10000"
        )  # Threshold for high-value confirmation

        # SECURITY: Atomic state management
        self._distribution_lock = asyncio.Lock()
        self._state_validation_enabled = True

        # SECURITY: Rate limiting for distribution requests
        self._distribution_requests = defaultdict(list)
        self._max_distributions_per_hour = 10

        # Load existing data
        self._initialize_engine()

        logger.info(f"Capsule Dividend Engine initialized with ID {self.engine_id}")

    def _initialize_engine(self):
        """Initialize engine data structures and load existing data."""
        try:
            # Load existing data if available
            self._load_engine_data()
        except Exception as e:
            logger.warning(
                f"Could not load engine data: {e}. Starting with empty engine."
            )
            # Initialize empty data stores
            self._save_engine_data()

    def _load_engine_data(self):
        """Load engine data from registry files."""
        engine_file = os.path.join(self.registry_path, f"engine_{self.engine_id}.json")

        if os.path.exists(engine_file):
            with open(engine_file) as f:
                data = json.load(f)

            # Load distributions
            for dist_data in data.get("distributions", []):
                dist_data["timestamp"] = datetime.fromisoformat(dist_data["timestamp"])
                dist_data["total_value"] = Decimal(str(dist_data["total_value"]))

                # Convert distribution values to Decimal
                distributions = {}
                for capsule_id, amount in dist_data.get("distributions", {}).items():
                    distributions[capsule_id] = Decimal(str(amount))
                dist_data["distributions"] = distributions

                # Convert model to enum
                dist_data["model"] = DistributionModel[dist_data["model"]]

                distribution = ValueDistribution(**dist_data)
                self.distributions[distribution.distribution_id] = distribution

            # Load ancestry cache (simplified version - full version would load all nodes)
            for capsule_id, ancestry_data in data.get("ancestry_cache", {}).items():
                if capsule_id not in self.ancestry_cache:
                    self.ancestry_cache[capsule_id] = {}

                for node_id, node_data in ancestry_data.items():
                    ancestry_node = AncestryNode(
                        capsule_id=node_data["capsule_id"],
                        parent_ids=node_data.get("parent_ids", []),
                        child_ids=node_data.get("child_ids", []),
                        depth=node_data.get("depth", 0),
                        contribution_weight=node_data.get("contribution_weight", 1.0),
                        metadata=node_data.get("metadata", {}),
                    )
                    self.ancestry_cache[capsule_id][node_id] = ancestry_node

            logger.info(
                f"Loaded engine data with {len(self.distributions)} distributions"
            )

    def _save_engine_data(self):
        """Save engine data to registry files."""
        engine_file = os.path.join(self.registry_path, f"engine_{self.engine_id}.json")

        # Prepare data for serialization
        data = {"engine_id": self.engine_id, "distributions": [], "ancestry_cache": {}}

        # Serialize distributions
        for distribution in self.distributions.values():
            dist_dict = {
                "distribution_id": distribution.distribution_id,
                "source_capsule_id": distribution.source_capsule_id,
                "total_value": str(distribution.total_value),
                "currency": distribution.currency,
                "timestamp": distribution.timestamp.isoformat(),
                "model": distribution.model.name,
                "metadata": distribution.metadata,
            }

            # Serialize distribution amounts
            dist_amounts = {}
            for capsule_id, amount in distribution.distributions.items():
                dist_amounts[capsule_id] = str(amount)
            dist_dict["distributions"] = dist_amounts

            data["distributions"].append(dist_dict)

        # Serialize ancestry cache
        for capsule_id, nodes in self.ancestry_cache.items():
            data["ancestry_cache"][capsule_id] = {}
            for node_id, node in nodes.items():
                data["ancestry_cache"][capsule_id][node_id] = {
                    "capsule_id": node.capsule_id,
                    "parent_ids": node.parent_ids,
                    "child_ids": node.child_ids,
                    "depth": node.depth,
                    "contribution_weight": node.contribution_weight,
                    "metadata": node.metadata,
                }

        # Save to file
        with open(engine_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved engine data to {engine_file}")

    async def build_ancestry_tree(
        self, capsule_id: str, max_depth: int = None
    ) -> Dict[str, AncestryNode]:
        """
        Build an ancestry tree for a capsule.

        Args:
            capsule_id: Root capsule ID to start from
            max_depth: Maximum depth to traverse (None for unlimited)

        Returns:
            Dictionary mapping capsule IDs to ancestry nodes
        """
        # Check cache first
        if capsule_id in self.ancestry_cache:
            logger.debug(f"Using cached ancestry tree for capsule {capsule_id}")
            return self.ancestry_cache[capsule_id]

        # Create new ancestry tree
        ancestry_tree: Dict[str, AncestryNode] = {}

        # Need capsule engine to traverse ancestry
        if not self.capsule_engine:
            logger.error("Cannot build ancestry tree without capsule engine")
            return ancestry_tree

        # Queue for breadth-first search
        queue = [(capsule_id, 0)]  # (capsule_id, depth)
        visited = set()

        while queue:
            current_id, depth = queue.pop(0)

            # Skip if already visited or max depth reached
            if current_id in visited or (max_depth is not None and depth > max_depth):
                continue

            visited.add(current_id)

            # Get the capsule
            try:
                capsule = await self.capsule_engine.get_capsule(current_id)
                if not capsule:
                    logger.warning(f"Capsule {current_id} not found")
                    continue

                # Parse parent references from capsule content
                # In real implementation, this would use proper ancestry tracking in capsules
                # For now, we'll use a simplified approach assuming content is JSON with references
                parent_ids = []
                try:
                    content = json.loads(capsule.content)
                    parent_ids = content.get("parent_capsules", [])
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse JSON from capsule {current_id}")

                # Create node for this capsule
                node = AncestryNode(
                    capsule_id=current_id, parent_ids=parent_ids, depth=depth
                )
                ancestry_tree[current_id] = node

                # Add parents to queue
                for parent_id in parent_ids:
                    if parent_id not in visited:
                        queue.append((parent_id, depth + 1))

                    # Update child references in parent nodes
                    if parent_id in ancestry_tree:
                        if current_id not in ancestry_tree[parent_id].child_ids:
                            ancestry_tree[parent_id].child_ids.append(current_id)

            except Exception as e:
                logger.error(f"Error retrieving capsule {current_id}: {e}")

        # Cache the result
        self.ancestry_cache[capsule_id] = ancestry_tree

        # Save updated engine data
        self._save_engine_data()

        return ancestry_tree

    async def _build_and_validate_ancestry_tree(
        self, capsule_id: str, max_depth: int = None
    ) -> Dict[str, AncestryNode]:
        """Build ancestry tree with integrity validation to prevent manipulation."""

        # Build the ancestry tree
        ancestry_tree = await self.build_ancestry_tree(capsule_id, max_depth)

        if not ancestry_tree:
            return ancestry_tree

        # SECURITY: Calculate ancestry tree checksum for integrity validation
        current_checksum = self._calculate_ancestry_checksum(ancestry_tree)

        # SECURITY: Compare with stored checksum to detect manipulation
        stored_checksum = self.ancestry_checksums.get(capsule_id)

        if stored_checksum and stored_checksum != current_checksum:
            # Ancestry tree has been modified - potential attack
            logger.error(
                f"Ancestry tree integrity violation detected for capsule {capsule_id}: "
                f"expected {stored_checksum}, got {current_checksum}"
            )

            # Audit the security event
            from src.audit.events import audit_emitter

            audit_emitter.emit_security_event(
                "ancestry_tree_integrity_violation",
                {
                    "capsule_id": capsule_id,
                    "expected_checksum": stored_checksum,
                    "actual_checksum": current_checksum,
                    "attack_type": "ancestry_manipulation",
                },
            )

            # SECURITY: Rebuild ancestry tree from trusted source
            logger.info(
                f"Rebuilding ancestry tree for capsule {capsule_id} from trusted source"
            )
            self.ancestry_cache.pop(
                capsule_id, None
            )  # Clear potentially corrupted cache
            ancestry_tree = await self.build_ancestry_tree(capsule_id, max_depth)
            current_checksum = self._calculate_ancestry_checksum(ancestry_tree)

        # Store/update the checksum
        self.ancestry_checksums[capsule_id] = current_checksum

        return ancestry_tree

    def _calculate_ancestry_checksum(
        self, ancestry_tree: Dict[str, AncestryNode]
    ) -> str:
        """Calculate cryptographic checksum of ancestry tree for integrity validation."""

        import hashlib
        import json

        # Create a deterministic representation of the ancestry tree
        tree_data = {}
        for capsule_id, node in sorted(ancestry_tree.items()):
            tree_data[capsule_id] = {
                "parent_ids": sorted(node.parent_ids),
                "child_ids": sorted(node.child_ids),
                "depth": node.depth,
                "contribution_weight": node.contribution_weight,
            }

        # Calculate SHA-256 checksum
        tree_json = json.dumps(tree_data, sort_keys=True)
        checksum = hashlib.sha256(tree_json.encode()).hexdigest()

        return checksum

    def _validate_distribution_timing(self, capsule_id: str) -> bool:
        """Validate distribution timing to prevent rapid successive attacks."""

        last_distribution = self.last_distribution_time.get(capsule_id)

        if last_distribution:
            time_since_last = datetime.now(timezone.utc) - last_distribution

            if time_since_last < self.min_distribution_interval:
                logger.warning(
                    f"Distribution timing violation for capsule {capsule_id}: "
                    f"{time_since_last.total_seconds()}s < {self.min_distribution_interval.total_seconds()}s required"
                )
                return False

        return True

    async def _require_high_value_confirmation(
        self,
        capsule_id: str,
        value_amount: Decimal,
        currency: str,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Require confirmation for high-value distributions to prevent large-scale attacks."""

        confirmation_id = f"confirm_{capsule_id}_{uuid.uuid4().hex[:8]}"

        # SECURITY: Create confirmation requirement
        confirmation_data = {
            "confirmation_id": confirmation_id,
            "capsule_id": capsule_id,
            "value_amount": str(value_amount),
            "currency": currency,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "confirmed": False,
            "confirmation_delay_minutes": 60,  # 1-hour delay for high-value distributions
            "metadata": metadata or {},
        }

        # Store confirmation requirement
        self.distribution_confirmations[confirmation_id] = confirmation_data

        # SECURITY: For demonstration, auto-confirm after validation
        # In production, this would require human/governance approval
        if self._validate_high_value_distribution(capsule_id, value_amount, metadata):
            confirmation_data["confirmed"] = True
            confirmation_data["confirmed_at"] = datetime.now(timezone.utc).isoformat()
            confirmation_data["confirmation_method"] = "automated_validation"

            return {"confirmed": True, "confirmation_id": confirmation_id}
        else:
            return {
                "confirmed": False,
                "confirmation_id": confirmation_id,
                "reason": "High-value distribution requires manual approval",
            }

    def _validate_high_value_distribution(
        self, capsule_id: str, value_amount: Decimal, metadata: Dict[str, Any] = None
    ) -> bool:
        """Validate high-value distributions for automatic confirmation."""

        # SECURITY: Basic validation rules for high-value distributions

        # Check if capsule has sufficient historical activity
        historical_distributions = [
            dist
            for dist in self.distributions.values()
            if dist.source_capsule_id == capsule_id
        ]

        if (
            len(historical_distributions) < 5
        ):  # Require at least 5 previous distributions
            return False

        # Check average historical distribution size
        avg_historical_value = sum(
            dist.total_value
            for dist in historical_distributions[-10:]  # Last 10 distributions
        ) / min(10, len(historical_distributions))

        # SECURITY: Flag if current distribution is >10x historical average
        if value_amount > avg_historical_value * 10:
            logger.warning(
                f"High-value distribution anomaly for capsule {capsule_id}: "
                f"{value_amount} > 10x avg {avg_historical_value}"
            )
            return False

        # Additional validation can be added here
        return True

    def _linear_weights(self, depths: List[int], **kwargs) -> List[float]:
        """
        Calculate linear distribution weights.

        All generations get equal weight regardless of depth.

        Args:
            depths: List of depths in the ancestry tree

        Returns:
            List of weights corresponding to each depth
        """
        if not depths:
            return []
        return [1.0] * len(depths)

    def _exponential_weights(
        self, depths: List[int], base: float = 0.7, **kwargs
    ) -> List[float]:
        """
        Calculate exponential distribution weights.

        Recent generations get higher weight than earlier ones.

        Args:
            depths: List of depths in the ancestry tree
            base: Base for exponential calculation (0-1)

        Returns:
            List of weights corresponding to each depth
        """
        if not depths:
            return []

        max_depth = max(depths)
        weights = []

        for depth in depths:
            # More recent nodes (lower depth) get higher weight
            weight = pow(base, max_depth - depth)
            weights.append(weight)

        return weights

    def _logarithmic_weights(
        self, depths: List[int], factor: float = 1.0, **kwargs
    ) -> List[float]:
        """
        Calculate logarithmic distribution weights.

        Earlier generations get higher weight than recent ones.

        Args:
            depths: List of depths in the ancestry tree
            factor: Multiplication factor for weights

        Returns:
            List of weights corresponding to each depth
        """
        if not depths:
            return []

        max_depth = max(depths) + 1  # Add 1 to avoid log(0)
        weights = []

        for depth in depths:
            # Earlier nodes (higher depth) get higher weight
            adjusted_depth = max_depth - depth
            weight = factor * (1 + (adjusted_depth / max_depth))
            weights.append(weight)

        return weights

    def _custom_weights(
        self, depths: List[int], weights_map: Dict[int, float] = None, **kwargs
    ) -> List[float]:
        """
        Apply custom weights based on a provided mapping.

        Args:
            depths: List of depths in the ancestry tree
            weights_map: Dictionary mapping depths to weights

        Returns:
            List of weights corresponding to each depth
        """
        if not depths or not weights_map:
            return self._linear_weights(depths)

        weights = []

        for depth in depths:
            weight = weights_map.get(depth, 1.0)
            weights.append(weight)

        return weights

    async def distribute_value(
        self,
        capsule_id: str,
        value_amount: Union[Decimal, float, str],
        currency: str = "USD",
        distribution_model: DistributionModel = DistributionModel.LINEAR,
        max_depth: int = None,
        custom_weights: Dict[str, float] = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Distribute value across a capsule's ancestry chain.

        Args:
            capsule_id: ID of the capsule generating value
            value_amount: Total value to distribute
            currency: Currency code (default: USD)
            distribution_model: Model for value distribution
            max_depth: Maximum ancestry depth to consider
            custom_weights: Custom weights for specific capsules
            metadata: Optional metadata about this distribution

        Returns:
            The ID of the distribution record
        """
        # SECURITY: Implement atomic state locking to prevent flash loan attacks
        distribution_key = f"distribution_{capsule_id}"
        async with self._get_atomic_lock(distribution_key):
            # Convert value_amount to Decimal if needed
            if isinstance(value_amount, float) or isinstance(value_amount, str):
                value_amount = Decimal(str(value_amount))

            # SECURITY: Rate limiting check
            if not self._check_distribution_rate_limit(capsule_id):
                raise ValueError(
                    f"Distribution rate limit exceeded for capsule {capsule_id}"
                )

            # SECURITY: Validate distribution timing to prevent rapid attacks
            if not self._validate_distribution_timing(capsule_id):
                raise ValueError(
                    f"Distribution too soon after previous distribution for capsule {capsule_id}"
                )

            # SECURITY: High-value distribution confirmation
            if value_amount >= self.high_value_threshold:
                confirmation = await self._require_high_value_confirmation(
                    capsule_id, value_amount, currency, metadata
                )
                if not confirmation["confirmed"]:
                    raise ValueError(
                        f"High-value distribution requires confirmation: {confirmation['reason']}"
                    )

            # Build and validate the ancestry tree with integrity checks
            ancestry_tree = await self._build_and_validate_ancestry_tree(
                capsule_id, max_depth
            )

        if not ancestry_tree:
            logger.warning(f"No ancestry tree found for capsule {capsule_id}")
            return None

        # Prepare for distribution
        distribution_id = str(uuid.uuid4())
        distribution = ValueDistribution(
            distribution_id=distribution_id,
            source_capsule_id=capsule_id,
            total_value=value_amount,
            currency=currency,
            model=distribution_model,
            metadata=metadata or {},
        )

        # Get unique depths and sort them
        depths = sorted({node.depth for node in ancestry_tree.values()})

        # Calculate weights based on distribution model
        weight_func = self.model_weights.get(distribution_model, self._linear_weights)
        depth_weights = weight_func(depths, base=0.7, factor=1.5)

        # Create mapping of depth to weight
        depth_to_weight = dict(zip(depths, depth_weights))

        # Calculate total weight
        total_weight = sum(
            depth_to_weight.get(node.depth, 1.0)
            * (custom_weights.get(node.capsule_id, 1.0) if custom_weights else 1.0)
            for node in ancestry_tree.values()
        )

        if total_weight <= 0:
            logger.warning(
                "Total weight is zero or negative. Using equal distribution."
            )
            total_weight = len(ancestry_tree)

            # Distribute value proportionally
            for capsule_node_id, node in ancestry_tree.items():
                # Calculate the weight for this node
                node_weight = depth_to_weight.get(node.depth, 1.0)

                # Apply custom weights if provided
                if custom_weights and capsule_node_id in custom_weights:
                    node_weight *= custom_weights[capsule_node_id]

                # Calculate the value share
                share = (node_weight / total_weight) * value_amount

                # Record the distribution
                distribution.distributions[capsule_node_id] = share

            # SECURITY: Record distribution timing for rate limiting
            self.last_distribution_time[capsule_id] = datetime.now(timezone.utc)
            self._record_distribution_request(capsule_id)

            # Save the distribution
            self.distributions[distribution_id] = distribution

            # Save updated engine data
            self._save_engine_data()

            logger.info(
                f"Distributed {value_amount} {currency} across {len(ancestry_tree)} capsules"
            )
            return distribution_id

    async def register_with_attribution_fund(
        self, distribution_id: str
    ) -> Dict[str, Any]:
        """
        Register a distribution with the Common Attribution Fund.

        Args:
            distribution_id: ID of the distribution to register

        Returns:
            Dictionary with registration results
        """
        if not self.attribution_fund:
            logger.error("No attribution fund configured")
            return {"registered": False, "reason": "No attribution fund configured"}

        distribution = self.distributions.get(distribution_id)
        if not distribution:
            logger.error(f"Distribution {distribution_id} not found")
            return {"registered": False, "reason": "Distribution not found"}

        results = {
            "registered": True,
            "distribution_id": distribution_id,
            "contributions": [],
            "attributions": [],
        }

        try:
            # Register each capsule in the distribution as a contribution
            for capsule_id, amount in distribution.distributions.items():
                # Determine contribution type based on relationship to source
                ancestry_tree = await self.build_ancestry_tree(
                    distribution.source_capsule_id
                )
                if capsule_id == distribution.source_capsule_id:
                    contrib_type = ContributionType.DIRECT
                elif capsule_id in ancestry_tree:
                    node = ancestry_tree.get(capsule_id)
                    if node and node.depth == 1:
                        contrib_type = ContributionType.DERIVATIVE
                    else:
                        contrib_type = ContributionType.COLLECTIVE
                else:
                    contrib_type = ContributionType.REMIX

                # Get the capsule to extract contributor info
                contributor_id = capsule_id  # Default to capsule ID
                if self.capsule_engine:
                    try:
                        capsule = await self.capsule_engine.get_capsule(capsule_id)
                        if capsule:
                            # In a real implementation, extract author/contributor info
                            # from capsule metadata or content
                            try:
                                content = json.loads(capsule.content)
                                if "author" in content:
                                    contributor_id = content["author"]
                            except json.JSONDecodeError:
                                pass
                    except Exception as e:
                        logger.warning(f"Error getting capsule {capsule_id}: {e}")

                # Register contribution
                contribution_id = await self.attribution_fund.register_contribution(
                    contributor_id=contributor_id,
                    contribution_type=contrib_type,
                    capsule_ids=[capsule_id],
                    weight=float(amount) / float(distribution.total_value),
                    description=f"Contribution from capsule dividend distribution {distribution_id}",
                )

                results["contributions"].append(
                    {
                        "contribution_id": contribution_id,
                        "contributor_id": contributor_id,
                        "capsule_id": capsule_id,
                        "amount": str(amount),
                        "type": contrib_type.name,
                    }
                )

                # Create attribution for this contribution
                attribution_id = await self.attribution_fund.attribute_value(
                    source_capsule_id=distribution.source_capsule_id,
                    contribution_ids=[contribution_id],
                    value_amount=amount,
                    currency=distribution.currency,
                    metadata={"distribution_id": distribution_id},
                )

                results["attributions"].append(
                    {
                        "attribution_id": attribution_id,
                        "contribution_id": contribution_id,
                        "amount": str(amount),
                    }
                )

        except Exception as e:
            logger.error(f"Error registering with attribution fund: {e}")
            return {"registered": False, "reason": str(e), "partial_results": results}

        return results

    async def get_capsule_value(self, capsule_id: str) -> Dict[str, Any]:
        """
        Get the total value attributed to a capsule.

        Args:
            capsule_id: ID of the capsule

        Returns:
            Dictionary with value information
        """
        total_value = Decimal("0.0")
        distributions_count = 0
        distribution_ids = []
        currencies = set()

        for distribution in self.distributions.values():
            if capsule_id in distribution.distributions:
                value = distribution.distributions[capsule_id]
                total_value += value
                distributions_count += 1
                distribution_ids.append(distribution.distribution_id)
                currencies.add(distribution.currency)

        return {
            "capsule_id": capsule_id,
            "total_value": str(total_value),
            "distributions_count": distributions_count,
            "distribution_ids": distribution_ids,
            "currencies": list(currencies),
        }

    async def get_distribution(
        self, distribution_id: str
    ) -> Optional[ValueDistribution]:
        """Get a specific value distribution by ID."""
        return self.distributions.get(distribution_id)

    def _check_distribution_rate_limit(self, capsule_id: str) -> bool:
        """Check if distribution rate limit is exceeded."""
        current_time = datetime.now(timezone.utc)
        hour_ago = current_time - timedelta(hours=1)

        # Clean old requests
        self._distribution_requests[capsule_id] = [
            timestamp
            for timestamp in self._distribution_requests[capsule_id]
            if timestamp > hour_ago
        ]

        # Check rate limit
        return (
            len(self._distribution_requests[capsule_id])
            < self._max_distributions_per_hour
        )

    def _record_distribution_request(self, capsule_id: str):
        """Record a distribution request for rate limiting."""
        self._distribution_requests[capsule_id].append(datetime.now(timezone.utc))

    async def _get_atomic_lock(self, key: str) -> asyncio.Lock:
        """Get or create an atomic lock for a specific key."""
        if key not in self._distribution_locks:
            self._distribution_locks[key] = asyncio.Lock()
        return self._distribution_locks[key]

    async def _take_state_snapshot(self, capsule_id: str) -> Dict:
        """Take a state snapshot before distribution for rollback capability."""
        snapshot = {
            "capsule_id": capsule_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "distributions_count": len(self.distributions),
            "last_distribution_time": self._distribution_timestamps.get(capsule_id),
            "ancestry_checksum": await self._calculate_ancestry_checksum(capsule_id),
        }

        self._state_snapshots[capsule_id] = snapshot
        return snapshot

    async def _calculate_ancestry_checksum(self, capsule_id: str) -> str:
        """Calculate checksum of ancestry tree for integrity validation."""
        try:
            ancestry_tree = await self.build_ancestry_tree(capsule_id)
            if not ancestry_tree:
                return "empty"

            # Create deterministic string representation
            sorted_nodes = sorted(ancestry_tree.keys())
            checksum_data = ""
            for node_id in sorted_nodes:
                node = ancestry_tree[node_id]
                checksum_data += (
                    f"{node_id}:{node.depth}:{','.join(sorted(node.parent_ids))}"
                )

            return hashlib.sha256(checksum_data.encode()).hexdigest()[:16]
        except Exception as e:
            logger.warning(
                f"Failed to calculate ancestry checksum for {capsule_id}: {e}"
            )
            return "error"

    def _validate_ancestry_tree_integrity(
        self, ancestry_tree: Dict[str, AncestryNode], capsule_id: str
    ) -> bool:
        """Validate ancestry tree integrity to prevent manipulation."""
        if not ancestry_tree:
            return False

        # SECURITY: Verify tree structure consistency
        for node_id, node in ancestry_tree.items():
            # Check parent-child relationships are bidirectional
            for parent_id in node.parent_ids:
                if parent_id in ancestry_tree:
                    parent_node = ancestry_tree[parent_id]
                    if node_id not in parent_node.child_ids:
                        logger.error(
                            f"Ancestry tree integrity violation: {node_id} not in {parent_id} children"
                        )
                        return False

            # Check depth consistency
            if node.depth < 0:
                logger.error(
                    f"Ancestry tree integrity violation: negative depth for {node_id}"
                )
                return False

        # SECURITY: Verify source capsule is at depth 0
        if capsule_id not in ancestry_tree or ancestry_tree[capsule_id].depth != 0:
            logger.error(
                f"Ancestry tree integrity violation: source capsule {capsule_id} not at depth 0"
            )
            return False

        return True

    def _validate_distribution_integrity(self, distribution: ValueDistribution) -> bool:
        """Validate distribution integrity before execution."""
        if not distribution.allocations:
            return False

        # SECURITY: Verify total allocation equals total value
        total_allocated = sum(alloc.amount for alloc in distribution.allocations)
        tolerance = Decimal("0.01")  # 1 cent tolerance for rounding

        if abs(total_allocated - distribution.total_value) > tolerance:
            logger.error(
                f"Distribution integrity violation: allocated {total_allocated} != total {distribution.total_value}"
            )
            return False

        # SECURITY: Verify no negative allocations
        for alloc in distribution.allocations:
            if alloc.amount < 0:
                logger.error(
                    f"Distribution integrity violation: negative allocation {alloc.amount}"
                )
                return False

        return True

    async def _rollback_state(self, capsule_id: str, snapshot: Dict):
        """Rollback state changes in case of distribution failure."""
        try:
            # Restore distribution timestamp
            if (
                "last_distribution_time" in snapshot
                and snapshot["last_distribution_time"]
            ):
                self._distribution_timestamps[capsule_id] = snapshot[
                    "last_distribution_time"
                ]
            elif capsule_id in self._distribution_timestamps:
                del self._distribution_timestamps[capsule_id]

            # Remove any distributions created during failed transaction
            distributions_to_remove = []
            for dist_id, distribution in self.distributions.items():
                if (
                    distribution.source_capsule_id == capsule_id
                    and distribution.created_at
                    >= datetime.fromisoformat(snapshot["timestamp"])
                ):
                    distributions_to_remove.append(dist_id)

            for dist_id in distributions_to_remove:
                del self.distributions[dist_id]

            logger.info(
                f"Rolled back state for capsule {capsule_id}, removed {len(distributions_to_remove)} distributions"
            )

        except Exception as e:
            logger.error(f"Failed to rollback state for capsule {capsule_id}: {e}")

    async def _build_and_validate_ancestry_tree(
        self, capsule_id: str, max_depth: int = None
    ) -> Dict[str, AncestryNode]:
        """Build and validate ancestry tree with enhanced security."""
        # Check cache first
        cache_key = f"{capsule_id}:{max_depth}"
        if cache_key in self.ancestry_cache:
            cached_tree = self.ancestry_cache[cache_key]

            # SECURITY: Verify cached tree is still valid
            current_checksum = await self._calculate_ancestry_checksum(capsule_id)
            if current_checksum == self.ancestry_checksums.get(capsule_id):
                return cached_tree
            else:
                # Cache invalidated, remove it
                del self.ancestry_cache[cache_key]

        # Build fresh ancestry tree
        ancestry_tree = await self.build_ancestry_tree(capsule_id, max_depth)

        if ancestry_tree:
            # Cache the tree and its checksum
            self.ancestry_cache[cache_key] = ancestry_tree
            self.ancestry_checksums[
                capsule_id
            ] = await self._calculate_ancestry_checksum(capsule_id)

        return ancestry_tree


async def demo_capsule_dividend_engine():
    """Demonstrate the Capsule Dividend Engine functionality."""
    # Create a temporary directory for the engine
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock capsule engine (for demo purposes only)
        class MockCapsuleEngine:
            async def get_capsule(self, capsule_id):
                """Return a mock capsule."""
                from collections import namedtuple

                MockCapsule = namedtuple("MockCapsule", ["id", "content", "status"])

                content_map = {
                    "capsule-root": json.dumps(
                        {
                            "type": "final_output",
                            "parent_capsules": ["capsule-parent1", "capsule-parent2"],
                            "author": "user-alice",
                        }
                    ),
                    "capsule-parent1": json.dumps(
                        {
                            "type": "intermediate_result",
                            "parent_capsules": ["capsule-grandparent"],
                            "author": "user-bob",
                        }
                    ),
                    "capsule-parent2": json.dumps(
                        {
                            "type": "intermediate_result",
                            "parent_capsules": ["capsule-grandparent"],
                            "author": "user-charlie",
                        }
                    ),
                    "capsule-grandparent": json.dumps(
                        {
                            "type": "source_material",
                            "parent_capsules": [],
                            "author": "user-david",
                        }
                    ),
                }

                if capsule_id in content_map:
                    return MockCapsule(
                        id=capsule_id,
                        content=content_map[capsule_id],
                        status=CapsuleStatus.VERIFIED,
                    )
                return None

        # Create mock attribution fund
        from src.integrations.economic.common_attribution_fund import (
            CommonAttributionFund,
        )

        attribution_fund = CommonAttributionFund(
            fund_id="demo-fund", registry_path=tmpdir
        )

        # Create the dividend engine
        engine = CapsuleDividendEngine(
            engine_id="demo-engine",
            capsule_engine=MockCapsuleEngine(),
            attribution_fund=attribution_fund,
            registry_path=tmpdir,
        )

        print(f"Created Capsule Dividend Engine with ID: {engine.engine_id}")

        # Build ancestry tree for a capsule
        ancestry = await engine.build_ancestry_tree("capsule-root")

        print(f"\nBuilt ancestry tree with {len(ancestry)} nodes:")
        for capsule_id, node in ancestry.items():
            print(f"  {capsule_id}: depth={node.depth}, parents={node.parent_ids}")

        # Distribute value with different models
        print("\nDistributing value with different models:")

        # Linear model (equal distribution)
        linear_dist = await engine.distribute_value(
            capsule_id="capsule-root",
            value_amount="100.00",
            distribution_model=DistributionModel.LINEAR,
        )
        linear_distribution = await engine.get_distribution(linear_dist)
        print("\nLinear distribution:")
        for capsule_id, amount in linear_distribution.distributions.items():
            print(f"  {capsule_id}: {amount}")

        # Exponential model (recent generations get more)
        exp_dist = await engine.distribute_value(
            capsule_id="capsule-root",
            value_amount="100.00",
            distribution_model=DistributionModel.EXPONENTIAL,
        )
        exp_distribution = await engine.get_distribution(exp_dist)
        print("\nExponential distribution:")
        for capsule_id, amount in exp_distribution.distributions.items():
            print(f"  {capsule_id}: {amount}")

        # Logarithmic model (earlier generations get more)
        log_dist = await engine.distribute_value(
            capsule_id="capsule-root",
            value_amount="100.00",
            distribution_model=DistributionModel.LOGARITHMIC,
        )
        log_distribution = await engine.get_distribution(log_dist)
        print("\nLogarithmic distribution:")
        for capsule_id, amount in log_distribution.distributions.items():
            print(f"  {capsule_id}: {amount}")

        # Register with attribution fund
        print("\nRegistering with attribution fund...")
        registration = await engine.register_with_attribution_fund(linear_dist)

        print(
            f"Registered {len(registration['contributions'])} contributions and {len(registration['attributions'])} attributions"
        )

        # Check capsule value
        for capsule_id in ancestry:
            value_info = await engine.get_capsule_value(capsule_id)
            print(f"\nCapsule {capsule_id} value: {value_info['total_value']}")


if __name__ == "__main__":
    import asyncio

    # Run the demo
    asyncio.run(demo_capsule_dividend_engine())
