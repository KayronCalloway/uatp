"""
Enterprise Single Sign-On (SSO) Integration System
Supports SAML, OAuth2, OpenID Connect, and Active Directory integration
"""

import base64
import json
import logging
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp
import jwt
from cryptography.x509 import load_pem_x509_certificate

from ..attribution.cross_conversation_tracker import CrossConversationTracker
from ..capsules.specialized_capsules import create_specialized_capsule
from ..engine.capsule_engine import CapsuleEngine

logger = logging.getLogger(__name__)


class SSOProtocol(Enum):
    """Supported SSO protocols"""

    SAML2 = "saml2"
    OAUTH2 = "oauth2"
    OPENID_CONNECT = "openid_connect"
    ACTIVE_DIRECTORY = "active_directory"
    LDAP = "ldap"
    KERBEROS = "kerberos"


class AuthenticationMethod(Enum):
    """Authentication methods"""

    PASSWORD = "password"
    CERTIFICATE = "certificate"
    MULTI_FACTOR = "multi_factor"
    BIOMETRIC = "biometric"
    HARDWARE_TOKEN = "hardware_token"


class UserRole(Enum):
    """User roles in enterprise system"""

    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    GUEST = "guest"
    SERVICE_ACCOUNT = "service_account"


@dataclass
class SSOConfig:
    """Configuration for SSO provider"""

    provider_id: str
    provider_name: str
    protocol: SSOProtocol
    endpoint_url: str
    client_id: str
    client_secret: str
    certificate_path: Optional[str] = None
    metadata_url: Optional[str] = None
    issuer: Optional[str] = None
    audience: Optional[str] = None
    scopes: List[str] = None
    claims_mapping: Dict[str, str] = None
    additional_parameters: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UserProfile:
    """User profile from SSO provider"""

    user_id: str
    email: str
    name: str
    roles: List[UserRole]
    groups: List[str]
    department: Optional[str] = None
    title: Optional[str] = None
    manager: Optional[str] = None
    attributes: Dict[str, Any] = None
    session_id: Optional[str] = None
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Convert datetime to ISO string
        if self.expires_at:
            data["expires_at"] = self.expires_at.isoformat()
        # Convert enums to strings
        data["roles"] = [role.value for role in self.roles]
        return data


@dataclass
class AuthenticationResult:
    """Result of authentication process"""

    success: bool
    user_profile: Optional[UserProfile] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    error_message: Optional[str] = None
    provider_id: Optional[str] = None
    authentication_method: Optional[AuthenticationMethod] = None
    session_duration: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.user_profile:
            data["user_profile"] = self.user_profile.to_dict()
        if self.authentication_method:
            data["authentication_method"] = self.authentication_method.value
        return data


class SAMLProvider:
    """SAML 2.0 authentication provider"""

    def __init__(self, config: SSOConfig):
        self.config = config
        self.metadata = None
        self.certificate = None

    async def initialize(self) -> bool:
        """Initialize SAML provider"""
        try:
            # Load SAML metadata
            if self.config.metadata_url:
                await self._load_metadata()

            # Load signing certificate
            if self.config.certificate_path:
                await self._load_certificate()

            return True
        except Exception as e:
            logger.error(f"Failed to initialize SAML provider: {str(e)}")
            return False

    async def authenticate(self, saml_response: str) -> AuthenticationResult:
        """Authenticate user with SAML response"""
        try:
            # Decode SAML response
            decoded_response = base64.b64decode(saml_response)

            # Parse SAML XML
            root = ET.fromstring(decoded_response)

            # Extract user attributes
            user_attributes = self._extract_saml_attributes(root)

            # Create user profile
            user_profile = UserProfile(
                user_id=user_attributes.get("user_id", ""),
                email=user_attributes.get("email", ""),
                name=user_attributes.get("name", ""),
                roles=[
                    UserRole(role) for role in user_attributes.get("roles", ["user"])
                ],
                groups=user_attributes.get("groups", []),
                department=user_attributes.get("department"),
                title=user_attributes.get("title"),
                attributes=user_attributes,
                expires_at=datetime.now() + timedelta(hours=8),
            )

            return AuthenticationResult(
                success=True,
                user_profile=user_profile,
                provider_id=self.config.provider_id,
                authentication_method=AuthenticationMethod.PASSWORD,
                session_duration=28800,  # 8 hours
            )

        except Exception as e:
            logger.error(f"SAML authentication failed: {str(e)}")
            return AuthenticationResult(
                success=False, error_message=str(e), provider_id=self.config.provider_id
            )

    async def _load_metadata(self):
        """Load SAML metadata from URL"""
        async with aiohttp.ClientSession() as session:
            async with session.get(self.config.metadata_url) as response:
                if response.status == 200:
                    self.metadata = await response.text()
                else:
                    raise Exception(f"Failed to load SAML metadata: {response.status}")

    async def _load_certificate(self):
        """Load SAML signing certificate"""
        with open(self.config.certificate_path, "rb") as cert_file:
            self.certificate = load_pem_x509_certificate(cert_file.read())

    def _extract_saml_attributes(self, saml_root: ET.Element) -> Dict[str, Any]:
        """Extract user attributes from SAML response"""
        attributes = {}

        # Mock attribute extraction - in reality, this would parse the SAML XML
        attributes = {
            "user_id": "user123",
            "email": "user@company.com",
            "name": "John Doe",
            "roles": ["user"],
            "groups": ["Engineering", "UATP_Users"],
            "department": "Engineering",
            "title": "Software Engineer",
        }

        return attributes


