"""
Dependency Injection Container

Provides a comprehensive dependency injection system for managing service
dependencies, lifecycles, and configurations. Supports singleton, transient,
and scoped lifetimes with proper cleanup and lifecycle management.

Key Features:
- Service registration with different lifetimes
- Automatic dependency resolution
- Circular dependency detection
- Scoped services for request-based lifetimes
- Proper resource cleanup
- Integration with FastAPI
- Configuration-based service setup
- Service health checking
"""

import asyncio
import inspect
import threading
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    get_origin,
    get_type_hints,
)

import structlog
from fastapi import Request

logger = structlog.get_logger(__name__)

T = TypeVar("T")
ServiceType = TypeVar("ServiceType")


class ServiceLifetime(Enum):
    """Service lifetime management options"""

    SINGLETON = "singleton"  # Single instance for application lifetime
    TRANSIENT = "transient"  # New instance every time
    SCOPED = "scoped"  # Single instance per scope (request)


class ServiceScope(Enum):
    """Service scope types"""

    APPLICATION = "application"  # Application-wide scope
    REQUEST = "request"  # HTTP request scope
    TASK = "task"  # Async task scope


@dataclass
class ServiceDescriptor:
    """Describes how a service should be created and managed"""

    service_type: Type
    implementation_type: Optional[Type] = None
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    dependencies: List[Type] = field(default_factory=list)
    is_initialized: bool = False
    health_check: Optional[Callable] = None
    cleanup: Optional[Callable] = None


@dataclass
class ServiceRegistration:
    """Service registration information"""

    service_type: Type
    descriptor: ServiceDescriptor
    registration_time: float = field(
        default_factory=lambda: asyncio.get_event_loop().time()
    )


class DependencyInjectionError(Exception):
    """Base exception for dependency injection errors"""

    pass


class CircularDependencyError(DependencyInjectionError):
    """Raised when circular dependencies are detected"""

    def __init__(self, cycle: List[Type]):
        cycle_names = [t.__name__ for t in cycle]
        super().__init__(f"Circular dependency detected: {' -> '.join(cycle_names)}")
        self.cycle = cycle


class ServiceNotFoundError(DependencyInjectionError):
    """Raised when a required service is not registered"""

    def __init__(self, service_type: Type):
        super().__init__(f"Service not registered: {service_type.__name__}")
        self.service_type = service_type


class ServiceScopeContext:
    """Manages scoped service instances"""

    def __init__(self, scope_type: ServiceScope = ServiceScope.REQUEST):
        self.scope_type = scope_type
        self.instances: Dict[Type, Any] = {}
        self.cleanup_callbacks: List[Callable] = []
        self._disposed = False

    async def dispose(self):
        """Dispose of all scoped services"""
        if self._disposed:
            return

        logger.debug(f"Disposing scope with {len(self.instances)} instances")

        # Run cleanup callbacks in reverse order
        for cleanup in reversed(self.cleanup_callbacks):
            try:
                if asyncio.iscoroutinefunction(cleanup):
                    await cleanup()
                else:
                    cleanup()
            except Exception as e:
                logger.error(f"Error during service cleanup: {e}")

        self.instances.clear()
        self.cleanup_callbacks.clear()
        self._disposed = True


# Context variable for current service scope
current_scope: ContextVar[Optional[ServiceScopeContext]] = ContextVar(
    "current_scope", default=None
)


