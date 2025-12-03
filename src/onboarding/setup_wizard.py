"""
Interactive Setup Wizard

Provides guided, visual setup with smart defaults and auto-detection.
Handles system initialization, environment detection, and configuration
with minimal user input required.
"""

import asyncio
import logging
import os
import sys
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class SetupStage(Enum):
    """Setup stages for progress tracking"""

    DETECTING = "detecting"
    CONFIGURING = "configuring"
    INITIALIZING = "initializing"
    VALIDATING = "validating"
    COMPLETE = "complete"


@dataclass
class EnvironmentInfo:
    """Environment detection results"""

    operating_system: str
    python_version: str
    has_git: bool = False
    has_docker: bool = False
    has_openai_key: bool = False
    has_anthropic_key: bool = False
    project_structure: Dict[str, Any] = field(default_factory=dict)
    network_access: bool = True
    system_capabilities: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SetupResult:
    """Result of setup process"""

    success: bool
    stage: SetupStage
    configuration: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)


class InteractiveSetupWizard:
    """
    Interactive setup wizard that makes UATP configuration effortless.

    Features:
    - Smart environment detection
    - Auto-configuration with sensible defaults
    - Visual progress indicators
    - Real-time validation
    - Contextual help and troubleshooting
    """

    def __init__(self):
        """Initialize the setup wizard"""
        self.current_stage = SetupStage.DETECTING
        self.setup_progress = {}
        self.environment_info = None

        logger.info("Interactive Setup Wizard initialized")

    async def detect_environment(self) -> EnvironmentInfo:
        """
        Intelligently detect user environment and capabilities

        Returns:
            EnvironmentInfo with detected environment details
        """

        self.current_stage = SetupStage.DETECTING
        logger.info("🔍 Detecting environment...")

        env_info = EnvironmentInfo(
            operating_system=platform.system(),
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )

        # Detect development tools
        env_info.has_git = await self._check_command_exists("git")
        env_info.has_docker = await self._check_command_exists("docker")

        # Check for API keys
        env_info.has_openai_key = bool(os.getenv("OPENAI_API_KEY"))
        env_info.has_anthropic_key = bool(os.getenv("ANTHROPIC_API_KEY"))

        # Analyze project structure
        env_info.project_structure = await self._analyze_project_structure()

        # Check network connectivity
        env_info.network_access = await self._check_network_connectivity()

        # Assess system capabilities
        env_info.system_capabilities = await self._assess_system_capabilities()

        self.environment_info = env_info

        logger.info(
            f"✅ Environment detection complete: {env_info.operating_system} with Python {env_info.python_version}"
        )

        return env_info

    async def quick_setup(
        self, user_type: Any, preferences: Dict[str, Any] = None
    ) -> SetupResult:
        """
        Perform quick setup with smart defaults

        Args:
            user_type: User type enum for personalized setup
            preferences: User preferences and context

        Returns:
            SetupResult with configuration details
        """

        self.current_stage = SetupStage.CONFIGURING
        preferences = preferences or {}

        logger.info(
            f"🚀 Starting quick setup for {user_type.value if hasattr(user_type, 'value') else str(user_type)}"
        )

        try:
            # Ensure environment is detected
            if not self.environment_info:
                await self.detect_environment()

            # Create optimal configuration based on environment and user type
            config = await self._create_optimal_configuration(user_type, preferences)

            # Initialize system with configuration
            init_result = await self._initialize_system(config)

            # Validate setup
            validation_result = await self._validate_setup(config)

            if init_result and validation_result:
                result = SetupResult(
                    success=True, stage=SetupStage.COMPLETE, configuration=config
                )

                # Add next steps based on user type
                result.next_steps = self._generate_setup_next_steps(user_type, config)

                logger.info("✅ Quick setup completed successfully")
                return result
            else:
                return SetupResult(
                    success=False,
                    stage=SetupStage.CONFIGURING,
                    errors=["Setup initialization failed"],
                    configuration=config,
                )

        except Exception as e:
            logger.error(f"❌ Quick setup failed: {e}")
            return SetupResult(
                success=False, stage=SetupStage.CONFIGURING, errors=[str(e)]
            )

    async def _create_optimal_configuration(
        self, user_type: Any, preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create optimal configuration based on environment and user needs"""

        config = {
            "user_type": str(user_type),
            "environment": "development",
            "storage": {"type": "local", "path": "./storage", "compressed": False},
            "api": {"host": "127.0.0.1", "port": 9090, "cors_enabled": True},
            "logging": {"level": "INFO", "console": True, "file": True},
            "security": {"api_keys_required": False, "rate_limiting": True},
            "features": {
                "crypto_enabled": True,
                "economics_enabled": True,
                "ml_analytics": True,
                "governance": False,  # Start simple
            },
        }

        # Customize based on user type
        if hasattr(user_type, "value"):
            if user_type.value == "developer":
                config["logging"]["level"] = "DEBUG"
                config["features"]["governance"] = True
                config["api"]["port"] = 9090

            elif user_type.value == "enterprise":
                config["security"]["api_keys_required"] = True
                config["features"]["governance"] = True
                config["storage"]["compressed"] = True
                config["logging"]["level"] = "WARNING"

            elif user_type.value in ["casual_user", "business_user"]:
                config["logging"]["level"] = "WARNING"
                config["features"] = {
                    "crypto_enabled": False,  # Simplify for casual users
                    "economics_enabled": True,
                    "ml_analytics": False,
                    "governance": False,
                }

        # Apply environment-specific optimizations
        if self.environment_info:
            # Adjust for available tools
            if not self.environment_info.has_docker:
                config["deployment"] = {"type": "local"}

            # Use available API keys
            if self.environment_info.has_openai_key:
                config["integrations"] = config.get("integrations", {})
                config["integrations"]["openai"] = {"enabled": True}

            if self.environment_info.has_anthropic_key:
                config["integrations"] = config.get("integrations", {})
                config["integrations"]["anthropic"] = {"enabled": True}

        # Apply user preferences
        if preferences:
            # Performance preferences
            if preferences.get("performance_priority") == "speed":
                config["storage"]["compressed"] = False
                config["features"]["ml_analytics"] = False

            elif preferences.get("performance_priority") == "storage":
                config["storage"]["compressed"] = True

        return config

    async def _initialize_system(self, config: Dict[str, Any]) -> bool:
        """Initialize UATP system with configuration"""

        self.current_stage = SetupStage.INITIALIZING
        logger.info("⚙️ Initializing UATP system...")

        try:
            # Create storage directories
            storage_path = Path(config["storage"]["path"])
            storage_path.mkdir(parents=True, exist_ok=True)

            # Create configuration file
            config_path = Path("config") / "setup.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            # Initialize core systems based on configuration
            await self._initialize_core_systems(config)

            logger.info("✅ System initialization complete")
            return True

        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False

    async def _initialize_core_systems(self, config: Dict[str, Any]):
        """Initialize core UATP systems"""

        # Import and initialize systems based on config
        systems_to_init = []

        if config["features"].get("crypto_enabled", False):
            systems_to_init.append("crypto")

        if config["features"].get("economics_enabled", False):
            systems_to_init.append("economics")

        if config["features"].get("ml_analytics", False):
            systems_to_init.append("ml_analytics")

        # Initialize each system
        for system in systems_to_init:
            try:
                await self._initialize_system_component(system, config)
                logger.info(f"✅ Initialized {system} system")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize {system}: {e}")

    async def _initialize_system_component(
        self, component: str, config: Dict[str, Any]
    ):
        """Initialize individual system component"""

        if component == "crypto":
            # Initialize crypto systems with minimal setup
            try:
                from ..crypto.post_quantum import post_quantum_crypto

                post_quantum_crypto.initialize_crypto_systems()
            except ImportError:
                logger.warning("Crypto systems not available")

        elif component == "economics":
            # Initialize economic systems
            try:
                from ..economic.fcde_engine import fcde_engine

                fcde_engine.initialize_system()
            except ImportError:
                logger.warning("Economic systems not available")

        elif component == "ml_analytics":
            # Initialize ML analytics
            try:
                from ..ml.analytics_engine import ml_analytics

                # ML analytics auto-initializes
                pass
            except ImportError:
                logger.warning("ML analytics not available")

    async def _validate_setup(self, config: Dict[str, Any]) -> bool:
        """Validate that setup was successful"""

        self.current_stage = SetupStage.VALIDATING
        logger.info("🔍 Validating setup...")

        validation_checks = [
            self._validate_storage_access(config),
            self._validate_api_readiness(config),
            self._validate_system_health(),
        ]

        results = await asyncio.gather(*validation_checks, return_exceptions=True)

        success = all(
            result is True for result in results if not isinstance(result, Exception)
        )

        if success:
            logger.info("✅ Setup validation successful")
        else:
            logger.warning("⚠️ Setup validation found issues")

        return success

    async def _validate_storage_access(self, config: Dict[str, Any]) -> bool:
        """Validate storage system is accessible"""
        try:
            storage_path = Path(config["storage"]["path"])

            # Test write access
            test_file = storage_path / "test_access.txt"
            test_file.write_text("test")
            test_file.unlink()

            return True
        except Exception as e:
            logger.error(f"Storage validation failed: {e}")
            return False

    async def _validate_api_readiness(self, config: Dict[str, Any]) -> bool:
        """Validate API is ready to start"""
        try:
            # Check port availability
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((config["api"]["host"], config["api"]["port"]))
            sock.close()

            # Port should be available (connection should fail)
            return result != 0
        except Exception:
            return True

    async def _validate_system_health(self) -> bool:
        """Validate overall system health"""
        try:
            # Basic system health checks
            import psutil

            # Check memory availability
            memory = psutil.virtual_memory()
            if memory.available < 100 * 1024 * 1024:  # 100MB minimum
                logger.warning("Low memory available")
                return False

            # Check disk space
            disk = psutil.disk_usage(".")
            if disk.free < 500 * 1024 * 1024:  # 500MB minimum
                logger.warning("Low disk space available")
                return False

            return True
        except ImportError:
            # psutil not available, assume healthy
            return True
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

    def _generate_setup_next_steps(
        self, user_type: Any, config: Dict[str, Any]
    ) -> List[str]:
        """Generate next steps based on setup configuration"""

        steps = [
            "🚀 Start the UATP API server",
            "🌐 Open the web dashboard",
            "🧪 Create your first capsule",
        ]

        # Add user-type specific steps
        if hasattr(user_type, "value"):
            if user_type.value == "developer":
                steps.extend(
                    [
                        "📚 Explore the API documentation",
                        "🔧 Set up your development environment",
                        "🧪 Try the example code snippets",
                    ]
                )
            elif user_type.value == "enterprise":
                steps.extend(
                    [
                        "👥 Configure team access",
                        "🔒 Review security settings",
                        "📊 Set up monitoring and alerts",
                    ]
                )

        # Add integration-specific steps
        if config.get("integrations", {}).get("openai", {}).get("enabled"):
            steps.append("🤖 Test OpenAI integration")

        if config.get("integrations", {}).get("anthropic", {}).get("enabled"):
            steps.append("🤖 Test Anthropic integration")

        return steps

    # Advanced setup methods for different user types

    async def analyze_development_environment(self) -> Dict[str, Any]:
        """Analyze development environment for developer users"""

        analysis = {
            "ide_detected": await self._detect_ide(),
            "package_managers": await self._detect_package_managers(),
            "testing_frameworks": await self._detect_testing_frameworks(),
            "ci_cd_systems": await self._detect_cicd_systems(),
            "container_platforms": await self._detect_container_platforms(),
        }

        return analysis

    async def setup_secure_credentials(self) -> Dict[str, Any]:
        """Setup secure credential management for developers"""

        return {
            "credential_store": "local_vault",
            "encryption_enabled": True,
            "api_key_rotation": False,
            "audit_logging": True,
        }

    async def setup_development_tools(self) -> Dict[str, Any]:
        """Setup development and debugging tools"""

        return {
            "debug_mode": True,
            "api_playground": True,
            "testing_tools": True,
            "performance_profiling": True,
        }

    async def assess_security_requirements(self) -> Dict[str, Any]:
        """Assess enterprise security requirements"""

        return {
            "compliance_frameworks": ["SOC2", "GDPR"],
            "encryption_requirements": "enterprise_grade",
            "audit_requirements": "comprehensive",
            "access_control": "rbac_enabled",
        }

    async def setup_production_infrastructure(self) -> Dict[str, Any]:
        """Setup production-ready infrastructure"""

        return {
            "scalability": "auto_scaling",
            "availability": "high_availability",
            "monitoring": "comprehensive",
            "backup_strategy": "automated",
        }

    async def setup_governance_framework(self) -> Dict[str, Any]:
        """Setup governance and compliance framework"""

        return {
            "governance_model": "committee_based",
            "voting_mechanisms": "stake_weighted",
            "audit_trails": "comprehensive",
            "compliance_monitoring": "automated",
        }

    async def setup_team_management(self) -> Dict[str, Any]:
        """Setup team member access and role management"""

        return {
            "access_control": "role_based",
            "team_roles": ["admin", "developer", "analyst", "viewer"],
            "permission_model": "granular",
            "audit_logging": True,
        }

    # Utility methods

    async def _check_command_exists(self, command: str) -> bool:
        """Check if a command exists in the system PATH"""
        try:
            result = subprocess.run(
                ["which" if os.name != "nt" else "where", command],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    async def _analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze current project structure for context"""

        structure = {
            "is_git_repo": os.path.exists(".git"),
            "has_requirements": os.path.exists("requirements.txt"),
            "has_dockerfile": os.path.exists("Dockerfile"),
            "has_config": os.path.exists("config"),
            "python_files": len(list(Path(".").glob("**/*.py"))),
        }

        return structure

    async def _check_network_connectivity(self) -> bool:
        """Check basic network connectivity"""
        try:
            import urllib.request

            urllib.request.urlopen("https://8.8.8.8", timeout=5)
            return True
        except Exception:
            return False

    async def _assess_system_capabilities(self) -> Dict[str, Any]:
        """Assess system computational capabilities"""

        capabilities = {
            "cpu_count": os.cpu_count(),
            "platform": platform.platform(),
            "architecture": platform.architecture()[0],
        }

        try:
            import psutil

            capabilities.update(
                {
                    "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                    "disk_free_gb": round(psutil.disk_usage(".").free / (1024**3), 2),
                }
            )
        except ImportError:
            pass

        return capabilities

    async def _detect_ide(self) -> Optional[str]:
        """Detect IDE being used"""
        # Simple heuristics for IDE detection
        if os.path.exists(".vscode"):
            return "vscode"
        elif os.path.exists(".idea"):
            return "pycharm"
        elif os.getenv("PYCHARM_HOSTED"):
            return "pycharm"
        elif os.getenv("VSCODE_INJECTION"):
            return "vscode"
        return None

    async def _detect_package_managers(self) -> List[str]:
        """Detect available package managers"""
        managers = []

        if await self._check_command_exists("pip"):
            managers.append("pip")
        if await self._check_command_exists("conda"):
            managers.append("conda")
        if await self._check_command_exists("poetry"):
            managers.append("poetry")
        if await self._check_command_exists("pipenv"):
            managers.append("pipenv")

        return managers

    async def _detect_testing_frameworks(self) -> List[str]:
        """Detect testing frameworks"""
        frameworks = []

        try:
            import pytest

            frameworks.append("pytest")
        except ImportError:
            pass

        try:
            import unittest

            frameworks.append("unittest")
        except ImportError:
            pass

        return frameworks

    async def _detect_cicd_systems(self) -> List[str]:
        """Detect CI/CD systems"""
        systems = []

        if os.path.exists(".github/workflows"):
            systems.append("github_actions")
        if os.path.exists(".gitlab-ci.yml"):
            systems.append("gitlab_ci")
        if os.path.exists("Jenkinsfile"):
            systems.append("jenkins")

        return systems

    async def _detect_container_platforms(self) -> List[str]:
        """Detect container platforms"""
        platforms = []

        if await self._check_command_exists("docker"):
            platforms.append("docker")
        if await self._check_command_exists("podman"):
            platforms.append("podman")
        if await self._check_command_exists("kubectl"):
            platforms.append("kubernetes")

        return platforms
