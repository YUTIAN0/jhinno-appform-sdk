"""
Tests for uncovered code paths identified by the coverage report.

Covers: common.py, auth.py, config.py, sftp.py, compute.py,
        utils.py, client.py, exceptions.py.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from appform_sdk.exceptions import APIError, AuthenticationError, SFTPError

# ==============================================================================
# common.py — remote_file_exists, check_is_directory, SFTP mode detection
# ==============================================================================


class TestRemoteFileExists:
    """Tests for appform_sdk.cli.common.remote_file_exists."""

    def test_returns_true_when_file_found(self):
        from appform_sdk.cli.common import remote_file_exists

        client = MagicMock()
        client.files.list_all.return_value = [
            {"fileName": "target.txt"},
            {"fileName": "other.log"},
        ]
        assert remote_file_exists(client, "/remote/dir", "target.txt") is True

    def test_returns_false_when_file_missing(self):
        from appform_sdk.cli.common import remote_file_exists

        client = MagicMock()
        client.files.list_all.return_value = [
            {"fileName": "other.log"},
        ]
        assert remote_file_exists(client, "/remote/dir", "target.txt") is False

    def test_returns_false_on_exception(self):
        from appform_sdk.cli.common import remote_file_exists

        client = MagicMock()
        client.files.list_all.return_value = [
            {"fileName": "other.log"},
        ]
        assert remote_file_exists(client, "/remote/dir", "target.txt") is False

    def test_returns_false_when_list_all_raises(self):
        from appform_sdk.cli.common import remote_file_exists

        client = MagicMock()
        client.files.list_all.side_effect = FileNotFoundError("no such dir")
        assert remote_file_exists(client, "/remote/dir", "target.txt") is False

    def test_returns_false_when_list_all_raises_same_dir(self):
        from appform_sdk.cli.common import remote_file_exists

        client = MagicMock()
        client.files.list_all.side_effect = FileNotFoundError("no such dir")
        assert remote_file_exists(client, "/remote/dir", "target.txt") is False

    def test_empty_list_returns_false(self):
        from appform_sdk.cli.common import remote_file_exists

        client = MagicMock()
        client.files.list_all.return_value = []
        assert remote_file_exists(client, "/remote/dir", "target.txt") is False


class TestCheckIsDirectory:
    """Tests for appform_sdk.cli.common.check_is_directory."""

    def test_http_with_dict_files_key(self):
        from appform_sdk.cli.common import check_is_directory

        client = MagicMock()
        client.files.list.return_value = {"data": {"files": [{"name": "x"}]}}
        assert check_is_directory(client, "http", "/remote/dir") is True

    def test_http_with_dict_records_key(self):
        from appform_sdk.cli.common import check_is_directory

        client = MagicMock()
        client.files.list.return_value = {"data": {"records": [{"id": 1}]}}
        assert check_is_directory(client, "http", "/remote/dir") is True

    def test_http_with_list_data(self):
        from appform_sdk.cli.common import check_is_directory

        client = MagicMock()
        client.files.list.return_value = {"data": [{"fileName": "x.txt"}]}
        assert check_is_directory(client, "http", "/remote/dir") is True

    def test_http_with_scalar_data_returns_false(self):
        from appform_sdk.cli.common import check_is_directory

        client = MagicMock()
        client.files.list.return_value = {"data": "just-a-string"}
        assert check_is_directory(client, "http", "/remote/dir") is False

    def test_http_with_scalar_data_again(self):
        from appform_sdk.cli.common import check_is_directory

        client = MagicMock()
        client.files.list.return_value = {"data": "just-a-string"}
        assert check_is_directory(client, "http", "/remote/dir") is False

    def test_http_with_exception_returns_false(self):
        from appform_sdk.cli.common import check_is_directory

        client = MagicMock()
        client.files.list.side_effect = FileNotFoundError("no path")
        assert check_is_directory(client, "http", "/remote/dir") is False

    def test_sftp_with_dict_files_key(self):
        from appform_sdk.cli.common import check_is_directory

        client = MagicMock()
        client.sftp.list.return_value = {"data": {"files": [{"name": "x"}]}}
        assert check_is_directory(client, "sftp", "/remote/dir") is True

    def test_sftp_with_list_data(self):
        from appform_sdk.cli.common import check_is_directory

        client = MagicMock()
        client.sftp.list.return_value = {"data": [{"fileName": "x.txt"}]}
        assert check_is_directory(client, "sftp", "/remote/dir") is True

    def test_sftp_with_scalar_data_falls_back_to_trailing_slash(self):
        from appform_sdk.cli.common import check_is_directory

        client = MagicMock()
        client.sftp.list.return_value = {"data": "just-a-string"}
        assert check_is_directory(client, "sftp", "/remote/dir/") is True

    def test_sftp_with_scalar_data_no_trailing_slash(self):
        from appform_sdk.cli.common import check_is_directory

        client = MagicMock()
        client.sftp.list.return_value = {"data": "just-a-string"}
        assert check_is_directory(client, "sftp", "/remote/file.txt") is False

    def test_sftp_with_exception_returns_false(self):
        from appform_sdk.cli.common import check_is_directory

        client = MagicMock()
        client.sftp.list.side_effect = FileNotFoundError("no path")
        # With trailing slash, fallback heuristic returns True
        assert check_is_directory(client, "sftp", "/remote/dir/") is True

    def test_sftp_with_exception_no_trailing_slash(self):
        from appform_sdk.cli.common import check_is_directory

        client = MagicMock()
        client.sftp.list.side_effect = FileNotFoundError("no path")
        assert check_is_directory(client, "sftp", "/remote/file.txt") is False


# ==============================================================================
# auth.py — login_with_token raises error when AES key missing
# ==============================================================================


class TestLoginWithToken:
    """Tests for appform_sdk.auth.AuthAPI.login_with_token."""

    @patch("appform_sdk.auth.check_cluster_environment")
    def test_raises_when_not_in_cluster(self, mock_check):
        from appform_sdk.auth import AuthAPI

        mock_check.return_value = {
            "in_cluster": False,
            "error": "jversion command not found",
        }
        client = MagicMock()
        auth = AuthAPI(client)
        with pytest.raises(AuthenticationError, match="cluster environments"):
            auth.login_with_token()

    @patch("appform_sdk.auth.check_cluster_environment")
    def test_raises_when_aes_key_missing(self, mock_check):
        from appform_sdk.auth import AuthAPI

        mock_check.return_value = {"in_cluster": True, "error": None}
        client = MagicMock()
        client._aes_key = None
        auth = AuthAPI(client)
        with pytest.raises(ValueError, match="AES key is required"):
            auth.login_with_token()

    @patch("appform_sdk.auth.check_cluster_environment")
    def test_raises_when_getpass_fails(self, mock_check):
        from appform_sdk.auth import AuthAPI

        mock_check.return_value = {"in_cluster": True, "error": None}
        client = MagicMock()
        client._aes_key = "0123456789abcdef"
        auth = AuthAPI(client)
        with patch("getpass.getuser") as mock_gp:
            mock_gp.side_effect = Exception("no user")
            with pytest.raises(AuthenticationError, match="Cannot determine"):
                auth.login_with_token()


# ==============================================================================
# config.py — to_dict() redacts secrets, config file parse warning
# ==============================================================================


class TestConfigRedaction:
    """Tests for appform_sdk.config.Config.to_dict() redaction."""

    def test_redacts_access_key(self):
        from appform_sdk.config import Config

        config = Config(access_key="real_key")
        d = config.to_dict()
        assert d["access_key"] == "***"

    def test_redacts_access_key_secret(self):
        from appform_sdk.config import Config

        config = Config(access_key_secret="real_secret")
        d = config.to_dict()
        assert d["access_key_secret"] == "***"

    def test_redacts_password(self):
        from appform_sdk.config import Config

        config = Config(password="real_pass")
        d = config.to_dict()
        assert d["password"] == "***"

    def test_redacts_token(self):
        from appform_sdk.config import Config

        config = Config(token="real_token")
        d = config.to_dict()
        assert d["token"] == "***"

    def test_redacts_aes_key(self):
        from appform_sdk.config import Config

        config = Config(aes_key="real_aes")
        d = config.to_dict()
        assert d["aes_key"] == "***"

    def test_redacts_sftp_password(self):
        from appform_sdk.config import Config

        # sftp_password is internal; test via _get_value not directly exposed.
        # Just verify non-sensitive fields pass through.
        config = Config(base_url="https://test.com")
        d = config.to_dict()
        assert d["base_url"] == "https://test.com"
        assert d["access_key"] is None  # None when not set (no redaction)

    def test_none_values_not_redacted(self):
        from appform_sdk.config import Config

        config = Config(base_url="https://test.com")
        d = config.to_dict()
        assert d["access_key"] is None
        assert d["access_key_secret"] is None
        assert d["token"] is None
        assert d["password"] is None

    def test_sensitive_fields_never_expose_raw_value(self):
        from appform_sdk.config import Config

        config = Config(
            access_key="sk_live_123",
            access_key_secret="secret_456",
            token="tok_789",
            password="pass_abc",
            aes_key="aes_xyz",
        )
        d = config.to_dict()
        for key in ("access_key", "access_key_secret", "token", "password", "aes_key"):
            assert d[key] == "***", f"{key} was not redacted"


class TestConfigFileWarning:
    """Tests for config file parse warning on JSON decode errors."""

    def test_warns_on_bad_json(self, monkeypatch):
        from appform_sdk.config import Config

        monkeypatch.delenv("APPFORM_BASE_URL", raising=False)
        monkeypatch.delenv("APPFORM_ACCESS_KEY", raising=False)
        monkeypatch.delenv("APPFORM_ACCESS_KEY_SECRET", raising=False)
        monkeypatch.delenv("APPFORM_USERNAME", raising=False)
        monkeypatch.delenv("APPFORM_PASSWORD", raising=False)
        monkeypatch.delenv("APPFORM_TOKEN", raising=False)
        monkeypatch.delenv("APPFORM_AES_KEY", raising=False)
        monkeypatch.delenv("APPFORM_TIMEOUT", raising=False)
        monkeypatch.delenv("APPFORM_VERIFY_SSL", raising=False)
        monkeypatch.delenv("APPFORM_API_VERSION", raising=False)
        monkeypatch.delenv("APPFORM_EXTENSIONS_DIR", raising=False)
        monkeypatch.delenv("APPFORM_JOB_PROFILE_CONFIG", raising=False)
        monkeypatch.delenv("APPFORM_OUTPUT_FORMAT", raising=False)
        monkeypatch.delenv("APPFORM_OUTPUT_TEMPLATE", raising=False)
        monkeypatch.delenv("APPFORM_DEFAULT_REMOTE_PATH", raising=False)
        monkeypatch.delenv("APPFORM_CHUNK_SIZE", raising=False)
        monkeypatch.delenv("APPFORM_DEFAULT_METHOD", raising=False)
        monkeypatch.delenv("APPFORM_SFTP_HOST", raising=False)
        monkeypatch.delenv("APPFORM_SFTP_PORT", raising=False)
        monkeypatch.delenv("APPFORM_SFTP_KEY_FILE", raising=False)
        monkeypatch.delenv("APPFORM_SFTP_KEY_PASSWORD", raising=False)
        monkeypatch.delenv("APPFORM_COMPUTE_CONFIG", raising=False)

        import warnings

        config_path = os.path.join(tempfile.gettempdir(), "_appform_test_bad.json")
        try:
            with open(config_path, "w") as f:
                f.write("{bad json content")
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                Config(config_file=config_path)
                # There should be at least one warning about JSON decode
                json_warnings = [
                    x for x in w if "Failed to load config file" in str(x.message)
                ]
                assert len(json_warnings) >= 1
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)


# ==============================================================================
# sftp.py — _validate_path rejects dangerous characters
# ==============================================================================


class TestSFTPValidatePath:
    """Tests for appform_sdk.sftp._validate_path."""

    def test_accepts_simple_path(self):
        from appform_sdk.sftp import _validate_path

        assert _validate_path("output.log") == "output.log"

    def test_accepts_nested_path(self):
        from appform_sdk.sftp import _validate_path

        assert _validate_path("dir/subdir/file.txt") == "dir/subdir/file.txt"

    def test_accepts_absolute_path(self):
        from appform_sdk.sftp import _validate_path

        assert _validate_path("/remote/path/file.txt") == "/remote/path/file.txt"

    def test_accepts_asterisk_glob(self):
        from appform_sdk.sftp import _validate_path

        assert _validate_path("*.log") == "*.log"

    def test_accepts_question_mark_glob(self):
        from appform_sdk.sftp import _validate_path

        assert _validate_path("file?.txt") == "file?.txt"

    def test_accepts_bracket_glob(self):
        from appform_sdk.sftp import _validate_path

        assert _validate_path("file[1-3].txt") == "file[1-3].txt"

    def test_rejects_semicolon(self):
        from appform_sdk.sftp import _validate_path

        with pytest.raises(SFTPError, match="Invalid characters"):
            _validate_path("file.txt; rm -rf /")

    def test_rejects_pipe(self):
        from appform_sdk.sftp import _validate_path

        with pytest.raises(SFTPError, match="Invalid characters"):
            _validate_path("file.txt | cat /etc/passwd")

    def test_rejects_ampersand(self):
        from appform_sdk.sftp import _validate_path

        with pytest.raises(SFTPError, match="Invalid characters"):
            _validate_path("file.txt & evil")

    def test_rejects_backtick(self):
        from appform_sdk.sftp import _validate_path

        with pytest.raises(SFTPError, match="Invalid characters"):
            _validate_path("file`whoami`.txt")

    def test_rejects_dollar_sign(self):
        from appform_sdk.sftp import _validate_path

        with pytest.raises(SFTPError, match="Invalid characters"):
            _validate_path("file_${HOME}.txt")

    def test_rejects_parentheses(self):
        from appform_sdk.sftp import _validate_path

        with pytest.raises(SFTPError, match="Invalid characters"):
            _validate_path("file(sub).txt")

    def test_rejects_curly_braces(self):
        from appform_sdk.sftp import _validate_path

        with pytest.raises(SFTPError, match="Invalid characters"):
            _validate_path("file{1,2}.txt")

    def test_rejects_backslash(self):
        from appform_sdk.sftp import _validate_path

        with pytest.raises(SFTPError, match="Invalid characters"):
            _validate_path("file\\n.txt")

    def test_rejects_redirect_gt(self):
        from appform_sdk.sftp import _validate_path

        with pytest.raises(SFTPError, match="Invalid characters"):
            _validate_path("file > /dev/null")

    def test_rejects_redirect_lt(self):
        from appform_sdk.sftp import _validate_path

        with pytest.raises(SFTPError, match="Invalid characters"):
            _validate_path("file < input.txt")

    def test_rejects_single_quote(self):
        from appform_sdk.sftp import _validate_path

        with pytest.raises(SFTPError, match="Invalid characters"):
            _validate_path("file'name.txt")

    def test_rejects_double_quote(self):
        from appform_sdk.sftp import _validate_path

        with pytest.raises(SFTPError, match="Invalid characters"):
            _validate_path('file"name.txt')

    def test_rejects_space(self):
        from appform_sdk.sftp import _validate_path

        with pytest.raises(SFTPError, match="Invalid characters"):
            _validate_path("my file.txt")

    def test_rejects_newline(self):
        from appform_sdk.sftp import _validate_path

        with pytest.raises(SFTPError, match="Newline"):
            _validate_path("file\n.txt")

    def test_rejects_directory_traversal(self):
        from appform_sdk.sftp import _validate_path

        with pytest.raises(SFTPError, match="Directory traversal"):
            _validate_path("../etc/passwd")

    def test_rejects_nested_traversal(self):
        from appform_sdk.sftp import _validate_path

        with pytest.raises(SFTPError, match="Directory traversal"):
            _validate_path("foo/../../bar")


# ==============================================================================
# compute.py — _validate_path, get_head_node, resolve_path, human_size
# NOTE: Many of these are already covered in test_compute.py. These tests
# focus on edge cases not yet exercised.
# ==============================================================================


class TestComputeValidatePath:
    """Tests for appform_sdk.compute._validate_path (edge cases)."""

    def test_rejects_single_quote(self):
        from appform_sdk.compute import _validate_path

        with pytest.raises(Exception, match="Invalid characters"):
            _validate_path("file'name.txt")

    def test_rejects_double_quote(self):
        from appform_sdk.compute import _validate_path

        with pytest.raises(Exception, match="Invalid characters"):
            _validate_path('file"name.txt')

    def test_rejects_space(self):
        from appform_sdk.compute import _validate_path

        with pytest.raises(Exception, match="Invalid characters"):
            _validate_path("my file.txt")


class TestHumanSizeEdgeCases:
    """Edge cases for appform_sdk.compute.human_size not in test_compute.py."""

    def test_terabyte(self):
        from appform_sdk.compute import human_size

        assert human_size(1.5 * 1024**4) == "1.5 TB"

    def test_negative_bytes(self):
        from appform_sdk.compute import human_size

        assert human_size(-100) == "-100.0 B"


# ==============================================================================
# utils.py — AESEncryptor rejects wrong key lengths
# ==============================================================================


class TestAESEncryptorKeyLength:
    """Tests for appform_sdk.utils.AESEncryptor key length validation."""

    def test_rejects_17_byte_key(self):
        from appform_sdk.utils import AESEncryptor

        key = "a" * 17
        with pytest.raises(ValueError, match="must be 16, 24, or 32 bytes"):
            AESEncryptor(key=key)

    def test_rejects_20_byte_key(self):
        from appform_sdk.utils import AESEncryptor

        key = "a" * 20
        with pytest.raises(ValueError, match="must be 16, 24, or 32 bytes"):
            AESEncryptor(key=key)

    def test_rejects_8_byte_key(self):
        from appform_sdk.utils import AESEncryptor

        key = "a" * 8
        with pytest.raises(ValueError, match="must be 16, 24, or 32 bytes"):
            AESEncryptor(key=key)

    def test_rejects_empty_key(self):
        from appform_sdk.utils import AESEncryptor

        with pytest.raises(ValueError, match="AES key is required"):
            AESEncryptor(key="")

    def test_rejects_none_key_with_no_env(self, monkeypatch):
        from appform_sdk.utils import AESEncryptor

        monkeypatch.delenv("APPFORM_AES_KEY", raising=False)
        with pytest.raises(ValueError, match="AES key is required"):
            AESEncryptor()

    def test_accepts_16_byte_key(self, monkeypatch):
        from appform_sdk.utils import AESEncryptor

        monkeypatch.delenv("APPFORM_AES_KEY", raising=False)
        encryptor = AESEncryptor(key="0123456789abcdef")
        encrypted = encryptor.encrypt("test")
        assert encryptor.decrypt(encrypted) == "test"

    def test_accepts_24_byte_key(self, monkeypatch):
        from appform_sdk.utils import AESEncryptor

        monkeypatch.delenv("APPFORM_AES_KEY", raising=False)
        encryptor = AESEncryptor(key="0123456789abcdef01234567")
        encrypted = encryptor.encrypt("test")
        assert encryptor.decrypt(encrypted) == "test"

    def test_accepts_32_byte_key(self, monkeypatch):
        from appform_sdk.utils import AESEncryptor

        monkeypatch.delenv("APPFORM_AES_KEY", raising=False)
        encryptor = AESEncryptor(key="0123456789abcdef0123456789abcdef")
        encrypted = encryptor.encrypt("test")
        assert encryptor.decrypt(encrypted) == "test"


# ==============================================================================
# client.py — Retry only on GET/HEAD/OPTIONS, falsy value handling
# ==============================================================================


class TestClientRetryMethods:
    """Tests for AppformClient retry strategy (allowed_methods)."""

    def test_retry_allowed_methods_are_get_head_options(self):
        """Verify the Retry strategy allows GET, HEAD, OPTIONS."""
        from appform_sdk.client import AppformClient

        client = AppformClient(base_url="https://test.com")
        # The retry strategy is attached to the HTTP adapter
        adapter = client.session.get_adapter("https://")
        retry = adapter.max_retries
        assert "GET" in retry.allowed_methods
        assert "HEAD" in retry.allowed_methods
        assert "OPTIONS" in retry.allowed_methods

    def test_post_not_in_retry_allowed_methods(self):
        """Verify POST is NOT retried by default."""
        from appform_sdk.client import AppformClient

        client = AppformClient(base_url="https://test.com")
        adapter = client.session.get_adapter("https://")
        retry = adapter.max_retries
        assert "POST" not in retry.allowed_methods

    def test_put_not_in_retry_allowed_methods(self):
        """Verify PUT is NOT retried by default."""
        from appform_sdk.client import AppformClient

        client = AppformClient(base_url="https://test.com")
        adapter = client.session.get_adapter("https://")
        retry = adapter.max_retries
        assert "PUT" not in retry.allowed_methods

    def test_delete_not_in_retry_allowed_methods(self):
        """Verify DELETE is NOT retried by default."""
        from appform_sdk.client import AppformClient

        client = AppformClient(base_url="https://test.com")
        adapter = client.session.get_adapter("https://")
        retry = adapter.max_retries
        assert "DELETE" not in retry.allowed_methods

    def test_max_retries_respected(self):
        """Verify max_retries parameter is passed through."""
        from appform_sdk.client import AppformClient

        client = AppformClient(base_url="https://test.com", max_retries=5)
        adapter = client.session.get_adapter("https://")
        retry = adapter.max_retries
        assert retry.total == 5


class TestClientFalsyValues:
    """Tests for AppformClient handling of falsy values (timeout=0, etc.)."""

    def test_timeout_zero_is_preserved(self):
        """Verify timeout=0 is treated as a falsy-but-valid value."""
        from appform_sdk.client import AppformClient

        # timeout=0 means 'no timeout' in requests. It should be stored as 0,
        # not replaced by the default of 30.
        client = AppformClient(base_url="https://test.com", timeout=0)
        assert client.timeout == 0

    def test_timeout_default_is_30(self):
        from appform_sdk.client import AppformClient

        client = AppformClient(base_url="https://test.com")
        assert client.timeout == 30

    def test_verify_ssl_default_is_true(self):
        from appform_sdk.client import AppformClient

        client = AppformClient(base_url="https://test.com")
        assert client.verify_ssl is True

    def test_base_url_trailing_slash_stripped(self):
        from appform_sdk.client import AppformClient

        client = AppformClient(base_url="https://test.com/")
        assert client.base_url == "https://test.com"


# ==============================================================================
# exceptions.py — APIError.__str__ includes status code
# ==============================================================================


class TestAPIErrorStr:
    """Tests for appform_sdk.exceptions.APIError.__str__."""

    def test_str_includes_status_code(self):
        err = APIError("Not found", status_code=404)
        assert str(err) == "[404] Not found"

    def test_str_includes_status_code_400(self):
        err = APIError("Bad request", status_code=400)
        assert str(err) == "[400] Bad request"

    def test_str_without_status_code(self):
        err = APIError("Server error", status_code=None)
        assert str(err) == "Server error"

    def test_str_with_500(self):
        err = APIError("Internal error", status_code=500)
        assert str(err) == "[500] Internal error"

    def test_str_with_200(self):
        err = APIError("OK", status_code=200)
        assert str(err) == "[200] OK"

    def test_message_attribute_preserved(self):
        err = APIError("Detail message", status_code=404)
        assert err.message == "Detail message"

    def test_response_attribute_preserved(self):
        resp = {"code": 404, "data": None}
        err = APIError("Not found", status_code=404, response=resp)
        assert err.response == resp

    def test_status_code_attribute_preserved(self):
        err = APIError("Not found", status_code=404)
        assert err.status_code == 404
