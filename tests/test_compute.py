"""Tests for compute node SSH operations."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from appform_sdk.exceptions import ComputeError


class TestLoadComputeConfig:
    """Tests for load_compute_config."""

    def test_load_from_explicit_path(self):
        """Test loading config from explicit file path."""
        from appform_sdk.compute import load_compute_config

        config_content = """
compute_config:
  default:
    mode: direct
    source_script: "/opt/profile"
    env_cmd: jjobs
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            path = f.name

        try:
            result = load_compute_config(config_file=path)
            assert result["compute_config"]["default"]["mode"] == "direct"
            assert (
                result["compute_config"]["default"]["source_script"] == "/opt/profile"
            )
        finally:
            os.unlink(path)

    def test_load_from_env_var(self, monkeypatch):
        """Test loading config from APPFORM_COMPUTE_CONFIG env var."""
        from appform_sdk.compute import load_compute_config

        config_content = "compute_config:\n  default:\n    mode: via_gateway\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            path = f.name

        try:
            monkeypatch.setenv("APPFORM_COMPUTE_CONFIG", path)
            monkeypatch.delenv("APPFORM_DEFAULT_COMPUTE", raising=False)
            result = load_compute_config()
            assert result["compute_config"]["default"]["mode"] == "via_gateway"
        finally:
            os.unlink(path)

    def test_load_missing_file(self):
        """Test loading non-existent config raises FileNotFoundError."""
        from appform_sdk.compute import load_compute_config

        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "nonexistent.yaml")
            with pytest.raises(FileNotFoundError):
                load_compute_config(config_file=path)


class TestResolveAppConfig:
    """Tests for resolve_app_config."""

    def _base_config(self, overrides=None, app_overrides=None):
        """Build a base compute config with optional overrides."""
        cfg = {
            "compute_config": {
                "default": {
                    "mode": "direct",
                    "source_script": "/opt/profile",
                    "env_cmd": "jjobs",
                    "work_path_var": "work_path",
                },
                "applications": {},
            }
        }
        if overrides:
            cfg["compute_config"]["default"].update(overrides)
        if app_overrides:
            for k, v in app_overrides.items():
                cfg["compute_config"]["applications"].setdefault(k, {})
                cfg["compute_config"]["applications"][k].update(v)
        return cfg

    def test_defaults_only(self):
        """Test resolving config with only defaults."""
        from appform_sdk.compute import resolve_app_config

        cfg = {"compute_config": {"default": {}}}
        result = resolve_app_config(cfg, "starccm")
        assert result["mode"] == "direct"
        assert result["source_script"] == ""
        assert result["env_cmd"] == "jjobs"
        assert result["work_path_var"] == "work_path"

    def test_app_override_work_path_var(self):
        """Test app-specific work_path_var overrides default."""
        from appform_sdk.compute import resolve_app_config

        cfg = self._base_config(
            app_overrides={"fluent": {"work_path_var": "fluent_work_dir"}}
        )
        result = resolve_app_config(cfg, "fluent")
        assert result["work_path_var"] == "fluent_work_dir"
        assert result["mode"] == "direct"

    def test_unknown_app_uses_defaults(self):
        """Test unknown app falls back to all defaults."""
        from appform_sdk.compute import resolve_app_config

        cfg = self._base_config()
        result = resolve_app_config(cfg, "unknown_app")
        assert result["mode"] == "direct"
        assert result["work_path_var"] == "work_path"

    def test_app_partial_override(self):
        """Test app only overrides some fields, rest from default."""
        from appform_sdk.compute import resolve_app_config

        cfg = self._base_config(
            overrides={"mode": "via_gateway"},
            app_overrides={"starccm": {"work_path_var": "casework"}},
        )
        result = resolve_app_config(cfg, "starccm")
        assert result["mode"] == "via_gateway"  # from default
        assert result["work_path_var"] == "casework"  # from app override
        assert result["env_cmd"] == "jjobs"


