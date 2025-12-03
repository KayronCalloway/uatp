"""
Dependency Injection Container for UATP Capsule Engine

Provides a centralized dependency injection system for better testability,
maintainability, and loose coupling between components.

Features:
- Singleton and factory providers
- Interface-based dependency resolution
- Configuration injection
- Lifecycle management
- Test-friendly dependency overrides
"""

import inspect
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, get_type_hints
from functools import wraps

import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class Lifetime(Enum):
    """Dependency lifetime management"""

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class DependencyDescriptor:
    """Describes how to create and manage a dependency"""

    dependency_type: Type
    factory: Optional[Callable] = None
    lifetime: Lifetime = Lifetime.SINGLETON
    instance: Any = None
    initialized: bool = False


class DependencyResolutionError(Exception):
    """Raised when dependency resolution fails"""

    pass


class CircularDependencyError(DependencyResolutionError):
    """Raised when circular dependencies are detected"""

    pass


class DIContainer:
    """Dependency Injection Container"""

    def __init__(self):
        self._descriptors: Dict[Type, DependencyDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._resolution_stack: list = []
        self.logger = logger.bind(component="di_container")

        # Register self
        self.register_instance(DIContainer, self)

    def register_singleton(
        self, interface: Type[T], implementation: Union[Type[T], Callable[[], T]]
    ) -> "DIContainer":
        """Register a singleton dependency"""
        factory = (
            implementation if callable(implementation) else lambda: implementation()
        )

        self._descriptors[interface] = DependencyDescriptor(
            dependency_type=interface, factory=factory, lifetime=Lifetime.SINGLETON
        )

        self.logger.info(
            "Registered singleton dependency",
            interface=interface.__name__,
            implementation=implementation.__name__
            if hasattr(implementation, "__name__")
            else str(implementation),
        )

        return self

    def register_transient(
        self, interface: Type[T], implementation: Union[Type[T], Callable[[], T]]
    ) -> "DIContainer":
        """Register a transient dependency (new instance each time)"""
        factory = (
            implementation if callable(implementation) else lambda: implementation()
        )

        self._descriptors[interface] = DependencyDescriptor(
            dependency_type=interface, factory=factory, lifetime=Lifetime.TRANSIENT
        )

        self.logger.info(
            "Registered transient dependency",
            interface=interface.__name__,
            implementation=implementation.__name__
            if hasattr(implementation, "__name__")
            else str(implementation),
        )

        return self

    def register_instance(self, interface: Type[T], instance: T) -> "DIContainer":
        """Register an existing instance"""
        self._descriptors[interface] = DependencyDescriptor(
            dependency_type=interface,
            instance=instance,
            lifetime=Lifetime.SINGLETON,
            initialized=True,
        )

        self._singletons[interface] = instance

        self.logger.info(
            "Registered instance",
            interface=interface.__name__,
            instance_type=type(instance).__name__,
        )

        return self

    def register_factory(
        self,
        interface: Type[T],
        factory: Callable[[], T],
        lifetime: Lifetime = Lifetime.SINGLETON,
    ) -> "DIContainer":
        """Register a factory function"""
        self._descriptors[interface] = DependencyDescriptor(
            dependency_type=interface, factory=factory, lifetime=lifetime
        )

        self.logger.info(
            "Registered factory",
            interface=interface.__name__,
            factory=factory.__name__,
            lifetime=lifetime.value,
        )

        return self

    def resolve(self, dependency_type: Type[T]) -> T:
        """Resolve a dependency"""
        # Check for circular dependencies
        if dependency_type in self._resolution_stack:
            cycle = " -> ".join(
                [t.__name__ for t in self._resolution_stack + [dependency_type]]
            )
            raise CircularDependencyError(f"Circular dependency detected: {cycle}")

        # Check if we already have a singleton instance
        if dependency_type in self._singletons:
            return self._singletons[dependency_type]

        # Get descriptor
        descriptor = self._descriptors.get(dependency_type)
        if not descriptor:
            # Try to create automatically if it's a concrete class
            if self._can_auto_create(dependency_type):
                return self._auto_create(dependency_type)

            raise DependencyResolutionError(
                f"No registration found for type {dependency_type.__name__}"
            )

        # Add to resolution stack
        self._resolution_stack.append(dependency_type)

        try:
            instance = self._create_instance(descriptor)

            # Cache singleton
            if descriptor.lifetime == Lifetime.SINGLETON:
                self._singletons[dependency_type] = instance

            self.logger.debug(
                "Resolved dependency",
                dependency_type=dependency_type.__name__,
                lifetime=descriptor.lifetime.value,
            )

            return instance

        finally:
            # Remove from resolution stack
            self._resolution_stack.pop()

    def _create_instance(self, descriptor: DependencyDescriptor) -> Any:
        """Create an instance from a descriptor"""
        if descriptor.initialized and descriptor.instance is not None:
            return descriptor.instance

        if descriptor.factory:
            # Check if factory needs dependency injection
            if self._needs_injection(descriptor.factory):
                return self._inject_dependencies(descriptor.factory)()
            else:
                return descriptor.factory()

        # Try to create using constructor injection
        return self._auto_create(descriptor.dependency_type)

    def _can_auto_create(self, dependency_type: Type) -> bool:
        """Check if we can automatically create this type"""
        return (
            inspect.isclass(dependency_type)
            and not inspect.isabstract(dependency_type)
            and not issubclass(dependency_type, ABC)
        )

    def _auto_create(self, dependency_type: Type) -> Any:
        """Automatically create instance with constructor injection"""
        try:
            constructor = dependency_type.__init__
            sig = inspect.signature(constructor)

            # Get constructor parameters (excluding 'self')
            params = list(sig.parameters.values())[1:]  # Skip 'self'

            if not params:
                # No parameters, create directly
                return dependency_type()

            # Resolve constructor dependencies
            args = []
            for param in params:
                if param.annotation and param.annotation != inspect.Parameter.empty:
                    try:
                        arg_value = self.resolve(param.annotation)
                        args.append(arg_value)
                    except DependencyResolutionError:
                        if param.default != inspect.Parameter.empty:
                            # Use default value
                            args.append(param.default)
                        else:
                            raise DependencyResolutionError(
                                f"Cannot resolve parameter '{param.name}' of type {param.annotation} "
                                f"for {dependency_type.__name__}"
                            )
                elif param.default != inspect.Parameter.empty:
                    # Use default value
                    args.append(param.default)
                else:
                    raise DependencyResolutionError(
                        f"Parameter '{param.name}' in {dependency_type.__name__} has no type annotation"
                    )

            return dependency_type(*args)

        except Exception as e:
            raise DependencyResolutionError(
                f"Failed to auto-create {dependency_type.__name__}: {str(e)}"
            ) from e

    def _needs_injection(self, func: Callable) -> bool:
        """Check if function needs dependency injection"""
        sig = inspect.signature(func)
        return any(
            param.annotation and param.annotation != inspect.Parameter.empty
            for param in sig.parameters.values()
        )

    def _inject_dependencies(self, func: Callable) -> Callable:
        """Create a wrapper that injects dependencies"""
        sig = inspect.signature(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Resolve dependencies for parameters
            bound_args = sig.bind_partial(*args, **kwargs)

            for param_name, param in sig.parameters.items():
                if param_name not in bound_args.arguments:
                    if param.annotation and param.annotation != inspect.Parameter.empty:
                        try:
                            bound_args.arguments[param_name] = self.resolve(
                                param.annotation
                            )
                        except DependencyResolutionError:
                            if param.default != inspect.Parameter.empty:
                                bound_args.arguments[param_name] = param.default
                            else:
                                raise

            return func(*bound_args.args, **bound_args.kwargs)

        return wrapper

    def is_registered(self, dependency_type: Type) -> bool:
        """Check if a type is registered"""
        return dependency_type in self._descriptors

    def override_for_testing(
        self, interface: Type[T], mock_instance: T
    ) -> "DIContainer":
        """Override a dependency for testing purposes"""
        original_descriptor = self._descriptors.get(interface)

        self.register_instance(interface, mock_instance)

        self.logger.info(
            "Dependency overridden for testing",
            interface=interface.__name__,
            mock_type=type(mock_instance).__name__,
        )

        return self

    def clear_overrides(self):
        """Clear all testing overrides"""
        self._descriptors.clear()
        self._singletons.clear()
        self.logger.info("Cleared all dependency overrides")

    def get_dependency_graph(self) -> Dict[str, list]:
        """Get dependency graph for debugging"""
        graph = {}

        for dep_type, descriptor in self._descriptors.items():
            dependencies = []

            if descriptor.factory:
                sig = inspect.signature(descriptor.factory)
                for param in sig.parameters.values():
                    if param.annotation and param.annotation != inspect.Parameter.empty:
                        dependencies.append(param.annotation.__name__)

            graph[dep_type.__name__] = dependencies

        return graph

    def validate_dependencies(self) -> list:
        """Validate all dependencies can be resolved"""
        errors = []

        for dep_type in self._descriptors.keys():
            try:
                self.resolve(dep_type)
            except DependencyResolutionError as e:
                errors.append(f"{dep_type.__name__}: {str(e)}")

        return errors


def inject(func: Callable) -> Callable:
    """Decorator for dependency injection"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get the global container
        container = get_container()
        injected_func = container._inject_dependencies(func)
        return injected_func(*args, **kwargs)

    return wrapper


# Global container instance
_global_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """Get the global DI container"""
    global _global_container
    if _global_container is None:
        _global_container = DIContainer()
    return _global_container


def configure_dependencies(container: DIContainer):
    """Configure all application dependencies"""
    from .config.settings import settings
    from .auth.jwt_manager import JWTManager
    from .auth.rbac import get_rbac_manager
    from .database.connection import get_database_manager
    from .resilience import circuit_registry

    logger.info("Configuring application dependencies")

    # Configuration
    container.register_instance(type(settings), settings)

    # Authentication & Authorization
    container.register_singleton(JWTManager, JWTManager)
    container.register_instance(type(get_rbac_manager()), get_rbac_manager())

    # Database
    container.register_instance(type(get_database_manager()), get_database_manager())

    # Circuit Breaker Registry
    container.register_instance(type(circuit_registry), circuit_registry)

    logger.info("Application dependencies configured")


def setup_dependency_injection() -> DIContainer:
    """Setup and configure the global dependency injection container"""
    container = get_container()
    configure_dependencies(container)

    # Validate all dependencies
    errors = container.validate_dependencies()
    if errors:
        logger.error("Dependency validation errors", errors=errors)
        raise DependencyResolutionError(
            f"Dependency validation failed: {'; '.join(errors)}"
        )

    logger.info("Dependency injection container setup complete")
    return container
