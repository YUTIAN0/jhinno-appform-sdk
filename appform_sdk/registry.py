"""
API Registry for managing and extending API endpoints
"""

import copy
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type

from .utils import compare_versions as _compare_versions


@dataclass
class EndpointDefinition:
    """Definition of an API endpoint."""

    path: str
    method: str
    name: str
    description: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    deprecated: bool = False
    version_added: str = "1.0.0"
    version_deprecated: Optional[str] = None


class APIRegistry:
    """
    Registry for managing API endpoints.

    Supports:
    - Registering custom endpoints
    - Versioning endpoints
    - Overriding existing endpoints
    - Loading endpoints from configuration
    """

    def __init__(self, version: str = "1.0.0"):
        """
        Initialize the API registry.

        Args:
            version: Current API version
        """
        self._version = version
        self._endpoints: Dict[str, EndpointDefinition] = {}
        self._custom_handlers: Dict[str, Callable] = {}
        self._extensions: List[str] = []

    @property
    def version(self) -> str:
        """Get current API version."""
        return self._version

    @version.setter
    def version(self, value: str):
        """Set API version."""
        self._version = value

    def register(
        self,
        name: str,
        path: str,
        method: str = "GET",
        description: str = "",
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        version_added: str = "1.0.0",
        version_deprecated: Optional[str] = None,
        override: bool = False,
    ) -> "APIRegistry":
        """
        Register an API endpoint.

        Args:
            name: Unique endpoint name (e.g., "jobs.list", "auth.login")
            path: API path (e.g., "/appform/ws/api/jobs/page")
            method: HTTP method (GET, POST, PUT, DELETE)
            description: Endpoint description
            params: Default parameters
            headers: Additional headers
            version_added: Version when this endpoint was added
            version_deprecated: Version when this endpoint was deprecated
            override: Whether to override existing endpoint

        Returns:
            Self for chaining

        Raises:
            ValueError: If endpoint already exists and override=False
        """
        if name in self._endpoints and not override:
            raise ValueError(
                f"Endpoint '{name}' already exists. Use override=True to replace."
            )

        endpoint = EndpointDefinition(
            path=path,
            method=method.upper(),
            name=name,
            description=description,
            params=params or {},
            headers=headers or {},
            version_added=version_added,
            version_deprecated=version_deprecated,
        )

        self._endpoints[name] = endpoint
        return self

    def unregister(self, name: str) -> bool:
        """
        Unregister an endpoint.

        Args:
            name: Endpoint name

        Returns:
            True if endpoint was removed, False if not found
        """
        if name in self._endpoints:
            del self._endpoints[name]
            return True
        return False

    def get(self, name: str) -> Optional[EndpointDefinition]:
        """
        Get endpoint definition.

        Args:
            name: Endpoint name

        Returns:
            Endpoint definition or None if not found
        """
        return self._endpoints.get(name)

    def get_all(self) -> Dict[str, EndpointDefinition]:
        """Get all registered endpoints."""
        return copy.deepcopy(self._endpoints)

    def get_for_version(self, version: str = None) -> Dict[str, EndpointDefinition]:
        """
        Get endpoints available for a specific version.

        Args:
            version: Target version (defaults to current version)

        Returns:
            Dictionary of available endpoints
        """
        target_version = version or self._version
        result = {}

        for name, endpoint in self._endpoints.items():
            # Check if endpoint was added before or at target version
            if _compare_versions(endpoint.version_added, target_version) <= 0:
                # Check if endpoint is not deprecated in target version
                if (
                    endpoint.version_deprecated is None
                    or _compare_versions(
                        endpoint.version_deprecated, target_version
                    )
                    > 0
                ):
                    result[name] = endpoint

        return result

    def register_handler(self, name: str, handler: Callable) -> "APIRegistry":
        """
        Register a custom handler for an endpoint.

        Args:
            name: Endpoint name
            handler: Custom handler function

        Returns:
            Self for chaining
        """
        self._custom_handlers[name] = handler
        return self

    def get_handler(self, name: str) -> Optional[Callable]:
        """Get custom handler for an endpoint."""
        return self._custom_handlers.get(name)

    def add_extension(self, extension_name: str) -> "APIRegistry":
        """
        Register an extension module.

        Args:
            extension_name: Name of the extension

        Returns:
            Self for chaining
        """
        if extension_name not in self._extensions:
            self._extensions.append(extension_name)
        return self

    def get_extensions(self) -> List[str]:
        """Get list of registered extensions."""
        return self._extensions.copy()

    def load_from_dict(
        self, config: Dict[str, Any], override: bool = False
    ) -> "APIRegistry":
        """
        Load endpoints from a dictionary configuration.

        Args:
            config: Dictionary with endpoint definitions
            override: Whether to override existing endpoints

        Returns:
            Self for chaining
        """
        for name, endpoint_config in config.items():
            self.register(
                name=name,
                path=endpoint_config.get("path", ""),
                method=endpoint_config.get("method", "GET"),
                description=endpoint_config.get("description", ""),
                params=endpoint_config.get("params"),
                headers=endpoint_config.get("headers"),
                version_added=endpoint_config.get("version_added", "1.0.0"),
                version_deprecated=endpoint_config.get("version_deprecated"),
                override=override,
            )
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Export endpoints to dictionary."""
        result = {}
        for name, endpoint in self._endpoints.items():
            result[name] = {
                "path": endpoint.path,
                "method": endpoint.method,
                "description": endpoint.description,
                "params": endpoint.params,
                "headers": endpoint.headers,
                "version_added": endpoint.version_added,
                "version_deprecated": endpoint.version_deprecated,
                "deprecated": endpoint.deprecated,
            }
        return result


# Global registry instance
_global_registry: Optional[APIRegistry] = None


def get_registry(version: str = "1.0.0") -> APIRegistry:
    """
    Get the global API registry.

    Args:
        version: API version (only used on first call)

    Returns:
        Global APIRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = APIRegistry(version)
    return _global_registry


def reset_registry():
    """Reset the global registry (mainly for testing)."""
    global _global_registry
    _global_registry = None
