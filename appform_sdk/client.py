"""
Appform API Client
"""

import getpass
import os
from typing import Any, Dict, Optional, Union

import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.exceptions import InsecureRequestWarning
from urllib3.util.retry import Retry

from .apps import AppsAPI
from .auth import AuthAPI
from .config import Config
from .exceptions import APIError, AppformError, AuthenticationError
from .extensions import DynamicAPI, ExtensionManager, init_default_registry
from .files import FilesAPI
from .jobs import JobsAPI
from .organization import OrganizationAPI
from .registry import APIRegistry
from .sessions import SessionsAPI
from .sftp import SFTPAPI
from .utils import SignatureGenerator


def _get_current_username() -> Optional[str]:
    """
    Get the current system username using multiple methods.
    Priority: USER env var > USERNAME env var > getpass.getuser() > pwd module.
    """
    username = os.getenv("USER") or os.getenv("USERNAME")
    if username:
        return username
    try:
        username = getpass.getuser()
        if username:
            return username
    except Exception:
        pass
    try:
        import pwd

        username = pwd.getpwuid(os.getuid()).pw_name
        if username:
            return username
    except Exception:
        pass
    return None


class AppformClient:
    """
    Appform API Client for interacting with Appform 6.5 services.

    Usage:
        # Token authentication
        client = AppformClient(base_url="https://your-appform-server.com")
        client.auth.login(username="user", password="pass")
        jobs = client.jobs.list_jobs()

        # AccessKey authentication
        client = AppformClient(
            base_url="https://your-appform-server.com",
            access_key="your_access_key",
            access_key_secret="your_access_key_secret",
            username="your_username"
        )
        jobs = client.jobs.list_jobs()

        # With version and extensions
        client = AppformClient(
            base_url="https://your-appform-server.com",
            api_version="6.6",
            extensions_dir="/path/to/extensions"
        )
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        access_key: Optional[str] = None,
        access_key_secret: Optional[str] = None,
        username: Optional[str] = None,
        aes_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        verify_ssl: Optional[bool] = None,
        api_version: Optional[str] = None,
        extensions_dir: Optional[str] = None,
        config: Optional[Config] = None,
    ):
        """
        Initialize the Appform client.

        Args:
            base_url: The base URL of the Appform server (e.g., "https://server.com")
            token: Optional pre-existing authentication token
            access_key: Access key for AccessKey authentication
            access_key_secret: Access key secret for AccessKey authentication (used for signature, NOT sent in headers)
            username: Username for AccessKey authentication (used in request header)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            verify_ssl: Whether to verify SSL certificates
            api_version: API version to use (e.g., "6.5", "7.0")
            extensions_dir: Directory containing extension configurations
            config: Configuration object (alternative to individual parameters)
        """
        # Support initialization from Config object
        if config:
            base_url = base_url if base_url is not None else config.base_url
            token = token if token is not None else config.token
            access_key = access_key if access_key is not None else config.access_key
            access_key_secret = (
                access_key_secret
                if access_key_secret is not None
                else config.access_key_secret
            )
            username = username if username is not None else config.username
            aes_key = aes_key if aes_key is not None else config.aes_key
            timeout = timeout if timeout is not None else config.timeout
            if verify_ssl is None:
                verify_ssl = config.verify_ssl
            api_version = api_version or config.api_version
            extensions_dir = extensions_dir or config.extensions_dir

        self.base_url = base_url.rstrip("/") if base_url else ""
        self._token = token
        self._access_key = access_key
        self._access_key_secret = access_key_secret
        # Auto-detect current system username if not specified
        self._username = username or _get_current_username()
        self._aes_key = aes_key
        self.timeout = timeout
        self.verify_ssl = verify_ssl if verify_ssl is not None else True
        self._api_version = api_version or "6.5"
        self._extensions_dir = extensions_dir

        # SFTP configuration
        self._sftp_host = None
        self._sftp_port = 22
        self._sftp_username = None
        self._sftp_password = None
        self._sftp_key_file = None
        self._sftp_key_password = None
        if config:
            self._sftp_host = config.sftp_host
            self._sftp_port = config.sftp_port
            self._sftp_username = config.sftp_username or config.username
            self._sftp_password = config.sftp_password or config.password
            self._sftp_key_file = config.sftp_key_file
            self._sftp_key_password = config.sftp_key_password
            # Auto-extract host from base_url if sftp_host not set
            if not self._sftp_host and self.base_url:
                from urllib.parse import urlparse

                parsed = urlparse(self.base_url)
                if parsed.hostname:
                    self._sftp_host = parsed.hostname

        # Suppress urllib3 InsecureRequestWarning when SSL verification is disabled
        if not self.verify_ssl:
            urllib3.disable_warnings(InsecureRequestWarning)

        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD", "OPTIONS"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Initialize API registry and extension manager
        self._registry = init_default_registry(self._api_version)
        self._extension_manager = ExtensionManager(self._registry)

        # Load extensions if directory is specified
        if self._extensions_dir:
            self._load_extensions()

        # Initialize API modules
        self._auth = AuthAPI(self)
        self._jobs = JobsAPI(self)
        self._sessions = SessionsAPI(self)
        self._apps = AppsAPI(self)
        self._files = FilesAPI(self)
        self._organization = OrganizationAPI(self)
        self._sftp_api = None

        # Initialize dynamic API
        self._dynamic_api = DynamicAPI(self, self._registry)

    def _load_extensions(self):
        """Load extensions from the extensions directory."""
        from pathlib import Path

        ext_dir = Path(self._extensions_dir)
        if ext_dir.exists() and ext_dir.is_dir():
            for ext_file in ext_dir.glob("*.json"):
                try:
                    self._extension_manager.load_from_file(str(ext_file))
                except Exception as e:
                    import warnings

                    warnings.warn(
                        f"Failed to load extension '{ext_file.name}': {e}",
                        UserWarning,
                    )

    @property
    def token(self) -> Optional[str]:
        """Get the current authentication token."""
        return self._token

    @token.setter
    def token(self, value: str):
        """Set the authentication token."""
        self._token = value

    @property
    def access_key(self) -> Optional[str]:
        """Get the access key."""
        return self._access_key

    @access_key.setter
    def access_key(self, value: str):
        """Set the access key."""
        self._access_key = value

    @property
    def access_key_secret(self) -> Optional[str]:
        """Get the access key secret."""
        return self._access_key_secret

    @access_key_secret.setter
    def access_key_secret(self, value: str):
        """Set the access key secret."""
        self._access_key_secret = value

    @property
    def username(self) -> Optional[str]:
        """Get the username."""
        return self._username

    @username.setter
    def username(self, value: str):
        """Set the username."""
        self._username = value

    @property
    def api_version(self) -> str:
        """Get the API version."""
        return self._api_version

    @property
    def registry(self) -> APIRegistry:
        """Get the API registry."""
        return self._registry

    @property
    def extension_manager(self) -> ExtensionManager:
        """Get the extension manager."""
        return self._extension_manager

    @property
    def auth(self) -> AuthAPI:
        """Access authentication APIs."""
        return self._auth

    @property
    def jobs(self) -> JobsAPI:
        """Access job APIs."""
        return self._jobs

    @property
    def sessions(self) -> SessionsAPI:
        """Access session APIs."""
        return self._sessions

    @property
    def apps(self) -> AppsAPI:
        """Access application APIs."""
        return self._apps

    @property
    def files(self) -> FilesAPI:
        """Access file APIs."""
        return self._files

    @property
    def organization(self) -> OrganizationAPI:
        """Access organization APIs."""
        return self._organization

    @property
    def sftp(self) -> SFTPAPI:
        """Access SFTP APIs."""
        if self._sftp_api is None:
            self._sftp_api = SFTPAPI(self)
        return self._sftp_api

    @property
    def api(self) -> DynamicAPI:
        """Access dynamic API for calling registered endpoints."""
        return self._dynamic_api

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers including authentication."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Token authentication
        if self._token:
            headers["token"] = self._token

        # AccessKey authentication
        # Generate signature dynamically for each request
        if self._access_key and self._access_key_secret:
            # Auto-detect current system username if not specified
            username = self._username
            if not username:
                username = _get_current_username()
            auth_headers = SignatureGenerator.generate_auth_headers(
                access_key=self._access_key,
                access_key_secret=self._access_key_secret,
                username=username or "",
            )
            headers.update(auth_headers)

        return headers

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        raw_response: bool = False,
    ) -> Union[Dict[str, Any], requests.Response]:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: API endpoint path
            params: Query parameters
            data: Form data
            json: JSON body data
            files: Files to upload
            headers: Additional headers
            raw_response: Return raw response instead of parsed JSON

        Returns:
            API response as dict or raw Response object

        Raises:
            AuthenticationError: If authentication fails
            APIError: If API returns an error
            AppformError: For other errors
        """
        url = f"{self.base_url}{path}"
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)

        # Remove Content-Type for file uploads
        if files:
            request_headers.pop("Content-Type", None)

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json,
                files=files,
                headers=request_headers,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )

            if raw_response:
                return response

            # Parse response
            try:
                result = response.json()
            except ValueError:
                result = {"code": response.status_code, "message": response.text}

            # Check for API errors
            if response.status_code >= 400:
                message = result.get("message", "Unknown error")
                if response.status_code == 401 or "无效的安全令牌" in message:
                    raise AuthenticationError(message)
                raise APIError(message, response.status_code, result)

            return result

        except requests.exceptions.RequestException as e:
            raise AppformError(f"Request failed: {e}") from e

    def get(self, path: str, **kwargs) -> Dict[str, Any]:
        """Make a GET request."""
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> Dict[str, Any]:
        """Make a POST request."""
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> Dict[str, Any]:
        """Make a PUT request."""
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs) -> Dict[str, Any]:
        """Make a DELETE request."""
        return self.request("DELETE", path, **kwargs)

    def call_endpoint(
        self,
        endpoint_name: str,
        path_params: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Call an API endpoint by name from the registry.

        Args:
            endpoint_name: Registered endpoint name (e.g., "jobs.list")
            path_params: Parameters to substitute in path
            **kwargs: Additional parameters for the request

        Returns:
            API response
        """
        return self._dynamic_api.call(endpoint_name, path_params=path_params, **kwargs)

    def register_endpoint(
        self,
        name: str,
        path: str,
        method: str = "GET",
        description: str = "",
        override: bool = False,
    ) -> "AppformClient":
        """
        Register a custom endpoint.

        Args:
            name: Unique endpoint name
            path: API path
            method: HTTP method
            description: Endpoint description
            override: Whether to override existing endpoint

        Returns:
            Self for chaining
        """
        self._registry.register(
            name=name,
            path=path,
            method=method,
            description=description,
            override=override,
        )
        return self

    def load_extension(self, extension_config: Dict[str, Any]) -> "AppformClient":
        """
        Load an extension from configuration.

        Args:
            extension_config: Extension configuration dictionary

        Returns:
            Self for chaining
        """
        self._extension_manager.load_from_dict(extension_config)
        return self

    def load_extension_file(self, file_path: str) -> "AppformClient":
        """
        Load an extension from a file.

        Args:
            file_path: Path to extension configuration file

        Returns:
            Self for chaining
        """
        self._extension_manager.load_from_file(file_path)
        return self

    def close(self):
        """Close the client session."""
        self.session.close()
        if self._sftp_api:
            self._sftp_api.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
