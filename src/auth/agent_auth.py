"""
Agent Authentication & Authorization System

Provides identity management and access control for AI agents operating
autonomously within the UATP system.

Key Concepts:
- Agent Identity: Each AI agent has a unique identity separate from its human owner
- Agent Credentials: Agents authenticate using agent-specific JWT tokens
- Agent Authorization: RBAC system with agent-specific permissions
- Human Oversight: Agents act on behalf of humans with delegated authority
- Revocation: Human owners can revoke agent authority at any time

Usage:
    from src.auth.agent_auth import AgentAuthManager

    # Register new agent
    agent_manager = AgentAuthManager()
    agent = await agent_manager.register_agent(
        human_owner_id="user_123",
        agent_name="ResearchAssistant",
        capabilities=["read_capsules", "create_capsules"]
    )

    # Authenticate agent
    is_valid = await agent_manager.verify_agent_token(agent_token)

    # Check agent permissions
    can_access = await agent_manager.check_agent_permission(
        agent_id="agent_abc",
        resource="capsule:cap_123",
        action="read"
    )
"""

import secrets
import jwt
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict, field
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentIdentity:
    """Identity information for an AI agent"""

    agent_id: str
    agent_name: str
    agent_type: str  # 'assistant', 'autonomous', 'research', 'creative', etc.
    human_owner_id: str
    human_owner_email: str
    created_at: str  # ISO 8601
    capabilities: List[str]  # List of allowed actions
    status: str  # 'active', 'suspended', 'revoked'
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class AgentCredential:
    """Credentials for agent authentication"""

    agent_id: str
    credential_id: str
    credential_type: str  # 'jwt_token', 'api_key'
    credential_hash: str
    created_at: str
    expires_at: Optional[str]
    last_used_at: Optional[str] = None
    revoked: bool = False
    revoked_at: Optional[str] = None


@dataclass
class AgentSession:
    """Active agent session"""

    session_id: str
    agent_id: str
    human_owner_id: str
    started_at: str
    expires_at: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    actions_count: int = 0
    last_activity_at: Optional[str] = None