class TestGetHeadNode:
    """Tests for get_head_node with various executionHost formats."""

    def test_list_single_node(self):
        """Test list with single node."""
        from appform_sdk.compute import get_head_node

        result = get_head_node(["compute01"])
        assert result == "compute01"

    def test_list_multiple_same_node(self):
        """Test list with same node repeated (multiple slots)."""
        from appform_sdk.compute import get_head_node

        result = get_head_node(["ev-hpc-compute226", "ev-hpc-compute226"])
        assert result == "ev-hpc-compute226"

    def test_list_different_nodes(self):
        """Test list with different nodes, first is head."""
        from appform_sdk.compute import get_head_node

        result = get_head_node(["node-a", "node-b", "node-c"])
        assert result == "node-a"

    def test_string_single_node(self):
        """Test legacy string format without multiplier."""
        from appform_sdk.compute import get_head_node

        result = get_head_node("ev-hpc-compute033")
        assert result == "ev-hpc-compute033"

    def test_string_with_multiplier(self):
        """Test legacy string format '64*nodeName'."""
        from appform_sdk.compute import get_head_node

        result = get_head_node("64*ev-hpc-compute033")
        assert result == "ev-hpc-compute033"

    def test_string_multi_node_colon_sep(self):
        """Test legacy string format with colon-separated nodes."""
        from appform_sdk.compute import get_head_node

        result = get_head_node("64*ev-hpc-compute033:64*ev-hpc-compute026")
        assert result == "ev-hpc-compute033"

    def test_empty_list_raises(self):
        """Test empty list raises ComputeError."""
        from appform_sdk.compute import get_head_node

        with pytest.raises(ComputeError):
            get_head_node([])

    def test_empty_string(self):
        """Test empty string returns empty."""
        from appform_sdk.compute import get_head_node

        result = get_head_node("")
        assert result == ""


class TestResolvePath:
    """Tests for resolve_path."""

    def test_absolute_path(self):
        """Test absolute path is returned as-is."""
        from appform_sdk.compute import resolve_path

        result = resolve_path("/share/work/123", "/absolute/path")
        assert result == "/absolute/path"

    def test_relative_path(self):
        """Test relative path is prepended with work_path."""
        from appform_sdk.compute import resolve_path

        result = resolve_path("/share/work/123", "output/log.txt")
        assert result == "/share/work/123/output/log.txt"

    def test_dot_path(self):
        """Test '.' path resolves to work_path."""
        from appform_sdk.compute import resolve_path

        result = resolve_path("/share/work/123", ".")
        assert result == "/share/work/123/."

    def test_trailing_slash_work_path(self):
        """Test work_path with trailing slash doesn't double-slash."""
        from appform_sdk.compute import resolve_path

        result = resolve_path("/share/work/123/", "subdir/file.txt")
        assert result == "/share/work/123/subdir/file.txt"


class TestComputeLs:
    """Tests for compute_ls."""

    def test_list_directory(self):
        """Test listing directory via SFTP."""
        from appform_sdk.compute import compute_ls

        sftp = MagicMock()
        attrs = [
            MagicMock(
                filename="subdir",
                st_mode=0o40755,
                st_size=4096,
                st_mtime=1700000000,
            ),
            MagicMock(
                filename="file.txt",
                st_mode=0o100644,
                st_size=1024,
                st_mtime=1700001000,
            ),
        ]
        sftp.listdir_attr.return_value = attrs

        result = compute_ls(sftp, "/remote/")
        assert len(result) == 2
        assert result[0]["fileType"] == "directory"
        assert result[1]["fileType"] == "file"
        assert result[1]["size"] == 1024

    def test_list_missing_directory(self):
        """Test ls raises on missing directory."""
        from appform_sdk.compute import compute_ls

        sftp = MagicMock()
        sftp.listdir_attr.side_effect = FileNotFoundError("no such dir")

        with pytest.raises(FileNotFoundError):
            compute_ls(sftp, "/missing/")


