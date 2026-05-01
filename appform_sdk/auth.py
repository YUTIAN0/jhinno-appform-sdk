"""
Authentication API module for Appform SDK
"""

from typing import Any, Dict, Optional

from .exceptions import AuthenticationError
from .utils import AESEncryptor, check_cluster_environment


class AuthAPI:
    """
    Authentication API for Appform.

    Provides methods for login, logout, token-based authentication,
    AccessKey authentication, and permission validation.
    """

    def __init__(self, client):
        """
        Initialize the Auth API.

        Args:
            client: AppformClient instance
        """
        self._client = client
        self._encryptor = None  # Lazy init, only when AES key is available

    def _get_encryptor(self) -> AESEncryptor:
        """Get or create AESEncryptor with key from config."""
        if self._encryptor is None:
            aes_key = getattr(self._client, "_aes_key", None)
            self._encryptor = AESEncryptor(key=aes_key)
        return self._encryptor

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Login with username and password.

        Args:
            username: User account name
            password: User password

        Returns:
            Response containing token on success

        Raises:
            AuthenticationError: If login fails
        """
        result = self._client.get(
            "/appform/ws/api/auth/login",
            params={"username": username, "password": password},
        )

        if result.get("result") == "success" and result.get("data"):
            self._client.token = result["data"].get("token")

        return result

    def login_with_token(
        self, username: Optional[str] = None, timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Login using AES encrypted username token.

        This method is restricted to cluster environments only:
        - jversion command must be available (scheduler installed)
        - Current hostname must appear in jhosts -w output (node in cluster)
        - Username is auto-detected from current system user

        Args:
            username: Ignored. Always uses current system user for security.
            timeout: Login timeout in seconds (5-360)

        Returns:
            Response containing token on success

        Raises:
            AuthenticationError: If not in cluster or AES key not configured
        """
        # Cluster environment check
        cluster_info = check_cluster_environment()
        if not cluster_info["in_cluster"]:
            raise AuthenticationError(
                f"AES token login is only available in cluster environments. "
                f"Reason: {cluster_info['error']}"
            )

        # Auto-detect current user (do not allow arbitrary username)
        import getpass

        try:
            current_user = getpass.getuser()
        except Exception:
            current_user = username

        if not current_user:
            raise AuthenticationError("Cannot determine current username for AES login")

        encryptor = self._get_encryptor()
        encrypted_username = encryptor.encrypt_username(current_user)

        # encrypt() already URL-encodes the result, so build the path
        # directly to avoid double-encoding by requests' params handling.
        path = f"/appform/ws/api/auth/token?username={encrypted_username}"
        if timeout is not None:
            path += f"&timeout={timeout}"

        result = self._client.get(path)

        if result.get("result") == "success" and result.get("data"):
            self._client.token = result["data"].get("token")

        return result

    def login_with_access_key(
        self,
        access_key: str,
        access_key_secret: str,
        username: str,
    ) -> None:
        """
        Configure AccessKey authentication.

        This method sets up AccessKey authentication for subsequent requests.
        The accessKey, accessKeySecret, and username will be sent in request headers.

        Args:
            access_key: Access key for authentication
            access_key_secret: Access key secret for authentication
            username: User account name (sent in request header)

        Example:
            client.auth.login_with_access_key(
                access_key="your_access_key",
                access_key_secret="your_access_key_secret",
                username="your_username"
            )
            # Now all subsequent requests will use AccessKey authentication
            jobs = client.jobs.list_jobs()
        """
        self._client.access_key = access_key
        self._client.access_key_secret = access_key_secret
        self._client.username = username

    def set_access_key(
        self,
        access_key: str,
        access_key_secret: str,
        username: str,
    ) -> None:
        """
        Set AccessKey authentication credentials (alias for login_with_access_key).

        Args:
            access_key: Access key for authentication
            access_key_secret: Access key secret for authentication
            username: User account name
        """
        self.login_with_access_key(access_key, access_key_secret, username)

    def clear_access_key(self) -> None:
        """
        Clear AccessKey authentication credentials.
        """
        self._client.access_key = None
        self._client.access_key_secret = None
        self._client.username = None

    def is_access_key_authenticated(self) -> bool:
        """
        Check if AccessKey authentication is configured.

        Returns:
            True if AccessKey authentication is configured
        """
        return (
            self._client.access_key is not None
            and self._client.access_key_secret is not None
            and self._client.username is not None
        )

    def is_token_authenticated(self) -> bool:
        """
        Check if token authentication is configured.

        Returns:
            True if token authentication is configured
        """
        return self._client.token is not None

    def is_authenticated(self) -> bool:
        """
        Check if any authentication method is configured.

        Returns:
            True if any authentication method is configured
        """
        return self.is_token_authenticated() or self.is_access_key_authenticated()

    def logout(self) -> Dict[str, Any]:
        """
        Logout and invalidate the current session.

        Returns:
            Response confirming logout
        """
        result = self._client.delete("/appform/ws/api/auth/logout")
        self._client.token = None
        return result

    def ping(self) -> Dict[str, Any]:
        """
        Test if the service is accessible with current authentication.

        Returns:
            Response confirming service availability
        """
        return self._client.get("/appform/ws/api/ping")

    def register(
        self,
        username: str,
        chusername: str,
        password: str,
        phone: Optional[str] = None,
        mail: Optional[str] = None,
        dep: Optional[str] = None,
        card: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register a new user.

        Args:
            username: User account name (English)
            chusername: User display name (Chinese)
            password: User password
            phone: Phone number (optional)
            mail: Email address (optional)
            dep: Department name (optional)
            card: ID card number (optional)

        Returns:
            Response confirming registration
        """
        params = {
            "username": username,
            "chusername": chusername,
            "password": password,
        }

        if phone is not None:
            params["phone"] = phone
        if mail is not None:
            params["mail"] = mail
        if dep is not None:
            params["dep"] = dep
        if card is not None:
            params["card"] = card

        return self._client.post("/appform/ws/api/auth/register", params=params)

    def check_upload_permission(self) -> Dict[str, Any]:
        """
        Check if current user has upload permission.

        Returns:
            Response with upload permission status
        """
        return self._client.get("/appform/ws/api/checkUploadToken")

    def check_download_permission(self) -> Dict[str, Any]:
        """
        Check if current user has download permission.

        Returns:
            Response with download permission status
        """
        return self._client.get("/appform/ws/api/checkDownloadToken")

    def has_upload_permission(self) -> bool:
        """
        Check if current user has upload permission.

        Returns:
            True if user has upload permission
        """
        result = self.check_upload_permission()
        return result.get("message") == "upload"

    def has_download_permission(self) -> bool:
        """
        Check if current user has download permission.

        Returns:
            True if user has download permission
        """
        result = self.check_download_permission()
        return result.get("message") == "download"