class ServiceContainer:
    """
    Main dependency injection container
    """

    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._lock = threading.RLock()
        self._building_stack: Set[Type] = set()

        # Register self
        self.register_instance(ServiceContainer, self)

        logger.info("Service container initialized")

    def register_singleton(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[..., T]] = None,
        instance: Optional[T] = None,
        health_check: Optional[Callable] = None,
        cleanup: Optional[Callable] = None,
    ) -> "ServiceContainer":
        """Register a singleton service"""
        return self._register_service(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            instance=instance,
            lifetime=ServiceLifetime.SINGLETON,
            health_check=health_check,
            cleanup=cleanup,
        )

    def register_transient(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[..., T]] = None,
        health_check: Optional[Callable] = None,
    ) -> "ServiceContainer":
        """Register a transient service"""
        return self._register_service(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            lifetime=ServiceLifetime.TRANSIENT,
            health_check=health_check,
        )

    def register_scoped(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[..., T]] = None,
        cleanup: Optional[Callable] = None,
    ) -> "ServiceContainer":
        """Register a scoped service"""
        return self._register_service(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            lifetime=ServiceLifetime.SCOPED,
            cleanup=cleanup,
        )

    def register_instance(
        self, service_type: Type[T], instance: T
    ) -> "ServiceContainer":
        """Register a specific instance as singleton"""
        return self._register_service(
            service_type=service_type,
            instance=instance,
            lifetime=ServiceLifetime.SINGLETON,
        )

    def _register_service(
        self,
        service_type: Type,
        implementation_type: Optional[Type] = None,
        factory: Optional[Callable] = None,
        instance: Optional[Any] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
        health_check: Optional[Callable] = None,
        cleanup: Optional[Callable] = None,
    ) -> "ServiceContainer":
        """Internal service registration"""

        with self._lock:
            # Determine implementation type
            if instance is not None:
                impl_type = type(instance)
            elif implementation_type is not None:
                impl_type = implementation_type
            elif factory is not None:
                impl_type = service_type
            else:
                impl_type = service_type

            # Analyze dependencies
            dependencies = self._analyze_dependencies(impl_type, factory)

            descriptor = ServiceDescriptor(
                service_type=service_type,
                implementation_type=impl_type,
                factory=factory,
                instance=instance,
                lifetime=lifetime,
                dependencies=dependencies,
                health_check=health_check,
                cleanup=cleanup,
            )

            self._services[service_type] = descriptor

            logger.debug(
                f"Registered service: {service_type.__name__}",
                implementation=impl_type.__name__,
                lifetime=lifetime.value,
                dependencies=len(dependencies),
            )

            return self

    def _analyze_dependencies(
        self, implementation_type: Type, factory: Optional[Callable] = None
    ) -> List[Type]:
        """Analyze constructor or factory dependencies"""
        dependencies = []

        try:
            if factory:
                # Analyze factory function
                sig = inspect.signature(factory)
                type_hints = get_type_hints(factory)
            else:
                # Analyze constructor
                sig = inspect.signature(implementation_type.__init__)
                type_hints = get_type_hints(implementation_type.__init__)

            for param_name, _param in sig.parameters.items():
                if param_name == "self":
                    continue

                param_type = type_hints.get(param_name)
                if param_type and param_type is not type(None):
                    # Handle generic types
                    origin = get_origin(param_type)
                    if origin is not None:
                        param_type = origin

                    dependencies.append(param_type)

        except Exception as e:
            logger.warning(
                f"Could not analyze dependencies for {implementation_type.__name__}: {e}"
            )

        return dependencies

    async def get_service(self, service_type: Type[T]) -> T:
        """Get service instance"""
        return await self._resolve_service(service_type)

    async def _resolve_service(self, service_type: Type[T]) -> T:
        """Resolve service with dependency injection"""

        # Check for circular dependencies
        if service_type in self._building_stack:
            cycle = list(self._building_stack) + [service_type]
            raise CircularDependencyError(cycle)

        descriptor = self._services.get(service_type)
        if not descriptor:
            raise ServiceNotFoundError(service_type)

        # Handle different lifetimes
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            return await self._get_singleton(service_type, descriptor)
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            return await self._get_scoped(service_type, descriptor)
        else:  # TRANSIENT
            return await self._create_instance(service_type, descriptor)

    async def _get_singleton(
        self, service_type: Type[T], descriptor: ServiceDescriptor
    ) -> T:
        """Get or create singleton instance"""

        if service_type in self._singletons:
            return self._singletons[service_type]

        with self._lock:
            # Double-check locking pattern
            if service_type in self._singletons:
                return self._singletons[service_type]

            instance = await self._create_instance(service_type, descriptor)
            self._singletons[service_type] = instance

            return instance

    async def _get_scoped(
        self, service_type: Type[T], descriptor: ServiceDescriptor
    ) -> T:
        """Get or create scoped instance"""

        scope = current_scope.get()
        if not scope:
            # No scope, create as transient
            logger.warning(
                f"No scope available for scoped service {service_type.__name__}, creating as transient"
            )
            return await self._create_instance(service_type, descriptor)

        if service_type in scope.instances:
            return scope.instances[service_type]

        instance = await self._create_instance(service_type, descriptor)
        scope.instances[service_type] = instance

        # Register cleanup if provided
        if descriptor.cleanup:
            scope.cleanup_callbacks.append(descriptor.cleanup)

        return instance

    async def _create_instance(
        self, service_type: Type[T], descriptor: ServiceDescriptor
    ) -> T:
        """Create new service instance"""

        if descriptor.instance is not None:
            return descriptor.instance

        self._building_stack.add(service_type)

        try:
            # Resolve dependencies
            dependencies = []
            for dep_type in descriptor.dependencies:
                dep_instance = await self._resolve_service(dep_type)
                dependencies.append(dep_instance)

            # Create instance
            if descriptor.factory:
                if asyncio.iscoroutinefunction(descriptor.factory):
                    instance = await descriptor.factory(*dependencies)
                else:
                    instance = descriptor.factory(*dependencies)
            else:
                instance = descriptor.implementation_type(*dependencies)

            # Initialize if needed
            if hasattr(instance, "initialize") and not descriptor.is_initialized:
                if asyncio.iscoroutinefunction(instance.initialize):
                    await instance.initialize()
                else:
                    instance.initialize()
                descriptor.is_initialized = True

            logger.debug(f"Created instance of {service_type.__name__}")
            return instance

        finally:
            self._building_stack.discard(service_type)

    @asynccontextmanager
    async def create_scope(self, scope_type: ServiceScope = ServiceScope.REQUEST):
        """Create a new service scope"""
        scope = ServiceScopeContext(scope_type)
        token = current_scope.set(scope)

        try:
            logger.debug(f"Created {scope_type.value} scope")
            yield scope
        finally:
            await scope.dispose()
            current_scope.reset(token)
            logger.debug(f"Disposed {scope_type.value} scope")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all registered services"""
        results = {}

        for service_type, descriptor in self._services.items():
            service_name = service_type.__name__

            try:
                if descriptor.health_check:
                    if asyncio.iscoroutinefunction(descriptor.health_check):
                        result = await descriptor.health_check()
                    else:
                        result = descriptor.health_check()

                    results[service_name] = {
                        "status": "healthy" if result else "unhealthy",
                        "details": result if isinstance(result, dict) else {},
                    }
                else:
                    results[service_name] = {
                        "status": "unknown",
                        "details": "No health check configured",
                    }

            except Exception as e:
                results[service_name] = {"status": "unhealthy", "error": str(e)}
                logger.error(f"Health check failed for {service_name}: {e}")

        return results

    async def shutdown(self):
        """Shutdown container and cleanup all singletons"""
        logger.info("Shutting down service container")

        # Cleanup singletons in reverse order of creation
        for service_type, instance in reversed(list(self._singletons.items())):
            try:
                descriptor = self._services.get(service_type)
                if descriptor and descriptor.cleanup:
                    if asyncio.iscoroutinefunction(descriptor.cleanup):
                        await descriptor.cleanup()
                    else:
                        descriptor.cleanup()

                # Call shutdown method if available
                if hasattr(instance, "shutdown"):
                    if asyncio.iscoroutinefunction(instance.shutdown):
                        await instance.shutdown()
                    else:
                        instance.shutdown()

            except Exception as e:
                logger.error(f"Error shutting down {service_type.__name__}: {e}")

        self._singletons.clear()
        logger.info("Service container shutdown complete")

    def get_registration_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered services"""
        info = {}

        for service_type, descriptor in self._services.items():
            info[service_type.__name__] = {
                "service_type": service_type.__name__,
                "implementation_type": descriptor.implementation_type.__name__
                if descriptor.implementation_type
                else None,
                "lifetime": descriptor.lifetime.value,
                "dependencies": [dep.__name__ for dep in descriptor.dependencies],
                "has_factory": descriptor.factory is not None,
                "has_instance": descriptor.instance is not None,
                "has_health_check": descriptor.health_check is not None,
                "has_cleanup": descriptor.cleanup is not None,
                "is_singleton": service_type in self._singletons,
            }

        return info