class TestComputeCat:
    """Tests for compute_cat."""

    def test_cat_full(self):
        """Test cat returns full file content."""
        from appform_sdk.compute import compute_cat

        client = MagicMock()
        stdout = MagicMock()
        stdout.read.return_value = b"line1\nline2\nline3\n"
        stdout.channel.recv_exit_status.return_value = 0
        stderr = MagicMock()
        stderr.read.return_value = b""
        client.exec_command.return_value = (MagicMock(), stdout, stderr)

        result = compute_cat(client, "/remote/file.txt")
        assert result == "line1\nline2\nline3"
        cmd = client.exec_command.call_args[0][0]
        assert cmd == "cat /remote/file.txt"

    def test_cat_head(self):
        """Test cat with head parameter."""
        from appform_sdk.compute import compute_cat

        client = MagicMock()
        stdout = MagicMock()
        stdout.read.return_value = b"line1\nline2\n"
        stdout.channel.recv_exit_status.return_value = 0
        stderr = MagicMock()
        stderr.read.return_value = b""
        client.exec_command.return_value = (MagicMock(), stdout, stderr)

        compute_cat(client, "/f.txt", head=2)
        cmd = client.exec_command.call_args[0][0]
        assert cmd == "head -n 2 /f.txt"

    def test_cat_tail(self):
        """Test cat with tail parameter."""
        from appform_sdk.compute import compute_cat

        client = MagicMock()
        stdout = MagicMock()
        stdout.read.return_value = b"line9\nline10\n"
        stdout.channel.recv_exit_status.return_value = 0
        stderr = MagicMock()
        stderr.read.return_value = b""
        client.exec_command.return_value = (MagicMock(), stdout, stderr)

        compute_cat(client, "/f.txt", tail=2)
        cmd = client.exec_command.call_args[0][0]
        assert cmd == "tail -n 2 /f.txt"

    def test_cat_stderr_on_failure(self, capfd):
        """Test cat prints stderr on non-zero exit."""
        from appform_sdk.compute import compute_cat

        client = MagicMock()
        stdout = MagicMock()
        stdout.read.return_value = b""
        stdout.channel.recv_exit_status.return_value = 1
        stderr = MagicMock()
        stderr.read.return_value = b"Permission denied\n"
        client.exec_command.return_value = (MagicMock(), stdout, stderr)

        result = compute_cat(client, "/f.txt")
        assert result == ""


class TestValidatePath:
    """Tests for _validate_path security checks."""

    def test_safe_paths(self):
        """Test safe paths pass validation."""
        from appform_sdk.compute import _validate_path

        assert _validate_path("output.log") == "output.log"
        assert _validate_path("dir/file.txt") == "dir/file.txt"
        assert _validate_path("/absolute/path") == "/absolute/path"
        assert _validate_path("*.log") == "*.log"  # glob allowed
        assert _validate_path("file[1].txt") == "file[1].txt"  # bracket glob

    def test_reject_semicolon(self):
        """Test semicolon in path is rejected."""
        from appform_sdk.compute import _validate_path

        with pytest.raises(ComputeError, match="Invalid characters"):
            _validate_path("file.txt; rm -rf /")

    def test_reject_pipe(self):
        """Test pipe in path is rejected."""
        from appform_sdk.compute import _validate_path

        with pytest.raises(ComputeError):
            _validate_path("file.txt | cat /etc/passwd")

    def test_reject_ampersand(self):
        """Test ampersand in path is rejected."""
        from appform_sdk.compute import _validate_path

        with pytest.raises(ComputeError):
            _validate_path("file.txt & evil")

    def test_reject_backticks(self):
        """Test backticks in path are rejected."""
        from appform_sdk.compute import _validate_path

        with pytest.raises(ComputeError):
            _validate_path("file`whoami`.txt")

    def test_reject_dollar(self):
        """Test dollar sign in path is rejected."""
        from appform_sdk.compute import _validate_path

        with pytest.raises(ComputeError):
            _validate_path("file_${HOME}.txt")

    def test_reject_parens(self):
        """Test parentheses in path are rejected."""
        from appform_sdk.compute import _validate_path

        with pytest.raises(ComputeError):
            _validate_path("file(sub).txt")

    def test_reject_braces(self):
        """Test braces in path are rejected."""
        from appform_sdk.compute import _validate_path

        with pytest.raises(ComputeError):
            _validate_path("file{1,2}.txt")

    def test_reject_backslash(self):
        """Test backslash in path is rejected."""
        from appform_sdk.compute import _validate_path

        with pytest.raises(ComputeError):
            _validate_path("file\\n.txt")

    def test_reject_redirect(self):
        """Test redirect characters in path are rejected."""
        from appform_sdk.compute import _validate_path

        with pytest.raises(ComputeError):
            _validate_path("file > /dev/null")

    def test_reject_newline(self):
        """Test newline in path is rejected."""
        from appform_sdk.compute import _validate_path

        with pytest.raises(ComputeError, match="Newline"):
            _validate_path("file\n.txt")

    def test_reject_dotdot_traversal(self):
        """Test '..' directory traversal is rejected."""
        from appform_sdk.compute import _validate_path

        with pytest.raises(ComputeError, match="Directory traversal"):
            _validate_path("../etc/passwd")

    def test_reject_nested_dotdot(self):
        """Test nested '..' in path is rejected."""
        from appform_sdk.compute import _validate_path

        with pytest.raises(ComputeError, match="Directory traversal"):
            _validate_path("foo/../../bar")


