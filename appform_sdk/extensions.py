"""
Extensions system for Appform SDK

Supports:
- Custom API endpoints
- Version-specific endpoints
- Environment-specific customizations
- Endpoint overrides
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

from .registry import APIRegistry, EndpointDefinition, get_registry
from .utils import compare_versions as _compare_versions


@dataclass
class ExtensionConfig:
    """Configuration for an extension."""

    name: str
    version: str
    description: str = ""
    endpoints: Dict[str, Dict[str, Any]] = None
    overrides: Dict[str, Dict[str, Any]] = None
    requires: List[str] = None

    def __post_init__(self):
        if self.endpoints is None:
            self.endpoints = {}
        if self.overrides is None:
            self.overrides = {}
        if self.requires is None:
            self.requires = []


class Extension:
    """
    Base class for SDK extensions.

    Extensions can:
    - Add new API endpoints
    - Override existing endpoints
    - Add custom functionality
    """

    def __init__(self, config: ExtensionConfig):
        """
        Initialize the extension.

        Args:
            config: Extension configuration
        """
        self.config = config
        self._registered = False

    def register(self, registry: APIRegistry) -> None:
        """
        Register the extension with the API registry.

        Args:
            registry: API registry instance
        """
        if self._registered:
            return

        # Register new endpoints
        for name, endpoint_config in self.config.endpoints.items():
            registry.register(
                name=name,
                path=endpoint_config.get("path", ""),
                method=endpoint_config.get("method", "GET"),
                description=endpoint_config.get("description", ""),
                params=endpoint_config.get("params"),
                headers=endpoint_config.get("headers"),
                version_added=endpoint_config.get("version_added", self.config.version),
                override=False,
            )

        # Override existing endpoints
        for name, endpoint_config in self.config.overrides.items():
            registry.register(
                name=name,
                path=endpoint_config.get("path", ""),
                method=endpoint_config.get("method", "GET"),
                description=endpoint_config.get("description", ""),
                params=endpoint_config.get("params"),
                headers=endpoint_config.get("headers"),
                version_added=endpoint_config.get("version_added", self.config.version),
                override=True,
            )

        registry.add_extension(self.config.name)
        self._registered = True

    def unregister(self, registry: APIRegistry) -> None:
        """
        Unregister the extension.

        Args:
            registry: API registry instance
        """
        for name in self.config.endpoints:
            registry.unregister(name)
        self._registered = False


class ExtensionManager:
    """
    Manager for SDK extensions.

    Handles loading, registering, and managing extensions.
    """

    def __init__(self, registry: APIRegistry = None):
        """
        Initialize the extension manager.

        Args:
            registry: API registry (defaults to global registry)
        """
        self._registry = registry or get_registry()
        self._extensions: Dict[str, Extension] = {}

    @property
    def registry(self) -> APIRegistry:
        """Get the API registry."""
        return self._registry

    def register(self, extension: Extension) -> None:
        """
        Register an extension.

        Args:
            extension: Extension to register

        Raises:
            ValueError: If extension already registered
        """
        if extension.config.name in self._extensions:
            raise ValueError(
                f"Extension '{extension.config.name}' is already registered"
            )

        # Check dependencies
        for required in extension.config.requires:
            if required not in self._extensions:
                raise ValueError(
                    f"Extension '{extension.config.name}' requires '{required}'"
                )

        extension.register(self._registry)
        self._extensions[extension.config.name] = extension

    def unregister(self, name: str) -> bool:
        """
        Unregister an extension.

        Args:
            name: Extension name

        Returns:
            True if extension was unregistered
        """
        if name in self._extensions:
            extension = self._extensions[name]
            extension.unregister(self._registry)
            del self._extensions[name]
            return True
        return False

    def get(self, name: str) -> Optional[Extension]:
        """Get a registered extension by name."""
        return self._extensions.get(name)

    def list_extensions(self) -> List[str]:
        """Get list of registered extension names."""
        return list(self._extensions.keys())

    def load_from_file(self, file_path: str) -> Extension:
        """
        Load extension from a JSON configuration file.

        Args:
            file_path: Path to extension configuration file

        Returns:
            Loaded and registered extension
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Extension file not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        config = ExtensionConfig(
            name=config_data.get("name", path.stem),
            version=config_data.get("version", "1.0.0"),
            description=config_data.get("description", ""),
            endpoints=config_data.get("endpoints", {}),
            overrides=config_data.get("overrides", {}),
            requires=config_data.get("requires", []),
        )

        extension = Extension(config)
        self.register(extension)
        return extension

    def load_from_dict(self, config_dict: Dict[str, Any]) -> Extension:
        """
        Load extension from a dictionary.

        Args:
            config_dict: Extension configuration dictionary

        Returns:
            Loaded and registered extension
        """
        config = ExtensionConfig(
            name=config_dict.get("name", "custom"),
            version=config_dict.get("version", "1.0.0"),
            description=config_dict.get("description", ""),
            endpoints=config_dict.get("endpoints", {}),
            overrides=config_dict.get("overrides", {}),
            requires=config_dict.get("requires", []),
        )

        extension = Extension(config)
        self.register(extension)
        return extension


