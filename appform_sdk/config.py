"""
Configuration management for Appform SDK
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse


class Config:
    """
    Configuration manager for Appform SDK.

    Supports configuration from multiple sources (in order of priority):
    1. Direct parameters
    2. Environment variables
    3. Configuration file
    """

    # Environment variable names
    ENV_BASE_URL = "APPFORM_BASE_URL"
    ENV_ACCESS_KEY = "APPFORM_ACCESS_KEY"
    ENV_ACCESS_KEY_SECRET = "APPFORM_ACCESS_KEY_SECRET"
    ENV_USERNAME = "APPFORM_USERNAME"
    ENV_PASSWORD = "APPFORM_PASSWORD"
    ENV_TOKEN = "APPFORM_TOKEN"
    ENV_TIMEOUT = "APPFORM_TIMEOUT"
    ENV_VERIFY_SSL = "APPFORM_VERIFY_SSL"
    ENV_API_VERSION = "APPFORM_API_VERSION"
    ENV_EXTENSIONS_DIR = "APPFORM_EXTENSIONS_DIR"
    ENV_JOB_PROFILE_CONFIG = "APPFORM_JOB_PROFILE_CONFIG"
    ENV_AES_KEY = "APPFORM_AES_KEY"
    ENV_OUTPUT_FORMAT = "APPFORM_OUTPUT_FORMAT"
    ENV_DEFAULT_REMOTE_PATH = "APPFORM_DEFAULT_REMOTE_PATH"
    ENV_OUTPUT_TEMPLATE = "APPFORM_OUTPUT_TEMPLATE"
    ENV_CHUNK_SIZE = "APPFORM_CHUNK_SIZE"
    ENV_DEFAULT_METHOD = "APPFORM_DEFAULT_METHOD"
    ENV_SFTP_HOST = "APPFORM_SFTP_HOST"
    ENV_SFTP_PORT = "APPFORM_SFTP_PORT"
    ENV_SFTP_KEY_FILE = "APPFORM_SFTP_KEY_FILE"
    ENV_SFTP_KEY_PASSWORD = "APPFORM_SFTP_KEY_PASSWORD"

    # Default config file paths
    DEFAULT_CONFIG_DIR = ".appform"
    DEFAULT_CONFIG_FILE = "config.json"

    def __init__(
        self,
        base_url: Optional[str] = None,
        access_key: Optional[str] = None,
        access_key_secret: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        aes_key: Optional[str] = None,
        timeout: Optional[int] = None,
        verify_ssl: Optional[bool] = None,
        api_version: Optional[str] = None,
        extensions_dir: Optional[str] = None,
        job_profile_config: Optional[str] = None,
        output_format: Optional[str] = None,
        output_template: Optional[str] = None,
        chunk_size: Optional[int] = None,
        config_file: Optional[str] = None,
        sftp_host: Optional[str] = None,
        sftp_port: Optional[int] = None,
        sftp_username: Optional[str] = None,
        sftp_password: Optional[str] = None,
        sftp_key_file: Optional[str] = None,
        sftp_key_password: Optional[str] = None,
    ):
        """
        Initialize configuration.

        Args:
            base_url: API base URL
            access_key: Access key
            access_key_secret: Access key secret
            username: Username
            password: Password
            token: Authentication token
            aes_key: AES encryption key for cluster token auth
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
            api_version: API version to use (e.g., "6.5", "7.0")
            extensions_dir: Directory containing extension configurations
            job_profile_config: Path to job profile configuration file (job_submit.yaml)
            output_format: Output format (json/table/text)
            output_template: Path to output template file (.yaml/.yml/.json)
            config_file: Path to configuration file (defaults to ~/.appform/config.json)
            sftp_host: SFTP server hostname (defaults to host from base_url)
            sftp_port: SFTP server port (default: 22)
            sftp_username: SFTP username (defaults to username)
            sftp_password: SFTP password (defaults to password)
            sftp_key_file: SSH private key file path
            sftp_key_password: SSH key passphrase
        """
        # Determine config file path - use default if not specified
        if config_file:
            self._config_file = os.path.expanduser(config_file)
        else:
            default_path = self.get_default_config_path()
            self._config_file = str(default_path) if default_path.exists() else None

        self._file_config = self._load_config_file() if self._config_file else {}

        # Set values with priority: direct params > env vars > config file
        self.base_url = self._get_value(base_url, self.ENV_BASE_URL, "base_url")
        self.access_key = self._get_value(access_key, self.ENV_ACCESS_KEY, "access_key")
        self.access_key_secret = self._get_value(
            access_key_secret, self.ENV_ACCESS_KEY_SECRET, "access_key_secret"
        )
        self.username = self._get_value(username, self.ENV_USERNAME, "username")
        self.password = self._get_value(password, self.ENV_PASSWORD, "password")
        self.token = self._get_value(token, self.ENV_TOKEN, "token")
        self.aes_key = self._get_value(aes_key, self.ENV_AES_KEY, "aes_key")
        self.timeout = self._get_int_value(
            timeout, self.ENV_TIMEOUT, "timeout", default=30
        )
        self.verify_ssl = self._get_bool_value(
            verify_ssl, self.ENV_VERIFY_SSL, "verify_ssl", default=True
        )
        self.api_version = self._get_value(
            api_version, self.ENV_API_VERSION, "api_version", default="6.5"
        )
        self.extensions_dir = self._get_value(
            extensions_dir, self.ENV_EXTENSIONS_DIR, "extensions_dir"
        )
        self.job_profile_config = self._get_value(
            job_profile_config, self.ENV_JOB_PROFILE_CONFIG, "job_profile_config"
        )
        self.output_format = self._get_value(
            output_format, self.ENV_OUTPUT_FORMAT, "output_format", default="table"
        )
        self.output_template = self._get_value(
            output_template, self.ENV_OUTPUT_TEMPLATE, "output_template"
        )
        self.default_remote_path = self._get_value(
            None, self.ENV_DEFAULT_REMOTE_PATH, "default_remote_path", default="/"
        )
        self.chunk_size = self._get_int_value(
            chunk_size, self.ENV_CHUNK_SIZE, "chunk_size", default=104857600
        )
        self.default_method = self._get_value(
            None, self.ENV_DEFAULT_METHOD, "default_method", default="http"
        )

        # SFTP configuration
        self.sftp_host = self._get_value(sftp_host, self.ENV_SFTP_HOST, "sftp_host")
        self.sftp_port = self._get_int_value(
            sftp_port, self.ENV_SFTP_PORT, "sftp_port", default=22
        )
        self.sftp_username = self._get_value(
            sftp_username, self.ENV_USERNAME, "sftp_username"
        ) or self.username
        self.sftp_password = self._get_value(
            sftp_password, self.ENV_PASSWORD, "sftp_password"
        ) or self.password
        self.sftp_key_file = self._get_value(
            sftp_key_file, self.ENV_SFTP_KEY_FILE, "sftp_key_file"
        )
        self.sftp_key_password = self._get_value(
            sftp_key_password, self.ENV_SFTP_KEY_PASSWORD, "sftp_key_password"
        )

    def _get_value(
        self,
        direct_value: Optional[str],
        env_var: str,
        config_key: str,
        default: Optional[str] = None,
    ) -> Optional[str]:
        """Get value with priority: direct > env > config file > default."""
        if direct_value is not None:
            return direct_value
        env_value = os.environ.get(env_var)
        if env_value is not None:
            return env_value
        file_value = self._file_config.get(config_key)
        if file_value is not None:
            return file_value
        return default

    def _get_int_value(
        self,
        direct_value: Optional[int],
        env_var: str,
        config_key: str,
        default: int,
    ) -> int:
        """Get integer value with priority: direct > env > config file > default.

        Supports human-readable size strings like '100M', '1G' from env/config.
        """
        if direct_value is not None:
            if isinstance(direct_value, str):
                from .files import parse_size

                return parse_size(direct_value)
            return direct_value
        env_value = os.environ.get(env_var)
        if env_value is not None:
            try:
                return int(env_value)
            except ValueError:
                from .files import parse_size

                try:
                    return parse_size(env_value)
                except ValueError:
                    pass
        file_value = self._file_config.get(config_key)
        if file_value is not None:
            if isinstance(file_value, int):
                return file_value
            try:
                return int(file_value)
            except (ValueError, TypeError):
                from .files import parse_size

                try:
                    return parse_size(file_value)
                except ValueError:
                    pass
        return default

    def _get_bool_value(
        self,
        direct_value: Optional[bool],
        env_var: str,
        config_key: str,
        default: bool,
    ) -> bool:
        """Get boolean value with priority: direct > env > config file > default."""
        if direct_value is not None:
            return direct_value
        env_value = os.environ.get(env_var)
        if env_value is not None:
            return env_value.lower() in ("true", "1", "yes", "on")
        file_value = self._file_config.get(config_key)
        if file_value is not None:
            if isinstance(file_value, bool):
                return file_value
            if isinstance(file_value, str):
                return file_value.lower() in ("true", "1", "yes", "on")
            if isinstance(file_value, int):
                return file_value == 1
        return default

    def _load_config_file(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self._config_file:
            return {}

        config_path = Path(self._config_file)
        if not config_path.is_absolute():
            config_path = Path.home() / self._config_file

        if not config_path.exists():
            return {}

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables only."""
        return cls()

    @classmethod
    def from_file(cls, config_file: str) -> "Config":
        """Create configuration from file."""
        return cls(config_file=config_file)

    @classmethod
    def get_default_config_path(cls) -> Path:
        """Get the default configuration file path."""
        return Path.home() / cls.DEFAULT_CONFIG_DIR / cls.DEFAULT_CONFIG_FILE

    @classmethod
    def get_default_extensions_dir(cls) -> Path:
        """Get the default extensions directory path."""
        return Path.home() / cls.DEFAULT_CONFIG_DIR / "extensions"

    @classmethod
    def save_config_file(
        cls,
        base_url: Optional[str] = None,
        access_key: Optional[str] = None,
        access_key_secret: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        aes_key: Optional[str] = None,
        timeout: Optional[int] = None,
        verify_ssl: Optional[bool] = None,
        api_version: Optional[str] = None,
        extensions_dir: Optional[str] = None,
        job_profile_config: Optional[str] = None,
        output_format: Optional[str] = None,
        output_template: Optional[str] = None,
        default_remote_path: Optional[str] = None,
        chunk_size: Optional[int] = None,
        default_method: Optional[str] = None,
        config_file: Optional[str] = None,
        sftp_host: Optional[str] = None,
        sftp_port: Optional[int] = None,
        sftp_username: Optional[str] = None,
        sftp_password: Optional[str] = None,
        sftp_key_file: Optional[str] = None,
        sftp_key_password: Optional[str] = None,
    ) -> None:
        """
        Save configuration to file.

        Args:
            base_url: API base URL
            access_key: Access key
            access_key_secret: Access key secret
            username: Username
            password: Password
            token: Authentication token
            aes_key: AES encryption key for cluster token auth
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
            api_version: API version
            extensions_dir: Extensions directory
            job_profile_config: Job profile config file path
            output_format: Output format (json/table/text)
            output_template: Output template file path
            default_remote_path: Default remote path for file operations
            config_file: Path to configuration file (defaults to ~/.appform/config.json)
        """
        if config_file:
            config_path = Path(config_file)
            if not config_path.is_absolute():
                config_path = Path.home() / config_file
        else:
            config_path = cls.get_default_config_path()

        # Create directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing config to preserve unset fields
        existing = {}
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        if base_url:
            existing["base_url"] = base_url
        if access_key:
            existing["access_key"] = access_key
        if access_key_secret:
            existing["access_key_secret"] = access_key_secret
        if username:
            existing["username"] = username
        if password:
            existing["password"] = password
        if token:
            existing["token"] = token
        if aes_key:
            existing["aes_key"] = aes_key
        if timeout is not None:
            existing["timeout"] = timeout
        if verify_ssl is not None:
            existing["verify_ssl"] = verify_ssl
        if api_version:
            existing["api_version"] = api_version
        if extensions_dir:
            existing["extensions_dir"] = extensions_dir
        if job_profile_config:
            existing["job_profile_config"] = job_profile_config
        if output_format:
            existing["output_format"] = output_format
        if output_template:
            existing["output_template"] = output_template
        if default_remote_path:
            existing["default_remote_path"] = default_remote_path
        if chunk_size is not None:
            existing["chunk_size"] = chunk_size
        if default_method:
            existing["default_method"] = default_method
        if sftp_host:
            existing["sftp_host"] = sftp_host
        if sftp_port is not None:
            existing["sftp_port"] = sftp_port
        if sftp_username:
            existing["sftp_username"] = sftp_username
        if sftp_password:
            existing["sftp_password"] = sftp_password
        if sftp_key_file:
            existing["sftp_key_file"] = sftp_key_file
        if sftp_key_password:
            existing["sftp_key_password"] = sftp_key_password

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "base_url": self.base_url,
            "access_key": self.access_key,
            "access_key_secret": self.access_key_secret,
            "username": self.username,
            "password": "***" if self.password else None,
            "token": "***" if self.token else None,
            "aes_key": "***" if self.aes_key else None,
            "timeout": self.timeout,
            "verify_ssl": self.verify_ssl,
            "api_version": self.api_version,
            "extensions_dir": self.extensions_dir,
            "job_profile_config": self.job_profile_config,
            "output_format": self.output_format,
            "output_template": self.output_template,
            "default_remote_path": self.default_remote_path,
            "chunk_size": self.chunk_size,
            "default_method": self.default_method,
            "sftp_host": self.sftp_host,
            "sftp_port": self.sftp_port,
            "sftp_username": self.sftp_username,
            "sftp_password": "***" if self.sftp_password else None,
            "sftp_key_file": self.sftp_key_file,
            "sftp_key_password": "***" if self.sftp_key_password else None,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Config(base_url={self.base_url!r}, "
            f"access_key={self.access_key!r}, "
            f"access_key_secret={'***' if self.access_key_secret else None}, "
            f"username={self.username!r}, "
            f"password={'***' if self.password else None}, "
            f"token={'***' if self.token else None}, "
            f"timeout={self.timeout}, "
            f"verify_ssl={self.verify_ssl}, "
            f"api_version={self.api_version!r}, "
            f"extensions_dir={self.extensions_dir!r})"
        )