class OAuth2Provider:
    """OAuth 2.0 / OpenID Connect provider"""

    def __init__(self, config: SSOConfig):
        self.config = config
        self.discovery_document = None
        self.jwks = None

    async def initialize(self) -> bool:
        """Initialize OAuth2 provider"""
        try:
            # Load OpenID Connect discovery document
            if self.config.protocol == SSOProtocol.OPENID_CONNECT:
                await self._load_discovery_document()
                await self._load_jwks()

            return True
        except Exception as e:
            logger.error(f"Failed to initialize OAuth2 provider: {str(e)}")
            return False

    async def authenticate(
        self, authorization_code: str, redirect_uri: str
    ) -> AuthenticationResult:
        """Authenticate user with OAuth2 authorization code"""
        try:
            # Exchange authorization code for tokens
            tokens = await self._exchange_code_for_tokens(
                authorization_code, redirect_uri
            )

            # Get user profile
            user_profile = await self._get_user_profile(tokens["access_token"])

            # Validate ID token if present
            if "id_token" in tokens:
                id_token_claims = await self._validate_id_token(tokens["id_token"])
                user_profile.attributes.update(id_token_claims)

            return AuthenticationResult(
                success=True,
                user_profile=user_profile,
                access_token=tokens["access_token"],
                refresh_token=tokens.get("refresh_token"),
                id_token=tokens.get("id_token"),
                provider_id=self.config.provider_id,
                authentication_method=AuthenticationMethod.PASSWORD,
                session_duration=tokens.get("expires_in", 3600),
            )

        except Exception as e:
            logger.error(f"OAuth2 authentication failed: {str(e)}")
            return AuthenticationResult(
                success=False, error_message=str(e), provider_id=self.config.provider_id
            )

    async def _load_discovery_document(self):
        """Load OpenID Connect discovery document"""
        discovery_url = f"{self.config.endpoint_url}/.well-known/openid_configuration"

        async with aiohttp.ClientSession() as session:
            async with session.get(discovery_url) as response:
                if response.status == 200:
                    self.discovery_document = await response.json()
                else:
                    raise Exception(
                        f"Failed to load discovery document: {response.status}"
                    )

    async def _load_jwks(self):
        """Load JSON Web Key Set"""
        jwks_uri = self.discovery_document.get("jwks_uri")

        if jwks_uri:
            async with aiohttp.ClientSession() as session:
                async with session.get(jwks_uri) as response:
                    if response.status == 200:
                        self.jwks = await response.json()
                    else:
                        raise Exception(f"Failed to load JWKS: {response.status}")

    async def _exchange_code_for_tokens(
        self, code: str, redirect_uri: str
    ) -> Dict[str, Any]:
        """Exchange authorization code for access tokens"""
        token_endpoint = self.discovery_document.get(
            "token_endpoint", f"{self.config.endpoint_url}/token"
        )

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(token_endpoint, data=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"Token exchange failed: {response.status} - {error_text}"
                    )

    async def _get_user_profile(self, access_token: str) -> UserProfile:
        """Get user profile using access token"""
        userinfo_endpoint = self.discovery_document.get(
            "userinfo_endpoint", f"{self.config.endpoint_url}/userinfo"
        )

        headers = {"Authorization": f"Bearer {access_token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(userinfo_endpoint, headers=headers) as response:
                if response.status == 200:
                    user_data = await response.json()

                    # Map claims to user profile
                    claims_mapping = self.config.claims_mapping or {}

                    return UserProfile(
                        user_id=user_data.get(claims_mapping.get("user_id", "sub"), ""),
                        email=user_data.get(claims_mapping.get("email", "email"), ""),
                        name=user_data.get(claims_mapping.get("name", "name"), ""),
                        roles=[
                            UserRole(role)
                            for role in user_data.get(
                                claims_mapping.get("roles", "roles"), ["user"]
                            )
                        ],
                        groups=user_data.get(
                            claims_mapping.get("groups", "groups"), []
                        ),
                        department=user_data.get(
                            claims_mapping.get("department", "department")
                        ),
                        title=user_data.get(claims_mapping.get("title", "title")),
                        attributes=user_data,
                        expires_at=datetime.now() + timedelta(hours=1),
                    )
                else:
                    raise Exception(f"Failed to get user profile: {response.status}")

    async def _validate_id_token(self, id_token: str) -> Dict[str, Any]:
        """Validate ID token and extract claims"""
        # Decode JWT header to get key ID
        header = jwt.get_unverified_header(id_token)
        key_id = header.get("kid")

        # Find matching public key
        public_key = None
        for key in self.jwks["keys"]:
            if key["kid"] == key_id:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                break

        if not public_key:
            raise Exception("No matching public key found for ID token")

        # Verify and decode ID token
        try:
            claims = jwt.decode(
                id_token,
                public_key,
                algorithms=["RS256"],
                audience=self.config.audience,
                issuer=self.config.issuer,
            )
            return claims
        except jwt.InvalidTokenError as e:
            raise Exception(f"Invalid ID token: {str(e)}")


class ActiveDirectoryProvider:
    """Active Directory authentication provider"""

    def __init__(self, config: SSOConfig):
        self.config = config
        self.connection = None

    async def initialize(self) -> bool:
        """Initialize AD provider"""
        try:
            # Initialize LDAP connection
            # This would use python-ldap or ldap3 library
            logger.info(f"Initialized AD provider: {self.config.provider_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize AD provider: {str(e)}")
            return False

    async def authenticate(self, username: str, password: str) -> AuthenticationResult:
        """Authenticate user with Active Directory"""
        try:
            # Mock AD authentication
            # In reality, this would connect to AD server

            if username and password:
                # Simulate successful authentication
                user_profile = UserProfile(
                    user_id=username,
                    email=f"{username}@company.com",
                    name=f"User {username}",
                    roles=[UserRole.USER],
                    groups=["Domain Users", "UATP_Users"],
                    department="IT",
                    title="Employee",
                    attributes={
                        "domain": "COMPANY",
                        "distinguished_name": f"CN={username},OU=Users,DC=company,DC=com",
                    },
                    expires_at=datetime.now() + timedelta(hours=24),
                )

                return AuthenticationResult(
                    success=True,
                    user_profile=user_profile,
                    provider_id=self.config.provider_id,
                    authentication_method=AuthenticationMethod.PASSWORD,
                    session_duration=86400,  # 24 hours
                )
            else:
                return AuthenticationResult(
                    success=False,
                    error_message="Invalid credentials",
                    provider_id=self.config.provider_id,
                )

        except Exception as e:
            logger.error(f"AD authentication failed: {str(e)}")
            return AuthenticationResult(
                success=False, error_message=str(e), provider_id=self.config.provider_id
            )


class EnterpriseSSO:
    """
    Enterprise Single Sign-On integration system
    """

    def __init__(
        self,
        capsule_engine: CapsuleEngine,
        attribution_tracker: CrossConversationTracker,
    ):
        self.capsule_engine = capsule_engine
        self.attribution_tracker = attribution_tracker

        # SSO providers registry
        self.providers = {}

        # Active user sessions
        self.active_sessions = {}

        # Provider factory
        self.provider_factory = {
            SSOProtocol.SAML2: SAMLProvider,
            SSOProtocol.OAUTH2: OAuth2Provider,
            SSOProtocol.OPENID_CONNECT: OAuth2Provider,
            SSOProtocol.ACTIVE_DIRECTORY: ActiveDirectoryProvider,
        }

        # Authentication statistics
        self.auth_stats = {
            "total_logins": 0,
            "successful_logins": 0,
            "failed_logins": 0,
            "active_sessions": 0,
            "by_provider": {},
            "by_protocol": {protocol.value: 0 for protocol in SSOProtocol},
        }

    async def register_sso_provider(self, config: SSOConfig) -> bool:
        """Register a new SSO provider"""
        try:
            provider_class = self.provider_factory.get(config.protocol)
            if not provider_class:
                raise ValueError(f"Unsupported SSO protocol: {config.protocol}")

            provider = provider_class(config)

            if await provider.initialize():
                self.providers[config.provider_id] = provider
                self.auth_stats["by_provider"][config.provider_id] = {
                    "total_logins": 0,
                    "successful_logins": 0,
                    "failed_logins": 0,
                }
                logger.info(
                    f"Successfully registered SSO provider: {config.provider_id}"
                )
                return True
            else:
                raise Exception("Provider initialization failed")

        except Exception as e:
            logger.error(
                f"Failed to register SSO provider {config.provider_id}: {str(e)}"
            )
            return False

    async def authenticate_user(
        self, provider_id: str, auth_data: Dict[str, Any]
    ) -> AuthenticationResult:
        """Authenticate user with specified provider"""
        try:
            self.auth_stats["total_logins"] += 1
            self.auth_stats["by_provider"][provider_id]["total_logins"] += 1

            provider = self.providers.get(provider_id)
            if not provider:
                raise ValueError(f"SSO provider not found: {provider_id}")

            # Authenticate based on provider type
            if isinstance(provider, SAMLProvider):
                result = await provider.authenticate(auth_data.get("saml_response", ""))
            elif isinstance(provider, OAuth2Provider):
                result = await provider.authenticate(
                    auth_data.get("authorization_code", ""),
                    auth_data.get("redirect_uri", ""),
                )
            elif isinstance(provider, ActiveDirectoryProvider):
                result = await provider.authenticate(
                    auth_data.get("username", ""), auth_data.get("password", "")
                )
            else:
                raise ValueError(f"Unsupported provider type: {type(provider)}")

            # Update statistics
            if result.success:
                self.auth_stats["successful_logins"] += 1
                self.auth_stats["by_provider"][provider_id]["successful_logins"] += 1

                # Create user session
                if result.user_profile:
                    session_id = await self._create_user_session(
                        result.user_profile, provider_id
                    )
                    result.user_profile.session_id = session_id

                    # Track authentication attribution
                    await self._track_authentication_attribution(result, auth_data)

                    # Create authentication capsule
                    await self._create_authentication_capsule(result, auth_data)

            else:
                self.auth_stats["failed_logins"] += 1
                self.auth_stats["by_provider"][provider_id]["failed_logins"] += 1

            return result

        except Exception as e:
            self.auth_stats["failed_logins"] += 1
            if provider_id in self.auth_stats["by_provider"]:
                self.auth_stats["by_provider"][provider_id]["failed_logins"] += 1

            logger.error(f"Authentication failed: {str(e)}")
            return AuthenticationResult(
                success=False, error_message=str(e), provider_id=provider_id
            )

    async def validate_session(self, session_id: str) -> Optional[UserProfile]:
        """Validate user session"""
        session = self.active_sessions.get(session_id)

        if not session:
            return None

        # Check if session is expired
        if session.expires_at and session.expires_at < datetime.now():
            await self._invalidate_session(session_id)
            return None

        return session

    async def refresh_session(
        self, session_id: str, refresh_token: Optional[str] = None
    ) -> Optional[UserProfile]:
        """Refresh user session"""
        session = self.active_sessions.get(session_id)

        if not session:
            return None

        # Extend session expiry
        session.expires_at = datetime.now() + timedelta(hours=8)

        # If refresh token provided, refresh OAuth2 tokens
        if refresh_token:
            # This would implement token refresh logic
            pass

        return session

    async def logout_user(self, session_id: str) -> bool:
        """Logout user and invalidate session"""
        return await self._invalidate_session(session_id)

    async def get_user_permissions(self, user_profile: UserProfile) -> Dict[str, Any]:
        """Get user permissions based on roles and groups"""
        permissions = {
            "can_read": True,
            "can_write": False,
            "can_admin": False,
            "can_manage": False,
            "accessible_resources": [],
            "restricted_resources": [],
        }

        # Check roles
        if UserRole.ADMIN in user_profile.roles:
            permissions.update(
                {
                    "can_write": True,
                    "can_admin": True,
                    "can_manage": True,
                    "accessible_resources": ["*"],
                }
            )
        elif UserRole.MANAGER in user_profile.roles:
            permissions.update(
                {
                    "can_write": True,
                    "can_manage": True,
                    "accessible_resources": ["team_resources", "department_resources"],
                }
            )
        elif UserRole.USER in user_profile.roles:
            permissions.update(
                {"can_write": True, "accessible_resources": ["user_resources"]}
            )

        # Check groups
        if "Engineering" in user_profile.groups:
            permissions["accessible_resources"].append("engineering_resources")

        if "UATP_Users" in user_profile.groups:
            permissions["accessible_resources"].append("uatp_resources")

        return permissions

    async def _create_user_session(
        self, user_profile: UserProfile, provider_id: str
    ) -> str:
        """Create user session"""
        session_id = f"session_{int(datetime.now().timestamp())}_{user_profile.user_id}"

        # Store session
        self.active_sessions[session_id] = user_profile
        self.auth_stats["active_sessions"] += 1

        logger.info(f"Created session {session_id} for user {user_profile.user_id}")
        return session_id

    async def _invalidate_session(self, session_id: str) -> bool:
        """Invalidate user session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            self.auth_stats["active_sessions"] -= 1
            logger.info(f"Invalidated session {session_id}")
            return True
        return False

    async def _track_authentication_attribution(
        self, result: AuthenticationResult, auth_data: Dict[str, Any]
    ):
        """Track attribution for authentication"""
        if result.user_profile:
            attribution_data = {
                "user_id": result.user_profile.user_id,
                "provider_id": result.provider_id,
                "authentication_method": result.authentication_method.value
                if result.authentication_method
                else None,
                "session_id": result.user_profile.session_id,
                "timestamp": datetime.now().isoformat(),
                "user_attributes": result.user_profile.attributes,
            }

            # This would integrate with the attribution tracker
            # await self.attribution_tracker.track_authentication(attribution_data)

    async def _create_authentication_capsule(
        self, result: AuthenticationResult, auth_data: Dict[str, Any]
    ):
        """Create capsule for authentication event"""
        capsule_data = {
            "type": "authentication_event",
            "authentication_result": result.to_dict(),
            "auth_data": {
                "provider_id": result.provider_id,
                "authentication_method": result.authentication_method.value
                if result.authentication_method
                else None,
                "timestamp": datetime.now().isoformat(),
            },
            "user_session": {
                "session_id": result.user_profile.session_id
                if result.user_profile
                else None,
                "session_duration": result.session_duration,
            },
        }

        # Create specialized capsule
        capsule = create_specialized_capsule(
            capsule_type="authentication_event",
            data=capsule_data,
            metadata={"source": "enterprise_sso"},
        )

        # Store in capsule engine
        await self.capsule_engine.store_capsule(capsule)

    async def get_sso_statistics(self) -> Dict[str, Any]:
        """Get SSO authentication statistics"""
        stats = self.auth_stats.copy()

        if stats["total_logins"] > 0:
            stats["success_rate"] = stats["successful_logins"] / stats["total_logins"]
        else:
            stats["success_rate"] = 0.0

        return stats

    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get list of active user sessions"""
        sessions = []

        for session_id, user_profile in self.active_sessions.items():
            sessions.append(
                {
                    "session_id": session_id,
                    "user_id": user_profile.user_id,
                    "email": user_profile.email,
                    "name": user_profile.name,
                    "roles": [role.value for role in user_profile.roles],
                    "expires_at": user_profile.expires_at.isoformat()
                    if user_profile.expires_at
                    else None,
                }
            )

        return sessions

    async def get_registered_providers(self) -> List[Dict[str, Any]]:
        """Get list of registered SSO providers"""
        providers = []

        for provider_id, provider in self.providers.items():
            provider_info = {
                "provider_id": provider_id,
                "provider_name": provider.config.provider_name,
                "protocol": provider.config.protocol.value,
                "status": "active",
            }
            providers.append(provider_info)

        return providers