class DynamicAPI:
    """
    Dynamic API that uses the registry for endpoint resolution.

    Allows calling endpoints by name with automatic parameter handling.
    """

    def __init__(self, client, registry: APIRegistry = None):
        """
        Initialize dynamic API.

        Args:
            client: AppformClient instance
            registry: API registry (defaults to global)
        """
        self._client = client
        self._registry = registry or get_registry()

    def call(
        self,
        endpoint_name: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        path_params: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Call an API endpoint by name.

        Args:
            endpoint_name: Registered endpoint name (e.g., "jobs.list")
            params: Query parameters
            data: Form data
            json_data: JSON body data
            headers: Additional headers
            path_params: Parameters to substitute in path
            **kwargs: Additional parameters

        Returns:
            API response

        Raises:
            ValueError: If endpoint not found
        """
        endpoint = self._registry.get(endpoint_name)
        if endpoint is None:
            raise ValueError(f"Endpoint '{endpoint_name}' not found in registry")

        # Check for custom handler
        handler = self._registry.get_handler(endpoint_name)
        if handler:
            return handler(
                self._client, params=params, data=data, json_data=json_data, **kwargs
            )

        # Build path with path parameters
        path = endpoint.path
        if path_params:
            for key, value in path_params.items():
                path = path.replace(f"{{{key}}}", str(value))

        # Merge default params with provided params
        merged_params = {**endpoint.params, **(params or {})}
        merged_headers = {**endpoint.headers, **(headers or {})}

        # Make request
        return self._client.request(
            method=endpoint.method,
            path=path,
            params=merged_params if merged_params else None,
            data=data,
            json=json_data,
            headers=merged_headers if merged_headers else None,
            **kwargs,
        )

    def __getattr__(self, name: str):
        """Allow calling endpoints as methods."""

        # Support dot notation like api.jobs_list() or api.jobs.list()
        def make_call(endpoint_name: str):
            def call(**kwargs):
                return self.call(endpoint_name, **kwargs)

            call.__name__ = endpoint_name
            return call

        # Try exact match first
        if self._registry.get(name):
            return make_call(name)

        # Try with dots replaced
        dotted_name = name.replace("_", ".")
        if self._registry.get(dotted_name):
            return make_call(dotted_name)

        raise AttributeError(f"No endpoint '{name}' or '{dotted_name}' found")


def create_version_specific_registry(
    base_version: str,
    version_specific_endpoints: Dict[str, Dict[str, Any]],
) -> APIRegistry:
    """
    Create a version-specific API registry.

    Args:
        base_version: Base API version
        version_specific_endpoints: Endpoints specific to this version

    Returns:
        Configured API registry
    """
    registry = APIRegistry(base_version)

    for name, config in version_specific_endpoints.items():
        registry.register(
            name=name,
            path=config.get("path", ""),
            method=config.get("method", "GET"),
            description=config.get("description", ""),
            params=config.get("params"),
            headers=config.get("headers"),
            version_added=config.get("version_added", base_version),
            override=config.get("override", False),
        )

    return registry


# Default endpoints for Appform 6.0-6.5 (base endpoints)
DEFAULT_ENDPOINTS = {
    # ==================== Authentication ====================
    "auth.login": {
        "path": "/appform/ws/api/auth/login",
        "method": "GET",
        "description": "Login with username and password",
        "version_added": "6.0",
    },
    "auth.token": {
        "path": "/appform/ws/api/auth/token",
        "method": "GET",
        "description": "Login with encrypted token",
        "version_added": "6.0",
    },
    "auth.logout": {
        "path": "/appform/ws/api/auth/logout",
        "method": "DELETE",
        "description": "Logout",
        "version_added": "6.0",
    },
    "auth.ping": {
        "path": "/appform/ws/api/ping",
        "method": "GET",
        "description": "Test service connection",
        "version_added": "6.0",
    },
    "auth.register": {
        "path": "/appform/ws/api/auth/register",
        "method": "POST",
        "description": "Register new user",
        "version_added": "6.0",
    },
    "auth.checkUpload": {
        "path": "/appform/ws/api/checkUploadToken",
        "method": "GET",
        "description": "Check upload permission",
        "version_added": "6.0",
    },
    "auth.checkDownload": {
        "path": "/appform/ws/api/checkDownloadToken",
        "method": "GET",
        "description": "Check download permission",
        "version_added": "6.0",
    },
    # ==================== Jobs ====================
    "jobs.submit": {
        "path": "/appform/ws/api/jobs/jsub",
        "method": "POST",
        "description": "Submit a job",
        "version_added": "6.0",
    },
    "jobs.get": {
        "path": "/appform/ws/api/jobs/{jobId}",
        "method": "GET",
        "description": "Get job details",
        "version_added": "6.0",
    },
    "jobs.list": {
        "path": "/appform/ws/api/jobs/page",
        "method": "GET",
        "description": "List jobs with pagination",
        "version_added": "6.0",
    },
    "jobs.listByIds": {
        "path": "/appform/ws/api/jobs/list",
        "method": "GET",
        "description": "List jobs by IDs",
        "version_added": "6.0",
    },
    "jobs.action": {
        "path": "/appform/ws/api/jobs/{jobId}/{action}",
        "method": "PUT",
        "description": "Perform action on job (stop/suspend/resume/requeue)",
        "version_added": "6.0",
    },
    "jobs.batchAction": {
        "path": "/appform/ws/api/jobs/{action}",
        "method": "PUT",
        "description": "Batch action on multiple jobs",
        "version_added": "6.0",
    },
    "jobs.history": {
        "path": "/appform/ws/api/jobs/{jobId}/hist",
        "method": "GET",
        "description": "Get job history",
        "version_added": "6.0",
    },
    "jobs.batchHistory": {
        "path": "/appform/ws/api/jobs/hist",
        "method": "GET",
        "description": "Batch get job history",
        "version_added": "6.0",
    },
    "jobs.output": {
        "path": "/appform/ws/api/jobs/{jobId}/peek",
        "method": "GET",
        "description": "Get job output",
        "version_added": "6.0",
    },
    "jobs.files": {
        "path": "/appform/ws/api/jobs/{jobId}/files",
        "method": "GET",
        "description": "Get job files",
        "version_added": "6.0",
    },
    "jobs.connect": {
        "path": "/appform/ws/api/jobs/{jobId}/connect",
        "method": "POST",
        "description": "Connect to job",
        "version_added": "6.0",
    },
    "jobs.historyPage": {
        "path": "/appform/ws/api/jobs/historyPage",
        "method": "GET",
        "description": "List history jobs with pagination",
        "version_added": "6.0",
    },
    # ==================== Sessions ====================
    "sessions.start": {
        "path": "/appform/ws/api/apps/{appId}/start",
        "method": "POST",
        "description": "Start a session",
        "version_added": "6.0",
    },
    "sessions.listAll": {
        "path": "/appform/ws/api/apps/sessions/all",
        "method": "GET",
        "description": "List all sessions",
        "version_added": "6.0",
    },
    "sessions.list": {
        "path": "/appform/ws/api/apps/sessions",
        "method": "GET",
        "description": "List sessions",
        "version_added": "6.0",
    },
    "sessions.share": {
        "path": "/appform/ws/api/apps/sessions/{sessionId}/share",
        "method": "POST",
        "description": "Share session",
        "version_added": "6.0",
    },
    "sessions.cancelShare": {
        "path": "/appform/ws/api/apps/sessions/{sessionsId}/share_cancel",
        "method": "PUT",
        "description": "Cancel session sharing",
        "version_added": "6.0",
    },
    "sessions.transferOperation": {
        "path": "/appform/ws/api/apps/sessions/{sessionId}/operation_transfer",
        "method": "PUT",
        "description": "Transfer session operation",
        "version_added": "6.0",
    },
    "sessions.connect": {
        "path": "/appform/ws/api/apps/sessions/{sessionId}/connect",
        "method": "GET",
        "description": "Connect to session",
        "version_added": "6.0",
    },
    "sessions.disconnect": {
        "path": "/appform/ws/api/apps/sessions/{sessionId}/disconnect",
        "method": "PUT",
        "description": "Disconnect from session",
        "version_added": "6.0",
    },
    "sessions.batchDisconnect": {
        "path": "/appform/ws/api/apps/sessions/disconnect",
        "method": "PUT",
        "description": "Batch disconnect sessions",
        "version_added": "6.0",
    },
    "sessions.close": {
        "path": "/appform/ws/api/apps/sessions/{sessionId}/close",
        "method": "PUT",
        "description": "Close session",
        "version_added": "6.0",
    },
    "sessions.batchClose": {
        "path": "/appform/ws/api/apps/sessions/close",
        "method": "PUT",
        "description": "Batch close sessions",
        "version_added": "6.0",
    },
    "sessions.webclientConnect": {
        "path": "/appform/ws/api/apps/webclient/{sessionId}/connect",
        "method": "GET",
        "description": "Connect to session via web browser",
        "version_added": "6.0",
    },
    # ==================== Applications ====================
    "apps.list": {
        "path": "/appform/ws/api/apps",
        "method": "GET",
        "description": "List all applications",
        "version_added": "6.0",
    },
    "apps.url": {
        "path": "/appform/ws/api/apps/{appName}/url",
        "method": "GET",
        "description": "Get application URL",
        "version_added": "6.0",
    },
    "apps.formParams": {
        "path": "/appform/appstore/app-info/v1/form_params",
        "method": "GET",
        "description": "Get compute app form params",
        "version_added": "6.0",
    },
    "apps.fileExtensions": {
        "path": "/appform/appstore/app-info/v1/user/findChooseBaseList",
        "method": "GET",
        "description": "Get file extensions for graphical apps",
        "version_added": "6.0",
    },
    # ==================== Files ====================
    "files.list": {
        "path": "/appform/ws/api/files",
        "method": "GET",
        "description": "List files",
        "version_added": "6.0",
    },
    "files.mkdir": {
        "path": "/appform/ws/api/files/mkdir",
        "method": "POST",
        "description": "Create directory",
        "version_added": "6.0",
    },
    "files.rename": {
        "path": "/appform/ws/api/files/rename",
        "method": "PUT",
        "description": "Rename file",
        "version_added": "6.0",
    },
    "files.copy": {
        "path": "/appform/ws/api/files/copy",
        "method": "PUT",
        "description": "Copy files",
        "version_added": "6.0",
    },
    "files.delete": {
        "path": "/appform/ws/api/files/delete",
        "method": "DELETE",
        "description": "Delete files",
        "version_added": "6.0",
    },
    "files.upload": {
        "path": "/appform/ws/api/files/upload",
        "method": "POST",
        "description": "Upload file",
        "version_added": "6.0",
    },
    "files.download": {
        "path": "/appform/ws/api/files/download",
        "method": "GET",
        "description": "Download file",
        "version_added": "6.0",
    },
    "files.compress": {
        "path": "/appform/ws/api/files/compress",
        "method": "POST",
        "description": "Compress files",
        "version_added": "6.0",
    },
    "files.uncompress": {
        "path": "/appform/ws/api/files/uncompress",
        "method": "POST",
        "description": "Uncompress files",
        "version_added": "6.0",
    },
    # ==================== Organization ====================
    "org.departments": {
        "path": "/appform/ws/api/deps",
        "method": "GET",
        "description": "Get departments tree",
        "version_added": "6.0",
    },
    "org.createDepartment": {
        "path": "/appform/ws/api/deps",
        "method": "POST",
        "description": "Create department",
        "version_added": "6.0",
    },
    "org.updateDepartment": {
        "path": "/appform/ws/api/deps/{depName}",
        "method": "PUT",
        "description": "Update department",
        "version_added": "6.0",
    },
    "org.deleteDepartment": {
        "path": "/appform/ws/api/deps/{depName}",
        "method": "DELETE",
        "description": "Delete department",
        "version_added": "6.0",
    },
    "org.users": {
        "path": "/appform/ws/api/users",
        "method": "GET",
        "description": "Get users",
        "version_added": "6.0",
    },
    "org.createUser": {
        "path": "/appform/ws/api/users",
        "method": "POST",
        "description": "Create user",
        "version_added": "6.0",
    },
    "org.updateUser": {
        "path": "/appform/ws/api/users/{username}",
        "method": "PUT",
        "description": "Update user",
        "version_added": "6.0",
    },
    "org.deleteUser": {
        "path": "/appform/ws/api/users/{username}",
        "method": "DELETE",
        "description": "Delete user",
        "version_added": "6.0",
    },
    "org.resetPassword": {
        "path": "/appform/ws/api/users/{username}/password/password_reset",
        "method": "POST",
        "description": "Reset user password",
        "version_added": "6.0",
    },
    # ==================== System ====================
    "system.serverTime": {
        "path": "/appform/systemInfo/serverTime",
        "method": "GET",
        "description": "Get server time",
        "version_added": "6.0",
    },
    "system.theme": {
        "path": "/appform/systemInfo/theme",
        "method": "GET",
        "description": "Get portal theme",
        "version_added": "6.0",
    },
    "system.rootDir": {
        "path": "/appform/fm/getRootDir",
        "method": "GET",
        "description": "Get root directory info",
        "version_added": "6.0",
    },
    "system.jobStats": {
        "path": "/appform/workspace/getAllJobInfoStatics",
        "method": "GET",
        "description": "Get job statistics",
        "version_added": "6.0",
    },
    "system.notificationCount": {
        "path": "/appform/notification/count",
        "method": "GET",
        "description": "Get notification count",
        "version_added": "6.0",
    },
    "system.notificationRead": {
        "path": "/appform/notification/read",
        "method": "POST",
        "description": "Mark all notifications as read",
        "version_added": "6.0",
    },
    # ==================== Jobs (deprecated 6.0) ====================
    "jobs.byName": {
        "path": "/appform/ws/api/jobs/byName",
        "method": "GET",
        "description": "Search jobs by name (deprecated)",
        "version_added": "6.0",
        "version_deprecated": "6.0",
    },
    "jobs.byStatus": {
        "path": "/appform/ws/api/jobs/byStatus/{status}",
        "method": "GET",
        "description": "Search jobs by status (deprecated)",
        "version_added": "6.0",
        "version_deprecated": "6.0",
    },
}

# Endpoints added in version 6.5
ENDPOINTS_6_5 = {
    "files.getConfidentiality": {
        "path": "/appform/ws/api/file/conf",
        "method": "GET",
        "description": "Get file confidentiality levels",
        "version_added": "6.5",
    },
    "files.setConfidentiality": {
        "path": "/appform/ws/api/file/conf",
        "method": "POST",
        "description": "Set file confidentiality level",
        "version_added": "6.5",
    },
}

# Endpoints added in version 6.6
ENDPOINTS_6_6 = {
    # ==================== V2 Jobs API ====================
    "jobs.getForm": {
        "path": "/appform/ws/api/v2/app/form/{appId}",
        "method": "GET",
        "description": "Get job submission form for an app",
        "version_added": "6.6",
    },
    "jobs.submitV2": {
        "path": "/appform/ws/api/v2/jobs",
        "method": "POST",
        "description": "Submit job v2 (with form params)",
        "version_added": "6.6",
    },
    "jobs.listV2": {
        "path": "/appform/ws/api/v2/jobs",
        "method": "GET",
        "description": "List jobs v2 with pagination",
        "version_added": "6.6",
    },
    "jobs.deleteV2": {
        "path": "/appform/ws/api/v2/jobs/{jobId}",
        "method": "DELETE",
        "description": "Delete a job",
        "version_added": "6.6",
    },
    "jobs.tooltip": {
        "path": "/appform/ws/api/v2/jobs/tooltip",
        "method": "GET",
        "description": "Get job app monitoring info",
        "version_added": "6.6",
    },
    "jobs.totalHistory": {
        "path": "/appform/workspace/myjob/totalHistory",
        "method": "GET",
        "description": "Get total history job count",
        "version_added": "6.6",
    },
    # ==================== V2 Session API ====================
    "sessions.startV2": {
        "path": "/appform/ws/api/v2/app_session",
        "method": "POST",
        "description": "Start session v2 (returns client and web connection)",
        "version_added": "6.6",
    },
    # ==================== V2 Apps API ====================
    "apps.listV2": {
        "path": "/appform/ws/api/v2/apps",
        "method": "GET",
        "description": "Get available compute, interactive, and web apps",
        "version_added": "6.6",
    },
    # ==================== Storage & Count ====================
    "quota.storage": {
        "path": "/appform/diskquota/quotaStorage",
        "method": "GET",
        "description": "Get user storage quota information",
        "version_added": "6.6",
    },
    "count.appsCpu": {
        "path": "/appform/count/appsCpu",
        "method": "GET",
        "description": "Get available cores and pending jobs for a specific app",
        "version_added": "6.6",
    },
    "count.allAppsCpu": {
        "path": "/appform/count/allAppsCpu",
        "method": "GET",
        "description": "Get usage info for all available simulation apps",
        "version_added": "6.6",
    },
}


def init_default_registry(version: str = "6.5") -> APIRegistry:
    """
    Initialize the default API registry with standard endpoints.

    Supports versions: 6.0, 6.3, 6.5, 6.6

    Args:
        version: API version (default: 6.5)

    Returns:
        Configured API registry
    """
    registry = APIRegistry(version)

    # Load base endpoints (6.0+)
    registry.load_from_dict(DEFAULT_ENDPOINTS)

    # Load version-specific endpoints
    # For version 6.5 and above, add 6.5 endpoints
    if _compare_versions(version, "6.5") >= 0:
        registry.load_from_dict(ENDPOINTS_6_5)

    # For version 6.6 and above, add 6.6 endpoints
    if _compare_versions(version, "6.6") >= 0:
        registry.load_from_dict(ENDPOINTS_6_6)

    return registry


# Version constants
VERSION_6_0 = "6.0"
VERSION_6_3 = "6.3"
VERSION_6_5 = "6.5"
VERSION_6_6 = "6.6"

# List of supported versions
SUPPORTED_VERSIONS = [VERSION_6_0, VERSION_6_3, VERSION_6_5, VERSION_6_6]