class TestHumanSize:
    """Tests for human_size helper."""

    def test_bytes(self):
        from appform_sdk.compute import human_size

        assert human_size(0) == "0.0 B"
        assert human_size(500) == "500.0 B"

    def test_kb(self):
        from appform_sdk.compute import human_size

        assert human_size(1536) == "1.5 KB"

    def test_mb(self):
        from appform_sdk.compute import human_size

        assert human_size(1572864) == "1.5 MB"

    def test_gb(self):
        from appform_sdk.compute import human_size

        assert human_size(1610612736) == "1.5 GB"


class TestExecuteOnComputeNode:
    """Tests for execute_on_compute_node dispatcher."""

    @patch("appform_sdk.compute.connect_direct")
    @patch("appform_sdk.compute.close_ssh_client")
    def test_ls_dispatch(self, mock_close, mock_connect):
        """Test ls subcommand dispatch."""
        from appform_sdk.compute import execute_on_compute_node

        mock_client = MagicMock()
        mock_connect.return_value = mock_client
        mock_sftp = MagicMock()
        mock_client.open_sftp.return_value = mock_sftp
        mock_sftp.listdir_attr.return_value = []

        # Mock query_work_path by patching exec_command
        stdout = MagicMock()
        stdout.read.return_value = b"work_path=/share/work/123\n"
        stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (
            MagicMock(),
            stdout,
            MagicMock(),
        )

        result = execute_on_compute_node(
            app_cfg={
                "mode": "direct",
                "source_script": "/opt/profile",
                "env_cmd": "jjobs",
                "work_path_var": "work_path",
            },
            head_node="compute01",
            job_id="12345",
            subcommand="ls",
            subcommand_args=[],
            ssh_kwargs={"connect_kwargs": {"username": "u", "password": "p"}},
        )
        assert result == 0
        mock_connect.assert_called_once()
        mock_close.assert_called_once_with(mock_client)

    @patch("appform_sdk.compute.connect_direct")
    @patch("appform_sdk.compute.close_ssh_client")
    def test_unknown_subcommand(self, mock_close, mock_connect):
        """Test unknown subcommand returns error code 1."""
        from appform_sdk.compute import execute_on_compute_node

        mock_client = MagicMock()
        mock_connect.return_value = mock_client

        stdout = MagicMock()
        stdout.read.return_value = b"work_path=/share/work/123\n"
        stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (
            MagicMock(),
            stdout,
            MagicMock(),
        )

        result = execute_on_compute_node(
            app_cfg={
                "mode": "direct",
                "source_script": "/opt/profile",
                "env_cmd": "jjobs",
                "work_path_var": "work_path",
            },
            head_node="compute01",
            job_id="12345",
            subcommand="unknown_cmd",
            subcommand_args=[],
            ssh_kwargs={"connect_kwargs": {"username": "u", "password": "p"}},
        )
        assert result == 1

    @patch("appform_sdk.compute.connect_direct")
    @patch("appform_sdk.compute.close_ssh_client")
    def test_cat_dispatch(self, mock_close, mock_connect):
        """Test cat subcommand dispatch."""
        from appform_sdk.compute import execute_on_compute_node

        mock_client = MagicMock()
        mock_connect.return_value = mock_client

        stdout = MagicMock()
        stdout.read.return_value = b"work_path=/share/work/123\n"
        stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (
            MagicMock(),
            stdout,
            MagicMock(),
        )

        result = execute_on_compute_node(
            app_cfg={
                "mode": "direct",
                "source_script": "/opt/profile",
                "env_cmd": "jjobs",
                "work_path_var": "work_path",
            },
            head_node="compute01",
            job_id="12345",
            subcommand="cat",
            subcommand_args=["output.log"],
            ssh_kwargs={"connect_kwargs": {"username": "u", "password": "p"}},
        )
        assert result == 0

    @patch("appform_sdk.compute.connect_direct")
    def test_connect_raises_no_paramiko(self, mock_connect):
        """Test ComputeError when paramiko is unavailable."""
        from appform_sdk.compute import execute_on_compute_node

        mock_connect.side_effect = ComputeError("paramiko is required")

        result = execute_on_compute_node(
            app_cfg={
                "mode": "direct",
                "source_script": "",
                "env_cmd": "jjobs",
                "work_path_var": "work_path",
            },
            head_node="compute01",
            job_id="12345",
            subcommand="ls",
            subcommand_args=[],
            ssh_kwargs={"connect_kwargs": {"username": "u"}},
        )
        assert result == 1

    @patch("appform_sdk.compute.connect_direct")
    @patch("appform_sdk.compute.close_ssh_client")
    def test_close_always_called(self, mock_close, mock_connect):
        """Test SSH client is always closed even on errors."""
        from appform_sdk.compute import execute_on_compute_node

        mock_client = MagicMock()
        mock_connect.return_value = mock_client

        stdout = MagicMock()
        stdout.read.return_value = b"work_path=/share/work/123\n"
        stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (
            MagicMock(),
            stdout,
            MagicMock(),
        )
        mock_sftp = MagicMock()
        mock_sftp.listdir_attr.side_effect = FileNotFoundError("no")
        mock_client.open_sftp.return_value = mock_sftp

        result = execute_on_compute_node(
            app_cfg={
                "mode": "direct",
                "source_script": "/opt/profile",
                "env_cmd": "jjobs",
                "work_path_var": "work_path",
            },
            head_node="compute01",
            job_id="12345",
            subcommand="ls",
            subcommand_args=["/missing/"],
            ssh_kwargs={"connect_kwargs": {"username": "u", "password": "p"}},
        )
        assert result == 1
        mock_close.assert_called_once()