# Global container instance
_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """Get global service container"""
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container


def reset_container():
    """Reset global container (mainly for testing)"""
    global _container
    _container = None


# Decorators for dependency injection
def inject(service_type: Type[T]):
    """Decorator to inject service as function parameter"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            container = get_container()
            service = await container.get_service(service_type)
            return await func(*args, service, **kwargs)

        return wrapper

    return decorator


def injectable(
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    health_check: Optional[Callable] = None,
    cleanup: Optional[Callable] = None,
):
    """Class decorator to mark class as injectable"""

    def decorator(cls):
        # Auto-register the class
        container = get_container()

        if lifetime == ServiceLifetime.SINGLETON:
            container.register_singleton(
                cls, implementation_type=cls, health_check=health_check, cleanup=cleanup
            )
        elif lifetime == ServiceLifetime.SCOPED:
            container.register_scoped(cls, implementation_type=cls, cleanup=cleanup)
        else:
            container.register_transient(
                cls, implementation_type=cls, health_check=health_check
            )

        return cls

    return decorator


# FastAPI integration
class DIContainer:
    """FastAPI-compatible dependency injection"""

    def __init__(self, container: Optional[ServiceContainer] = None):
        self.container = container or get_container()

    async def __call__(self, request: Request) -> ServiceContainer:
        """FastAPI dependency that provides the container"""
        return self.container


async def get_scoped_service(
    service_type: Type[T], container: ServiceContainer = None
) -> T:
    """FastAPI dependency for getting scoped services"""
    if container is None:
        container = get_container()

    return await container.get_service(service_type)


# Middleware for request scoping
async def di_scope_middleware(request: Request, call_next):
    """Middleware to create request scope for dependency injection"""
    container = get_container()

    async with container.create_scope(ServiceScope.REQUEST) as scope:
        # Store scope in request state for access in route handlers
        request.state.di_scope = scope
        response = await call_next(request)
        return response


# Configuration-based service registration
class ServiceConfiguration:
    """Configuration for service registration"""

    @staticmethod
    async def configure_services(container: ServiceContainer, config: Dict[str, Any]):
        """Configure services from configuration dictionary"""

        for service_name, service_config in config.items():
            try:
                # Import service class
                module_path = service_config.get("module")
                class_name = service_config.get("class")

                if module_path and class_name:
                    module = __import__(module_path, fromlist=[class_name])
                    service_class = getattr(module, class_name)

                    # Register service based on configuration
                    lifetime = ServiceLifetime(
                        service_config.get("lifetime", "transient")
                    )

                    if lifetime == ServiceLifetime.SINGLETON:
                        container.register_singleton(service_class)
                    elif lifetime == ServiceLifetime.SCOPED:
                        container.register_scoped(service_class)
                    else:
                        container.register_transient(service_class)

                    logger.info(f"Configured service: {service_name}")

            except Exception as e:
                logger.error(f"Failed to configure service {service_name}: {e}")


# Example service interfaces
class ILogger(ABC):
    """Logger service interface"""

    @abstractmethod
    def log(self, message: str, level: str = "info"):
        pass


class IDatabase(ABC):
    """Database service interface"""

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass


class ICacheService(ABC):
    """Cache service interface"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        pass

    @abstractmethod
    async def delete(self, key: str):
        pass