class AgentAuthManager:
    """
    Manages agent authentication, authorization, and identity lifecycle.

    This system provides:
    1. Agent registration and identity management
    2. Agent credential issuance (JWT tokens, API keys)
    3. Agent authentication and session management
    4. Agent authorization (RBAC)
    5. Human oversight and revocation
    """

    def __init__(
        self,
        storage_path: str = "security/agents",
        jwt_secret: Optional[str] = None,
        jwt_algorithm: str = "HS256",
    ):
        """
        Initialize agent auth manager.

        Args:
            storage_path: Directory to store agent data
            jwt_secret: Secret for JWT signing (generated if None)
            jwt_algorithm: JWT algorithm (default: HS256)
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # JWT configuration
        self.jwt_secret = jwt_secret or secrets.token_hex(32)
        self.jwt_algorithm = jwt_algorithm

        # In-memory registries (loaded from storage)
        self.agents: Dict[str, AgentIdentity] = {}
        self.credentials: Dict[str, AgentCredential] = {}
        self.sessions: Dict[str, AgentSession] = {}

        # Load existing data
        self._load_agents()
        self._load_credentials()

    def _load_agents(self):
        """Load agent identities from storage"""
        agents_file = self.storage_path / "agents.jsonl"

        if not agents_file.exists():
            return

        with open(agents_file, "r") as f:
            for line in f:
                agent_dict = json.loads(line)
                agent = AgentIdentity(**agent_dict)
                self.agents[agent.agent_id] = agent

    def _load_credentials(self):
        """Load agent credentials from storage"""
        creds_file = self.storage_path / "credentials.jsonl"

        if not creds_file.exists():
            return

        with open(creds_file, "r") as f:
            for line in f:
                cred_dict = json.loads(line)
                cred = AgentCredential(**cred_dict)
                self.credentials[cred.credential_id] = cred

    def _save_agent(self, agent: AgentIdentity):
        """Save agent identity to storage"""
        agents_file = self.storage_path / "agents.jsonl"

        with open(agents_file, "a") as f:
            f.write(json.dumps(asdict(agent)) + "\n")

    def _save_credential(self, credential: AgentCredential):
        """Save agent credential to storage"""
        creds_file = self.storage_path / "credentials.jsonl"

        with open(creds_file, "a") as f:
            f.write(json.dumps(asdict(credential)) + "\n")

    async def register_agent(
        self,
        human_owner_id: str,
        human_owner_email: str,
        agent_name: str,
        agent_type: str = "assistant",
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ) -> tuple[AgentIdentity, str]:
        """
        Register a new AI agent.

        Args:
            human_owner_id: ID of human who owns this agent
            human_owner_email: Email of human owner
            agent_name: Display name for agent
            agent_type: Type of agent (assistant, autonomous, etc.)
            capabilities: List of allowed actions
            metadata: Additional agent metadata

        Returns:
            (AgentIdentity, agent_token) tuple
        """
        # Generate unique agent ID
        agent_id = f"agent_{secrets.token_hex(16)}"

        # Default capabilities
        if capabilities is None:
            capabilities = ["read_capsules", "create_capsules", "read_own_data"]

        # Create agent identity
        agent = AgentIdentity(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type=agent_type,
            human_owner_id=human_owner_id,
            human_owner_email=human_owner_email,
            created_at=datetime.now(timezone.utc).isoformat(),
            capabilities=capabilities,
            status="active",
            metadata=metadata or {},
        )

        # Save agent
        self.agents[agent_id] = agent
        self._save_agent(agent)

        # Generate agent token
        agent_token = await self.issue_agent_token(
            agent_id=agent_id, expires_in_hours=24 * 365  # 1 year
        )

        logger.info(
            f"Registered new agent: {agent_id} ({agent_name}) for owner {human_owner_id}"
        )

        # Emit audit event
        try:
            from src.audit.events import audit_emitter

            audit_emitter.emit_security_event(
                event_name="agent_registered",
                metadata={
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "human_owner_id": human_owner_id,
                    "capabilities": capabilities,
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit audit event: {e}")

        return agent, agent_token

    async def issue_agent_token(self, agent_id: str, expires_in_hours: int = 24) -> str:
        """
        Issue JWT token for agent authentication.

        Args:
            agent_id: Agent ID
            expires_in_hours: Token expiration (default: 24 hours)

        Returns:
            JWT token string
        """
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        if agent.status != "active":
            raise ValueError(f"Agent is not active: {agent.status}")

        # Create credential
        credential_id = f"cred_{secrets.token_hex(16)}"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

        # JWT payload
        payload = {
            "agent_id": agent_id,
            "credential_id": credential_id,
            "human_owner_id": agent.human_owner_id,
            "agent_name": agent.agent_name,
            "agent_type": agent.agent_type,
            "capabilities": agent.capabilities,
            "iat": datetime.now(timezone.utc).timestamp(),
            "exp": expires_at.timestamp(),
            "type": "agent_token",
        }

        # Sign token
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

        # Store credential
        credential = AgentCredential(
            agent_id=agent_id,
            credential_id=credential_id,
            credential_type="jwt_token",
            credential_hash=self._hash_token(token),
            created_at=datetime.now(timezone.utc).isoformat(),
            expires_at=expires_at.isoformat(),
            revoked=False,
        )

        self.credentials[credential_id] = credential
        self._save_credential(credential)

        logger.info(
            f"Issued token for agent: {agent_id} (expires in {expires_in_hours}h)"
        )

        return token

    def _hash_token(self, token: str) -> str:
        """Hash token for storage"""
        import hashlib

        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    async def verify_agent_token(self, token: str) -> Optional[Dict]:
        """
        Verify agent JWT token.

        Args:
            token: JWT token string

        Returns:
            Token payload if valid, None otherwise
        """
        try:
            # Decode and verify token
            payload = jwt.decode(
                token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )

            # Check token type
            if payload.get("type") != "agent_token":
                logger.warning("Invalid token type")
                return None

            # Check agent exists and is active
            agent_id = payload.get("agent_id")
            agent = self.agents.get(agent_id)

            if not agent:
                logger.warning(f"Agent not found: {agent_id}")
                return None

            if agent.status != "active":
                logger.warning(f"Agent is not active: {agent.status}")
                return None

            # Check credential not revoked
            credential_id = payload.get("credential_id")
            credential = self.credentials.get(credential_id)

            if credential and credential.revoked:
                logger.warning(f"Credential revoked: {credential_id}")
                return None

            # Update last used
            if credential:
                credential.last_used_at = datetime.now(timezone.utc).isoformat()

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    async def check_agent_permission(
        self, agent_id: str, action: str, resource: Optional[str] = None
    ) -> bool:
        """
        Check if agent has permission for action.

        Args:
            agent_id: Agent ID
            action: Action to check (e.g., "read_capsules", "create_policy")
            resource: Optional specific resource ID

        Returns:
            True if permitted, False otherwise
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return False

        if agent.status != "active":
            return False

        # Check if action in capabilities
        if action not in agent.capabilities:
            # Check for wildcard permissions
            if (
                "*" not in agent.capabilities
                and f"{action.split('_')[0]}_*" not in agent.capabilities
            ):
                return False

        # Resource-level checks (if needed)
        if resource:
            # Check if agent owns resource
            # This would integrate with resource ownership system
            pass

        return True

    async def revoke_agent(
        self, agent_id: str, human_owner_id: str, reason: str = "Manual revocation"
    ) -> bool:
        """
        Revoke agent access (can only be done by owner).

        Args:
            agent_id: Agent ID to revoke
            human_owner_id: ID of human requesting revocation (must be owner)
            reason: Reason for revocation

        Returns:
            True if revoked, False if not authorized
        """
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        # Verify ownership
        if agent.human_owner_id != human_owner_id:
            logger.warning(
                f"Unauthorized revocation attempt: {human_owner_id} tried to revoke {agent_id}"
            )
            return False

        # Update agent status
        agent.status = "revoked"

        # Revoke all credentials
        for cred in self.credentials.values():
            if cred.agent_id == agent_id and not cred.revoked:
                cred.revoked = True
                cred.revoked_at = datetime.now(timezone.utc).isoformat()

        logger.info(
            f"Revoked agent: {agent_id} by owner {human_owner_id}. Reason: {reason}"
        )

        # Emit audit event
        try:
            from src.audit.events import audit_emitter

            audit_emitter.emit_security_event(
                event_name="agent_revoked",
                metadata={
                    "agent_id": agent_id,
                    "human_owner_id": human_owner_id,
                    "reason": reason,
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit audit event: {e}")

        return True

    def get_agent(self, agent_id: str) -> Optional[AgentIdentity]:
        """Get agent by ID"""
        return self.agents.get(agent_id)

    def list_agents(
        self, human_owner_id: Optional[str] = None, status: Optional[str] = None
    ) -> List[AgentIdentity]:
        """
        List agents with optional filtering.

        Args:
            human_owner_id: Filter by owner
            status: Filter by status

        Returns:
            List of agents
        """
        agents = list(self.agents.values())

        if human_owner_id:
            agents = [a for a in agents if a.human_owner_id == human_owner_id]

        if status:
            agents = [a for a in agents if a.status == status]

        return agents


# Global agent auth manager
agent_auth_manager = AgentAuthManager()