class TestQueryWorkPath:
    """Tests for query_work_path."""

    def test_extract_work_path(self):
        """Test extracting work_path from jjobs output."""
        from appform_sdk.compute import query_work_path

        client = MagicMock()
        stdout = MagicMock()
        stdout.read.return_value = (
            b"old_work_path=/apps/backup/old\n"
            b"work_path=/share/work/123\n"
            b"slots=8\n"
        )
        stdout.channel.recv_exit_status.return_value = 0
        stderr = MagicMock()
        stderr.read.return_value = b""
        client.exec_command.return_value = (MagicMock(), stdout, stderr)

        result = query_work_path(
            client, "node1", "12345", "/opt/profile", "jjobs", "work_path"
        )
        assert result == "/share/work/123"

    def test_custom_work_path_var(self):
        """Test extracting custom work_path_var."""
        from appform_sdk.compute import query_work_path

        client = MagicMock()
        stdout = MagicMock()
        stdout.read.return_value = (
            b"work_path=/share/old\n" b"fluent_work_dir=/share/fluent/456\n"
        )
        stdout.channel.recv_exit_status.return_value = 0
        stderr = MagicMock()
        stderr.read.return_value = b""
        client.exec_command.return_value = (MagicMock(), stdout, stderr)

        result = query_work_path(
            client, "node1", "12345", "/opt/profile", "jjobs", "fluent_work_dir"
        )
        assert result == "/share/fluent/456"

    def test_command_failure(self):
        """Test query_work_path raises on command failure."""
        from appform_sdk.compute import query_work_path

        client = MagicMock()
        stdout = MagicMock()
        stdout.read.return_value = b""
        stdout.channel.recv_exit_status.return_value = 1
        stderr = MagicMock()
        stderr.read.return_value = b"job not found\n"
        client.exec_command.return_value = (MagicMock(), stdout, stderr)

        with pytest.raises(ComputeError, match="failed"):
            query_work_path(
                client, "node1", "99999", "/opt/profile", "jjobs", "work_path"
            )

    def test_var_not_found(self):
        """Test query_work_path raises when variable is missing."""
        from appform_sdk.compute import query_work_path

        client = MagicMock()
        stdout = MagicMock()
        stdout.read.return_value = b"slots=8\nstatus=RUN\n"
        stdout.channel.recv_exit_status.return_value = 0
        stderr = MagicMock()
        stderr.read.return_value = b""
        client.exec_command.return_value = (MagicMock(), stdout, stderr)

        with pytest.raises(ComputeError, match="Could not find"):
            query_work_path(
                client, "node1", "12345", "/opt/profile", "jjobs", "work_path"
            )
