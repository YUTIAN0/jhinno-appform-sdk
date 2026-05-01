"""
Tests for Appform SDK
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from appform_sdk import AESEncryptor, AppformClient, Config, SignatureGenerator
from appform_sdk.exceptions import APIError, AppformError, AuthenticationError


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
        assert d["access_key"] == "key"
        assert d["username"] == "user"


class TestAESEncryptor:
    """Tests for AES encryption utility."""

    def test_encrypt_decrypt(self):
        """Test encryption and decryption roundtrip."""
        encryptor = AESEncryptor()
        plaintext = "testuser,1234567890"
        encrypted = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_username(self):
        """Test username encryption."""
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
        assert client.username is None

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
        result = client.jobs.list_jobs(page=1, page_size=20)

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
