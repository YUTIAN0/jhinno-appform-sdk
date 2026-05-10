"""
Tests for Appform SDK
"""

import json
import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from appform_sdk import AESEncryptor, AppformClient, Config, SignatureGenerator
from appform_sdk.exceptions import APIError, AuthenticationError


class TestConfig:
    """Tests for configuration management."""

    def test_config_from_env(self, monkeypatch):
        """Test loading configuration from environment variables."""
        monkeypatch.setenv("APPFORM_BASE_URL", "https://env-server.com")
        monkeypatch.setenv("APPFORM_ACCESS_KEY", "env_key")
        monkeypatch.setenv("APPFORM_ACCESS_KEY_SECRET", "env_secret")
        monkeypatch.setenv("APPFORM_USERNAME", "env_user")

        config = Config()
        assert config.base_url == "https://env-server.com"
        assert config.access_key == "env_key"
        assert config.access_key_secret == "env_secret"
        assert config.username == "env_user"

    def test_config_from_file(self):
        """Test loading configuration from file."""
        config_data = {
            "base_url": "https://file-server.com",
            "access_key": "file_key",
            "access_key_secret": "file_secret",
            "username": "file_user",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = Config(config_file=config_path)
            assert config.base_url == "https://file-server.com"
            assert config.access_key == "file_key"
            assert config.access_key_secret == "file_secret"
            assert config.username == "file_user"
        finally:
            os.unlink(config_path)

    def test_config_priority(self, monkeypatch):
        """Test configuration priority: direct > env > file."""
        # Set env vars
        monkeypatch.setenv("APPFORM_BASE_URL", "https://env-server.com")
        monkeypatch.setenv("APPFORM_ACCESS_KEY", "env_key")

        # Create config file
        config_data = {
            "base_url": "https://file-server.com",
            "access_key": "file_key",
            "username": "file_user",
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Direct params should override env and file
            config = Config(
                base_url="https://direct-server.com",
                config_file=config_path,
            )
            assert config.base_url == "https://direct-server.com"
            # access_key from env (overrides file)
            assert config.access_key == "env_key"
            # username from file
            assert config.username == "file_user"
        finally:
            os.unlink(config_path)

    def test_config_save(self):
        """Test saving configuration to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")

            Config.save_config_file(
                base_url="https://saved-server.com",
                access_key="saved_key",
                access_key_secret="saved_secret",
                username="saved_user",
                config_file=config_path,
            )

            # Verify file was created
            assert os.path.exists(config_path)

            # Verify content
            with open(config_path, "r") as f:
                data = json.load(f)

            assert data["base_url"] == "https://saved-server.com"
            assert data["access_key"] == "saved_key"
            assert data["access_key_secret"] == "saved_secret"
            assert data["username"] == "saved_user"

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = Config(
            base_url="https://test.com",
            access_key="key",
            username="user",
        )
        d = config.to_dict()
        assert d["base_url"] == "https://test.com"
        assert d["access_key"] == "***"
        assert d["username"] == "user"

    def test_config_proxy_from_env(self, monkeypatch):
        """Test loading proxy configuration from environment variables."""
        monkeypatch.setenv("APPFORM_HTTP_PROXY", "http://proxy:8080")
        monkeypatch.setenv("APPFORM_SFTP_PROXY", "socks5://proxy:1080")

        config = Config()
        assert config.http_proxy == "http://proxy:8080"
        assert config.sftp_proxy == "socks5://proxy:1080"

    def test_config_proxy_from_file(self):
        """Test loading proxy configuration from file."""
        config_data = {
            "base_url": "https://file-server.com",
            "http_proxy": "http://proxy.local:8080",
            "sftp_proxy": "http://proxy.local:8080",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = Config(config_file=config_path)
            assert config.http_proxy == "http://proxy.local:8080"
            assert config.sftp_proxy == "http://proxy.local:8080"
        finally:
            os.unlink(config_path)

    def test_config_proxy_priority(self, monkeypatch):
        """Test proxy configuration priority: direct > env > file."""
        monkeypatch.setenv("APPFORM_HTTP_PROXY", "http://env-proxy:8080")
        config_data = {"base_url": "https://file-server.com", "http_proxy": "http://file-proxy:8080"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = Config(
                http_proxy="http://direct-proxy:8080", config_file=config_path
            )
            assert config.http_proxy == "http://direct-proxy:8080"

            config2 = Config(config_file=config_path)
            assert config2.http_proxy == "http://env-proxy:8080"

            monkeypatch.delenv("APPFORM_HTTP_PROXY")
            config3 = Config(config_file=config_path)
            assert config3.http_proxy == "http://file-proxy:8080"
        finally:
            os.unlink(config_path)

    def test_config_save_proxy(self):
        """Test saving proxy configuration to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")

            Config.save_config_file(
                base_url="https://saved-server.com",
                http_proxy="http://proxy:8080",
                sftp_proxy="socks5://proxy:1080",
                config_file=config_path,
            )

            assert os.path.exists(config_path)

            with open(config_path, "r") as f:
                data = json.load(f)

            assert data["http_proxy"] == "http://proxy:8080"
            assert data["sftp_proxy"] == "socks5://proxy:1080"

    def test_config_save_proxy_to_environment(self):
        """Test saving proxy configuration to a named environment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")

            Config.save_config_file(
                base_url="https://prod-server.com",
                http_proxy="http://prod-proxy:8080",
                config_file=config_path,
                environment="prod",
            )

            with open(config_path, "r") as f:
                data = json.load(f)

            assert data["environments"]["prod"]["http_proxy"] == "http://prod-proxy:8080"

    def test_config_to_dict_includes_proxy(self):
        """Test that to_dict includes proxy fields."""
        config = Config(
            base_url="https://test.com",
            http_proxy="http://proxy:8080",
        )
        d = config.to_dict()
        assert d["http_proxy"] == "http://proxy:8080"

    def test_config_env_from_param(self):
        """Test loading from environment via constructor parameter."""
        config_data = {
            "default_environment": "dev",
            "environments": {
                "prod": {
                    "base_url": "https://prod-server.com",
                    "username": "prod_user",
                },
                "dev": {
                    "base_url": "https://dev-server.com",
                    "username": "dev_user",
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = Config(config_file=config_path, env="prod")
            assert config.base_url == "https://prod-server.com"
            assert config.username == "prod_user"
            assert config._current_environment == "prod"
        finally:
            os.unlink(config_path)

    def test_config_env_from_env_var(self, monkeypatch):
        """Test loading from environment via APPFORM_ENV."""
        monkeypatch.setenv("APPFORM_ENV", "dev")
        config_data = {
            "environments": {
                "dev": {
                    "base_url": "https://dev-server.com",
                    "username": "dev_user",
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = Config(config_file=config_path)
            assert config.base_url == "https://dev-server.com"
            assert config.username == "dev_user"
            assert config._current_environment == "dev"
        finally:
            os.unlink(config_path)

    def test_config_env_root_fallback(self):
        """Test fallback to root config when env not found."""
        config_data = {
            "base_url": "https://root-server.com",
            "username": "root_user",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = Config(config_file=config_path, env="nonexistent")
            assert config.base_url == "https://root-server.com"
            assert config.username == "root_user"
            assert config._current_environment == "nonexistent"
        finally:
            os.unlink(config_path)

    def test_config_priority_with_env(self, monkeypatch):
        """Test priority with environment: direct > env var > merged file."""
        monkeypatch.setenv("APPFORM_BASE_URL", "https://env-server.com")
        config_data = {
            "base_url": "https://root-server.com",
            "default_environment": "prod",
            "environments": {
                "prod": {
                    "base_url": "https://prod-server.com",
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            # direct param > env var > merged file
            config = Config(
                base_url="https://direct-server.com", config_file=config_path
            )
            assert config.base_url == "https://direct-server.com"

            # env var > merged file
            config2 = Config(config_file=config_path)
            assert config2.base_url == "https://env-server.com"

            # merged file (env config) when no env var and no direct param
            monkeypatch.delenv("APPFORM_BASE_URL")
            config3 = Config(config_file=config_path)
            assert config3.base_url == "https://prod-server.com"
        finally:
            os.unlink(config_path)

    def test_config_save_to_environment(self):
        """Test saving configuration to a named environment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")

            Config.save_config_file(
                base_url="https://prod-server.com",
                username="prod_user",
                config_file=config_path,
                environment="prod",
            )

            assert os.path.exists(config_path)

            with open(config_path, "r") as f:
                data = json.load(f)

            assert "environments" in data
            assert "prod" in data["environments"]
            assert data["environments"]["prod"]["base_url"] == "https://prod-server.com"
            assert data["environments"]["prod"]["username"] == "prod_user"

        # now save another env
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            # first save root + prod env
            Config.save_config_file(
                base_url="https://root.com",
                config_file=config_path,
                environment="prod",
                api_version="6.5",
            )
            # now add dev env only with base_url
            Config.save_config_file(
                base_url="https://dev-server.com",
                config_file=config_path,
                environment="dev",
            )

            with open(config_path, "r") as f:
                data = json.load(f)

            assert data["environments"]["prod"]["base_url"] == "https://root.com"
            assert data["environments"]["dev"]["base_url"] == "https://dev-server.com"
            assert data["environments"]["prod"]["api_version"] == "6.5"


class TestAESEncryptor:
    """Tests for AES encryption utility."""

    def test_encrypt_decrypt(self, monkeypatch):
        """Test encryption and decryption roundtrip."""
        monkeypatch.setenv("APPFORM_AES_KEY", "0123456789abcdef")
        encryptor = AESEncryptor()
        plaintext = "testuser,1234567890"
        encrypted = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_username(self, monkeypatch):
        """Test username encryption."""
        monkeypatch.setenv("APPFORM_AES_KEY", "0123456789abcdef")
        encryptor = AESEncryptor()
        encrypted = encryptor.encrypt_username("testuser", timestamp=1234567890)
        decrypted = encryptor.decrypt_username(encrypted)
        assert decrypted == "testuser"


class TestSignatureGenerator:
    """Tests for signature generation."""

    def test_generate_signature(self):
        """Test signature generation matches expected format."""
        access_key = "test_access_key"
        access_key_secret = "test_secret"
        username = "testuser"
        current_time = 1234567890000

        signature, timestamp = SignatureGenerator.generate_signature(
            access_key=access_key,
            access_key_secret=access_key_secret,
            username=username,
            current_time=current_time,
        )

        # Verify signature format
        # beforeSignature = `#${accessKey}#${username}#${currentTime}#`
        # signature = HmacSHA256(beforeSignature, accessKeySecret)
        assert timestamp == current_time
        assert signature is not None
        assert len(signature) == 64  # SHA256 hex digest length

    def test_generate_auth_headers(self):
        """Test auth headers generation."""
        headers = SignatureGenerator.generate_auth_headers(
            access_key="test_key",
            access_key_secret="test_secret",
            username="testuser",
        )

        assert "accessKey" in headers
        assert "signature" in headers
        assert "currentTimeMillis" in headers
        assert "username" in headers
        assert headers["accessKey"] == "test_key"
        assert headers["username"] == "testuser"

    def test_signature_consistency(self):
        """Test that same inputs produce same signature."""
        access_key = "test_key"
        access_key_secret = "test_secret"
        username = "testuser"
        current_time = 1234567890000

        sig1, _ = SignatureGenerator.generate_signature(
            access_key, access_key_secret, username, current_time
        )
        sig2, _ = SignatureGenerator.generate_signature(
            access_key, access_key_secret, username, current_time
        )

        assert sig1 == sig2


class TestAppformClient:
    """Tests for AppformClient."""

    def test_init(self):
        """Test client initialization."""
        client = AppformClient(base_url="https://test.com")
        assert client.base_url == "https://test.com"
        assert client.token is None
        assert client.access_key is None
        assert client.access_key_secret is None
        # username may be auto-detected from environment, so don't assert None
        assert isinstance(client.username, str) or client.username is None

    def test_init_with_token(self):
        """Test client initialization with token."""
        client = AppformClient(base_url="https://test.com", token="test_token")
        assert client.token == "test_token"

    def test_init_with_access_key(self):
        """Test client initialization with AccessKey."""
        client = AppformClient(
            base_url="https://test.com",
            access_key="test_key",
            access_key_secret="test_secret",
            username="test_user",
        )
        assert client.access_key == "test_key"
        assert client.access_key_secret == "test_secret"
        assert client.username == "test_user"

    def test_context_manager(self):
        """Test context manager usage."""
        with AppformClient(base_url="https://test.com") as client:
            assert client is not None

    def test_headers_with_token(self):
        """Test headers include token."""
        client = AppformClient(base_url="https://test.com", token="test_token")
        headers = client._get_headers()
        assert headers["token"] == "test_token"

    def test_headers_with_access_key(self):
        """Test headers include AccessKey credentials with signature."""
        client = AppformClient(
            base_url="https://test.com",
            access_key="test_key",
            access_key_secret="test_secret",
            username="test_user",
        )
        headers = client._get_headers()
        # Should include accessKey, signature, currentTimeMillis, username
        assert headers["accessKey"] == "test_key"
        assert headers["username"] == "test_user"
        assert "signature" in headers
        assert "currentTimeMillis" in headers
        # accessKeySecret should NOT be in headers (used for signature only)
        assert "accessKeySecret" not in headers

    def test_headers_with_both_auth(self):
        """Test headers include both token and AccessKey."""
        client = AppformClient(
            base_url="https://test.com",
            token="test_token",
            access_key="test_key",
            access_key_secret="test_secret",
            username="test_user",
        )
        headers = client._get_headers()
        assert headers["token"] == "test_token"
        assert headers["accessKey"] == "test_key"
        assert headers["username"] == "test_user"
        assert "signature" in headers
        assert "currentTimeMillis" in headers
        # accessKeySecret should NOT be in headers
        assert "accessKeySecret" not in headers


class TestAuthAPI:
    """Tests for Auth API."""

    @patch("appform_sdk.client.requests.Session")
    def test_login_success(self, mock_session):
        """Test successful login."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 200,
            "result": "success",
            "message": "请求成功",
            "data": {"token": "test_token_123"},
        }
        mock_session.return_value.request.return_value = mock_response

        client = AppformClient(base_url="https://test.com")
        result = client.auth.login(username="user", password="pass")

        assert result["result"] == "success"
        assert client.token == "test_token_123"

    @patch("appform_sdk.client.requests.Session")
    def test_login_failure(self, mock_session):
        """Test failed login."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 500,
            "result": "failed",
            "message": "密码错误",
            "data": None,
        }
        mock_session.return_value.request.return_value = mock_response

        client = AppformClient(base_url="https://test.com")
        result = client.auth.login(username="user", password="wrong")

        assert result["result"] == "failed"
        assert client.token is None

    def test_login_with_access_key(self):
        """Test AccessKey authentication setup."""
        client = AppformClient(base_url="https://test.com")

        client.auth.login_with_access_key(
            access_key="test_key", access_key_secret="test_secret", username="test_user"
        )

        assert client.access_key == "test_key"
        assert client.access_key_secret == "test_secret"
        assert client.username == "test_user"
        assert client.auth.is_access_key_authenticated() is True
        assert client.auth.is_authenticated() is True

    def test_set_access_key(self):
        """Test set_access_key method."""
        client = AppformClient(base_url="https://test.com")

        client.auth.set_access_key(
            access_key="test_key", access_key_secret="test_secret", username="test_user"
        )

        assert client.auth.is_access_key_authenticated() is True

    def test_clear_access_key(self):
        """Test clearing AccessKey credentials."""
        client = AppformClient(
            base_url="https://test.com",
            access_key="test_key",
            access_key_secret="test_secret",
            username="test_user",
        )

        assert client.auth.is_access_key_authenticated() is True

        client.auth.clear_access_key()

        assert client.access_key is None
        assert client.access_key_secret is None
        assert client.username is None
        assert client.auth.is_access_key_authenticated() is False

    def test_is_authenticated(self):
        """Test is_authenticated method."""
        client = AppformClient(base_url="https://test.com")

        assert client.auth.is_authenticated() is False

        client.token = "test_token"
        assert client.auth.is_authenticated() is True
        assert client.auth.is_token_authenticated() is True

        client.token = None
        client.access_key = "test_key"
        client.access_key_secret = "test_secret"
        client.username = "test_user"
        assert client.auth.is_authenticated() is True
        assert client.auth.is_access_key_authenticated() is True


class TestJobsAPI:
    """Tests for Jobs API."""

    @patch("appform_sdk.client.requests.Session")
    def test_get_job(self, mock_session):
        """Test getting job details."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 200,
            "result": "success",
            "data": {"jobId": "12345", "name": "test_job", "status": "RUN"},
        }
        mock_session.return_value.request.return_value = mock_response

        client = AppformClient(base_url="https://test.com", token="test_token")
        result = client.jobs.get_job("12345")

        assert result["data"]["jobId"] == "12345"

    @patch("appform_sdk.client.requests.Session")
    def test_list_jobs(self, mock_session):
        """Test listing jobs."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 200,
            "result": "success",
            "data": {
                "content": [
                    {"jobId": "1", "name": "job1", "status": "RUN"},
                    {"jobId": "2", "name": "job2", "status": "PEND"},
                ],
                "totalElements": 2,
            },
        }
        mock_session.return_value.request.return_value = mock_response

        client = AppformClient(base_url="https://test.com", token="test_token")
        result = client.jobs.list_jobs(page=1, page_size=20)

        assert len(result["data"]["content"]) == 2

    @patch("appform_sdk.client.requests.Session")
    def test_list_jobs_with_access_key(self, mock_session):
        """Test listing jobs with AccessKey authentication."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 200,
            "result": "success",
            "data": {
                "content": [
                    {"jobId": "1", "name": "job1", "status": "RUN"},
                ],
                "totalElements": 1,
            },
        }
        mock_session.return_value.request.return_value = mock_response

        client = AppformClient(
            base_url="https://test.com",
            access_key="test_key",
            access_key_secret="test_secret",
            username="test_user",
        )
        client.jobs.list_jobs(page=1, page_size=20)

        # Verify AccessKey headers were sent
        call_args = mock_session.return_value.request.call_args
        headers = call_args.kwargs["headers"]
        assert headers["accessKey"] == "test_key"
        assert headers["username"] == "test_user"
        assert "signature" in headers
        assert "currentTimeMillis" in headers
        # accessKeySecret should NOT be in headers
        assert "accessKeySecret" not in headers


class TestExceptions:
    """Tests for exception handling."""

    @patch("appform_sdk.client.requests.Session")
    def test_authentication_error(self, mock_session):
        """Test authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "code": 500,
            "result": "failed",
            "message": "无效的安全令牌",
            "data": None,
        }
        mock_session.return_value.request.return_value = mock_response

        client = AppformClient(base_url="https://test.com", token="invalid_token")

        with pytest.raises(AuthenticationError):
            client.auth.ping()

    @patch("appform_sdk.client.requests.Session")
    def test_api_error(self, mock_session):
        """Test API error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            "code": 500,
            "result": "failed",
            "message": "Internal server error",
            "data": None,
        }
        mock_session.return_value.request.return_value = mock_response

        client = AppformClient(base_url="https://test.com", token="test_token")

        with pytest.raises(APIError) as exc_info:
            client.jobs.get_job("invalid_id")

        assert exc_info.value.status_code == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
