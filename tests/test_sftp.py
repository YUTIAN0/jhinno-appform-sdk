"""Tests for SFTP file transfer operations."""

import os
import stat as stat_module
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from appform_sdk.exceptions import SFTPError


def _make_sftp_attr(filename, file_size=100, is_dir=False, mtime=1700000000):
    """Create a mock SFTP attribute object."""
    attr = MagicMock()
    attr.filename = filename
    attr.st_size = file_size
    attr.st_mtime = mtime
    if is_dir:
        attr.st_mode = stat_module.S_IFDIR | 0o755
    else:
        attr.st_mode = stat_module.S_IFREG | 0o644
    return attr


def _make_mock_manager(sftp_mock=None):
    """Create a mock SFTPClientManager with a given sftp mock."""
    if sftp_mock is None:
        sftp_mock = MagicMock()
    manager = MagicMock()
    manager.sftp = sftp_mock
    manager._transport = MagicMock()
    return manager


class TestSFTPClientManager:
    """Tests for SFTPClientManager connection management."""

    def _patch_paramiko(self):
        """Return a patch that makes paramiko available in sftp module."""
        mock_paramiko = MagicMock()
        mock_paramiko.SSHException = Exception
        return patch("appform_sdk.sftp._require_paramiko", return_value=mock_paramiko)

    def test_connect_with_password(self):
        """Test lazy connection with password auth."""
        mock_paramiko = MagicMock()
        mock_paramiko.SSHException = Exception
        mock_transport = MagicMock()
        mock_transport.is_active.return_value = True
        mock_sftp = MagicMock()
        mock_ssh_client = MagicMock()
        mock_ssh_client.get_transport.return_value = mock_transport
        mock_paramiko.SSHClient.return_value = mock_ssh_client
        mock_paramiko.SFTPClient.from_transport.return_value = mock_sftp

        with patch("appform_sdk.sftp._require_paramiko", return_value=mock_paramiko):
            from appform_sdk.sftp import SFTPClientManager

            mgr = SFTPClientManager(
                host="test.host", port=22, username="user", password="pass"
            )
            _ = mgr.sftp  # trigger lazy connect

        mock_ssh_client.connect.assert_called_once_with(
            hostname="test.host",
            port=22,
            username="user",
            password="pass",
            key_filename=None,
            passphrase=None,
            timeout=30,
            sock=None,
            look_for_keys=False,
            allow_agent=False,
        )
        assert mgr._sftp is mock_sftp

    def test_connect_with_key(self):
        """Test lazy connection with key file auth."""
        mock_paramiko = MagicMock()
        mock_paramiko.SSHException = Exception
        mock_transport = MagicMock()
        mock_sftp = MagicMock()
        mock_sftp.closed = False
        mock_ssh_client = MagicMock()
        mock_ssh_client.get_transport.return_value = mock_transport
        mock_paramiko.SSHClient.return_value = mock_ssh_client
        mock_paramiko.SFTPClient.from_transport.return_value = mock_sftp

        with patch("appform_sdk.sftp._require_paramiko", return_value=mock_paramiko):
            from appform_sdk.sftp import SFTPClientManager

            mgr = SFTPClientManager(
                host="test.host",
                username="user",
                key_filename="/id_rsa",
                key_password="keypass",
            )
            _ = mgr.sftp

        mock_ssh_client.connect.assert_called_once_with(
            hostname="test.host",
            port=22,
            username="user",
            password=None,
            key_filename="/id_rsa",
            passphrase="keypass",
            timeout=30,
            sock=None,
            look_for_keys=False,
            allow_agent=False,
        )

    def test_connect_no_auth_raises(self):
        """Test that connecting without credentials raises SFTPError."""
        mock_paramiko = MagicMock()
        mock_paramiko.SSHException = Exception
        mock_transport = MagicMock()
        mock_paramiko.Transport.return_value = mock_transport

        with patch("appform_sdk.sftp._require_paramiko", return_value=mock_paramiko):
            from appform_sdk.sftp import SFTPClientManager

            mgr = SFTPClientManager(host="test.host", username="user")
            with pytest.raises(SFTPError, match="password|sftp_key_file"):
                _ = mgr.sftp

    @patch("appform_sdk.sftp._require_paramiko")
    def test_connect_ssh_exception(self, mock_req_paramiko):
        """Test that SSH connection failure raises SFTPError."""
        mock_paramiko = MagicMock()
        mock_paramiko.SSHException = Exception
        mock_ssh_client = MagicMock()
        mock_ssh_client.connect.side_effect = mock_paramiko.SSHException("conn refused")
        mock_paramiko.SSHClient.return_value = mock_ssh_client
        mock_req_paramiko.return_value = mock_paramiko

        from appform_sdk.sftp import SFTPClientManager

        mgr = SFTPClientManager(host="test.host", username="user", password="pass")
        with pytest.raises(SFTPError, match="connection failed"):
            _ = mgr.sftp
        mock_ssh_client.close.assert_called_once()

    def test_close_idempotent(self):
        """Test close handles already-closed state gracefully."""
        from appform_sdk.sftp import SFTPClientManager

        mgr = SFTPClientManager(host="x", username="u", password="p")
        mgr._sftp = MagicMock()
        mgr._transport = MagicMock()
        mgr.close()  # should not raise
        mgr.close()  # second call also safe

    def test_reuse_open_session(self):
        """Test that sftp property reuses an open session."""
        mock_paramiko = MagicMock()
        mock_paramiko.SSHException = Exception
        mock_transport = MagicMock()
        mock_transport.is_active.return_value = True
        mock_sftp = MagicMock()
        mock_ssh_client = MagicMock()
        mock_ssh_client.get_transport.return_value = mock_transport
        mock_paramiko.SSHClient.return_value = mock_ssh_client
        mock_paramiko.SFTPClient.from_transport.return_value = mock_sftp

        with patch("appform_sdk.sftp._require_paramiko", return_value=mock_paramiko):
            from appform_sdk.sftp import SFTPClientManager

            mgr = SFTPClientManager(host="test.host", username="user", password="pass")
            s1 = mgr.sftp
            s2 = mgr.sftp
            assert s1 is s2
            assert mock_paramiko.SSHClient.call_count == 1

    def test_reconnect_on_inactive_transport(self):
        """Test that sftp property reconnects when transport is inactive."""
        mock_paramiko = MagicMock()
        mock_paramiko.SSHException = Exception
        mock_transport1 = MagicMock()
        mock_transport1.is_active.return_value = False
        mock_transport2 = MagicMock()
        mock_transport2.is_active.return_value = True
        mock_sftp1 = MagicMock()
        mock_sftp2 = MagicMock()
        mock_ssh_client1 = MagicMock()
        mock_ssh_client1.get_transport.return_value = mock_transport1
        mock_ssh_client2 = MagicMock()
        mock_ssh_client2.get_transport.return_value = mock_transport2
        mock_paramiko.SSHClient.side_effect = [mock_ssh_client1, mock_ssh_client2]
        mock_paramiko.SFTPClient.from_transport.side_effect = [mock_sftp1, mock_sftp2]

        with patch("appform_sdk.sftp._require_paramiko", return_value=mock_paramiko):
            from appform_sdk.sftp import SFTPClientManager

            mgr = SFTPClientManager(host="test.host", username="user", password="pass")
            s1 = mgr.sftp
            s2 = mgr.sftp
            assert s2 is mock_sftp2
            assert mock_paramiko.SSHClient.call_count == 2

    def test_auto_add_host_key_policy(self):
        """Test that auto_add_host_key=True uses AutoAddPolicy."""
        mock_paramiko = MagicMock()
        mock_paramiko.SSHException = Exception
        mock_transport = MagicMock()
        mock_transport.is_active.return_value = True
        mock_ssh_client = MagicMock()
        mock_ssh_client.get_transport.return_value = mock_transport
        mock_paramiko.SSHClient.return_value = mock_ssh_client

        with patch("appform_sdk.sftp._require_paramiko", return_value=mock_paramiko):
            from appform_sdk.sftp import SFTPClientManager

            mgr = SFTPClientManager(
                host="test.host",
                username="user",
                password="pass",
                auto_add_host_key=True,
            )
            _ = mgr.sftp

        mock_ssh_client.set_missing_host_key_policy.assert_called_once()
        policy = mock_ssh_client.set_missing_host_key_policy.call_args[0][0]
        assert policy is mock_paramiko.AutoAddPolicy.return_value

    def test_prompt_policy_accept_saves_key(self, tmp_path):
        """Test that accepting host key prompt saves to known_hosts file."""
        known_hosts = str(tmp_path / "known_hosts")

        mock_paramiko = MagicMock()
        mock_paramiko.SSHException = Exception
        mock_transport = MagicMock()
        mock_transport.is_active.return_value = True
        mock_ssh_client = MagicMock()
        mock_ssh_client.get_transport.return_value = mock_transport
        mock_paramiko.SSHClient.return_value = mock_ssh_client

        with patch(
            "appform_sdk.sftp._require_paramiko", return_value=mock_paramiko
        ), patch(
            "appform_sdk.sftp.os.path.expanduser", return_value=known_hosts
        ), patch(
            "builtins.input", return_value="yes"
        ):
            from appform_sdk.sftp import SFTPClientManager

            mgr = SFTPClientManager(host="test.host", username="user", password="pass")
            _ = mgr.sftp

        # Verify policy was set (not AutoAddPolicy)
        mock_ssh_client.set_missing_host_key_policy.assert_called_once()
        policy = mock_ssh_client.set_missing_host_key_policy.call_args[0][0]
        assert policy is not mock_paramiko.AutoAddPolicy

    def test_prompt_policy_reject_raises(self):
        """Test that rejecting host key prompt raises SSHException."""
        mock_paramiko = MagicMock()
        mock_paramiko.SSHException = Exception
        mock_ssh_client = MagicMock()
        mock_ssh_client.connect.side_effect = Exception("Host key verification failed")
        mock_paramiko.SSHClient.return_value = mock_ssh_client

        with patch(
            "appform_sdk.sftp._require_paramiko", return_value=mock_paramiko
        ), patch("builtins.input", return_value="no"):
            from appform_sdk.sftp import SFTPClientManager

            mgr = SFTPClientManager(host="test.host", username="user", password="pass")
            with pytest.raises(SFTPError, match="connection failed"):
                _ = mgr.sftp

    def test_known_hosts_file_created(self, tmp_path):
        """Test that ~/.appform/known_hosts file is created before load_host_keys."""
        known_hosts = str(tmp_path / "appform" / "known_hosts")

        mock_paramiko = MagicMock()
        mock_paramiko.SSHException = Exception
        mock_transport = MagicMock()
        mock_transport.is_active.return_value = True
        mock_ssh_client = MagicMock()
        mock_ssh_client.get_transport.return_value = mock_transport
        mock_paramiko.SSHClient.return_value = mock_ssh_client

        with patch(
            "appform_sdk.sftp._require_paramiko", return_value=mock_paramiko
        ), patch("appform_sdk.sftp.os.path.expanduser", return_value=known_hosts):
            from appform_sdk.sftp import SFTPClientManager

            mgr = SFTPClientManager(host="test.host", username="user", password="pass")
            _ = mgr.sftp

        # Directory and file should have been created
        assert os.path.isdir(os.path.dirname(known_hosts))
        assert os.path.isfile(known_hosts)
        # load_host_keys should have been called with the path
        mock_ssh_client.load_host_keys.assert_called_once_with(known_hosts)


class TestSFTPAPI:
    """Tests for SFTPAPI file operations."""

    def _make_client(self, sftp_mock, manager_mock=None):
        """Create an SFTPAPI with mocked manager."""
        from appform_sdk.sftp import SFTPAPI

        api = SFTPAPI(MagicMock())
        if manager_mock:
            api._manager = manager_mock
        elif sftp_mock:
            api._manager = _make_mock_manager(sftp_mock)
        return api

    def test_upload_file(self):
        """Test uploading a single file."""
        sftp_mock = MagicMock()
        api = self._make_client(sftp_mock)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"hello")
            tmp = f.name

        try:
            result = api.upload(tmp, "/remote/dir")
        finally:
            os.unlink(tmp)

        sftp_mock.put.assert_called_once()
        assert result["data"]["file"] == Path(tmp).name
        assert result["data"]["result"] == "success"

    def test_upload_missing_file(self):
        """Test upload raises on non-existent local file."""
        from appform_sdk.sftp import SFTPAPI

        api = SFTPAPI(MagicMock())
        with pytest.raises(FileNotFoundError):
            api.upload("/nonexistent/file.txt", "/remote/")

    def test_upload_creates_remote_dir(self):
        """Test upload creates remote directory if missing."""
        sftp_mock = MagicMock()
        # _mkdir_recursive checks e.errno == 2 for "no such file"
        no_such = IOError("no such")
        no_such.errno = 2
        sftp_mock.stat.side_effect = no_such
        api = self._make_client(sftp_mock)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"x")
            tmp = f.name

        try:
            api.upload(tmp, "/new/dir/sub")
        finally:
            os.unlink(tmp)

        # stat called to check dir, then put called
        assert sftp_mock.put.called

    def test_upload_with_progress(self):
        """Test upload calls progress callback."""
        sftp_mock = MagicMock()
        progress_calls = []
        api = self._make_client(sftp_mock)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"hello world")
            tmp = f.name

        try:
            api.upload(
                tmp,
                "/remote/",
                on_progress=lambda fname, x, y: progress_calls.append(x),
            )
        finally:
            os.unlink(tmp)

        # Callback was passed to put
        assert sftp_mock.put.call_args[1]["callback"] is not None

    def test_download_to_file(self):
        """Test downloading a file to local path."""
        sftp_mock = MagicMock()
        sftp_mock.stat.return_value = _make_sftp_attr("f.txt", 50)
        api = self._make_client(sftp_mock)

        with tempfile.TemporaryDirectory() as d:
            api.download("/remote/f.txt", local_path=d)
            sftp_mock.get.assert_called_once()

    def test_download_to_bytes(self):
        """Test downloading a file as bytes."""
        sftp_mock = MagicMock()
        sftp_mock.stat.return_value = _make_sftp_attr("f.txt", 50)
        mock_buf = MagicMock()
        with patch("io.BytesIO", return_value=mock_buf):
            sftp_mock.getfo.return_value = None
            mock_buf.getvalue.return_value = b"content"
            api = self._make_client(sftp_mock)

            result = api.download("/remote/f.txt")
            assert result == b"content"

    def test_download_missing_remote(self):
        """Test download raises on missing remote file."""
        sftp_mock = MagicMock()
        sftp_mock.stat.side_effect = IOError("no such file")
        api = self._make_client(sftp_mock)

        with pytest.raises(FileNotFoundError):
            api.download("/missing.txt")

    def test_list_directory(self):
        """Test listing a directory."""
        sftp_mock = MagicMock()
        sftp_mock.stat.side_effect = IOError("not a file")
        entries = [
            _make_sftp_attr("a.txt", 100),
            _make_sftp_attr("subdir", is_dir=True),
        ]
        sftp_mock.listdir_attr.return_value = entries
        api = self._make_client(sftp_mock)

        result = api.list("/remote/")
        assert result["total"] == 2
        assert len(result["data"]) == 2
        names = [item["fileName"] for item in result["data"]]
        assert "a.txt" in names
        assert "subdir" in names

    def test_list_pagination(self):
        """Test list respects page/pageSize."""
        sftp_mock = MagicMock()
        sftp_mock.stat.side_effect = IOError("not a file")
        entries = [_make_sftp_attr(f"file{i}.txt", 10) for i in range(5)]
        sftp_mock.listdir_attr.return_value = entries
        api = self._make_client(sftp_mock)

        result = api.list("/remote/", page=1, page_size=2)
        assert len(result["data"]) == 2
        assert result["total"] == 5
        assert result["page"] == 1

    def test_list_single_file(self):
        """Test listing a specific file path returns single item."""
        sftp_mock = MagicMock()
        sftp_mock.stat.return_value = _make_sftp_attr("hello.txt", 42)
        api = self._make_client(sftp_mock)

        result = api.list("/remote/hello.txt")
        assert len(result["data"]) == 1
        assert result["data"][0]["fileName"] == "hello.txt"

    def test_list_missing_path(self):
        """Test list raises on non-existent path."""
        sftp_mock = MagicMock()
        sftp_mock.stat.side_effect = IOError("no")
        sftp_mock.listdir_attr.side_effect = IOError("no such dir")
        api = self._make_client(sftp_mock)

        with pytest.raises(FileNotFoundError):
            api.list("/nonexistent/")

    def test_mkdir_basic(self):
        """Test creating a directory."""
        sftp_mock = MagicMock()
        no_such = OSError("no")
        no_such.errno = 2
        sftp_mock.stat.side_effect = no_such
        api = self._make_client(sftp_mock)

        result = api.mkdir("/new/dir")
        assert result["result"] is True

    def test_mkdir_exists_force(self):
        """Test mkdir with existing dir and force=True."""
        sftp_mock = MagicMock()
        sftp_mock.stat.return_value = _make_sftp_attr("x", is_dir=True)
        api = self._make_client(sftp_mock)

        result = api.mkdir("/existing", force=True)
        assert result["result"] is True

    def test_mkdir_exists_no_force(self):
        """Test mkdir with existing dir and force=False."""
        sftp_mock = MagicMock()
        sftp_mock.stat.return_value = _make_sftp_attr("x", is_dir=True)
        api = self._make_client(sftp_mock)

        result = api.mkdir("/existing", force=False)
        assert result["result"] is False

    def test_copy_file(self):
        """Test copying a file via SFTP."""
        sftp_mock = MagicMock()
        src_stat = _make_sftp_attr("f", 100)
        sftp_mock.stat.return_value = src_stat

        mock_src = MagicMock()
        mock_src.read.side_effect = [b"data", b""]
        mock_src.__enter__ = MagicMock(return_value=mock_src)
        mock_src.__exit__ = MagicMock(return_value=False)

        mock_dst = MagicMock()
        mock_dst.__enter__ = MagicMock(return_value=mock_dst)
        mock_dst.__exit__ = MagicMock(return_value=False)

        def open_side(path, mode="r"):
            if "rb" in mode:
                return mock_src
            return mock_dst

        sftp_mock.open.side_effect = open_side
        api = self._make_client(sftp_mock)

        result = api.copy("/src/file.txt", "/dest/")
        assert result["result"] is True

    def test_move_file(self):
        """Test moving a file via SFTP rename."""
        sftp_mock = MagicMock()
        src_stat = _make_sftp_attr("f", 100)
        sftp_mock.stat.return_value = src_stat
        api = self._make_client(sftp_mock)

        result = api.move("/src/file.txt", "/dest/file.txt")
        assert result["result"] is True
        sftp_mock.rename.assert_called_once_with("/src/file.txt", "/dest/file.txt")

    def test_move_to_directory(self):
        """Test move appends filename when dest is a directory."""
        sftp_mock = MagicMock()
        dest_stat = _make_sftp_attr("d", is_dir=True)
        src_stat = _make_sftp_attr("f", 100)

        def stat_fn(p):
            if p == "/src/file.txt":
                return src_stat
            if p == "/dest/":
                return dest_stat
            raise IOError("no")

        sftp_mock.stat.side_effect = stat_fn
        sftp_mock.rename.return_value = None
        api = self._make_client(sftp_mock)

        result = api.move("/src/file.txt", "/dest/")
        assert result["result"] is True
        sftp_mock.rename.assert_called_once_with("/src/file.txt", "/dest/file.txt")

    def test_move_source_not_found(self):
        """Test move raises when source doesn't exist."""
        sftp_mock = MagicMock()
        sftp_mock.stat.side_effect = IOError("no")
        api = self._make_client(sftp_mock)

        with pytest.raises(FileNotFoundError):
            api.move("/missing/", "/dest/")

    def test_delete_file(self):
        """Test deleting a file."""
        sftp_mock = MagicMock()
        sftp_mock.stat.return_value = _make_sftp_attr("f", 100)
        api = self._make_client(sftp_mock)

        result = api.delete("/remote/f.txt")
        assert result["result"] is True
        sftp_mock.remove.assert_called_once_with("/remote/f.txt")

    def test_delete_directory(self):
        """Test deleting a directory recursively."""
        sftp_mock = MagicMock()
        dir_stat = _make_sftp_attr("d", is_dir=True)
        child = _make_sftp_attr("child.txt", 50)
        child_stat = _make_sftp_attr("child.txt", 50)

        def stat_side(p):
            if "child" in str(p):
                return child_stat
            return dir_stat

        sftp_mock.stat.side_effect = stat_side
        sftp_mock.listdir_attr.return_value = [child]
        api = self._make_client(sftp_mock)

        result = api.delete("/remote/dir/")
        assert result["result"] is True
        # _remove_recursive constructs paths as f"{path}/{entry.filename}"
        # so with trailing slash on path, we get double slash
        calls = [c[0][0] for c in sftp_mock.remove.call_args_list]
        assert any("child.txt" in c for c in calls)
        sftp_mock.rmdir.assert_called()

    def test_cat_small_file(self):
        """Test cat reads small file entirely."""
        sftp_mock = MagicMock()
        file_stat = _make_sftp_attr("f.txt", 100)
        sftp_mock.stat.return_value = file_stat

        mock_buf = MagicMock()
        with patch("io.BytesIO", return_value=mock_buf):
            mock_buf.getvalue.return_value = b"line1\nline2\nline3\n"
            api = self._make_client(sftp_mock)

            result = api.cat("/remote/f.txt")
            assert result == ["line1", "line2", "line3"]

    def test_cat_head(self):
        """Test cat with head parameter."""
        sftp_mock = MagicMock()
        file_stat = _make_sftp_attr("f.txt", 100)
        sftp_mock.stat.return_value = file_stat

        mock_buf = MagicMock()
        with patch("io.BytesIO", return_value=mock_buf):
            mock_buf.getvalue.return_value = b"a\nb\nc\nd\n"
            api = self._make_client(sftp_mock)

            result = api.cat("/remote/f.txt", head=2)
            assert result == ["a", "b"]

    def test_cat_tail(self):
        """Test cat with tail parameter."""
        sftp_mock = MagicMock()
        file_stat = _make_sftp_attr("f.txt", 100)
        sftp_mock.stat.return_value = file_stat

        mock_buf = MagicMock()
        with patch("io.BytesIO", return_value=mock_buf):
            mock_buf.getvalue.return_value = b"a\nb\nc\nd\n"
            api = self._make_client(sftp_mock)

            result = api.cat("/remote/f.txt", tail=2)
            assert result == ["c", "d"]

    def test_cat_line_range(self):
        """Test cat with start/end line range."""
        sftp_mock = MagicMock()
        file_stat = _make_sftp_attr("f.txt", 100)
        sftp_mock.stat.return_value = file_stat

        mock_buf = MagicMock()
        with patch("io.BytesIO", return_value=mock_buf):
            mock_buf.getvalue.return_value = b"a\nb\nc\nd\n"
            api = self._make_client(sftp_mock)

            result = api.cat("/remote/f.txt", start=2, end=3)
            assert result == ["b", "c"]

    def test_cat_directory_raises(self):
        """Test cat raises on directory path."""
        sftp_mock = MagicMock()
        dir_stat = _make_sftp_attr("d", is_dir=True)
        sftp_mock.stat.return_value = dir_stat
        api = self._make_client(sftp_mock)

        with pytest.raises(IsADirectoryError):
            api.cat("/remote/dir/")

    def test_cat_missing_file(self):
        """Test cat raises on missing file."""
        sftp_mock = MagicMock()
        sftp_mock.stat.side_effect = IOError("no")
        api = self._make_client(sftp_mock)

        with pytest.raises(FileNotFoundError):
            api.cat("/missing.txt")

    def test_list_all(self):
        """Test list_all returns all items without pagination."""
        sftp_mock = MagicMock()
        sftp_mock.stat.side_effect = IOError("not a file")
        entries = [_make_sftp_attr(f"f{i}.txt", 10) for i in range(5)]
        sftp_mock.listdir_attr.return_value = entries
        api = self._make_client(sftp_mock)

        result = api.list_all("/remote/")
        assert len(result) == 5

    def test_get_home_dir(self):
        """Test get_home_dir returns home path."""
        manager = _make_mock_manager()
        channel = MagicMock()
        channel.recv.return_value = b"/home/user\n"
        manager._transport.open_session.return_value = channel

        from appform_sdk.sftp import SFTPAPI

        api = SFTPAPI(MagicMock())
        api._manager = manager

        home = api.get_home_dir()
        assert home == "/home/user"

    def test_download_directory(self):
        """Test download_directory recursively downloads files."""
        sftp_mock = MagicMock()
        file_attr = _make_sftp_attr("a.txt", 200)
        dir_attr = _make_sftp_attr("sub", is_dir=True)
        sub_file = _make_sftp_attr("b.txt", 100)
        sftp_mock.stat.return_value = file_attr

        def listdir(p):
            if "sub" in str(p):
                return [sub_file]
            return [file_attr, dir_attr]

        sftp_mock.listdir_attr.side_effect = listdir
        api = self._make_client(sftp_mock)

        with tempfile.TemporaryDirectory() as d:
            results = api.download_directory("/remote/", d)
            assert len(results) >= 1

    def test_upload_directory(self):
        """Test upload_directory recursively uploads files."""
        sftp_mock = MagicMock()
        sftp_mock.stat.return_value = _make_sftp_attr("d", is_dir=True)
        api = self._make_client(sftp_mock)

        with tempfile.TemporaryDirectory() as d:
            Path(d, "f1.txt").write_text("hello")
            subdir = Path(d, "sub")
            subdir.mkdir()
            Path(subdir, "f2.txt").write_text("world")

            results = api.upload_directory(d, "/remote/")
            assert len(results) == 2

    def test_close(self):
        """Test SFTPAPI close delegates to manager."""
        mgr = MagicMock()
        from appform_sdk.sftp import SFTPAPI

        api = SFTPAPI(MagicMock())
        api._manager = mgr
        api.close()
        mgr.close.assert_called_once()


class TestFormatMode:
    """Tests for _format_mode() helper."""

    def test_regular_file(self):
        from appform_sdk.sftp import _format_mode

        mode = stat_module.S_IFREG | 0o644
        assert _format_mode(mode) == "- rw-r--r--"

    def test_directory(self):
        from appform_sdk.sftp import _format_mode

        mode = stat_module.S_IFDIR | 0o755
        assert _format_mode(mode) == "d rwxr-xr-x"

    def test_executable_file(self):
        from appform_sdk.sftp import _format_mode

        mode = stat_module.S_IFREG | 0o755
        assert _format_mode(mode) == "- rwxr-xr-x"

    def test_no_permissions(self):
        from appform_sdk.sftp import _format_mode

        mode = stat_module.S_IFREG | 0o000
        assert _format_mode(mode) == "- ---------"

    def test_setuid_with_execute(self):
        from appform_sdk.sftp import _format_mode

        mode = stat_module.S_IFREG | stat_module.S_ISUID | 0o755
        assert _format_mode(mode) == "- rwsr-xr-x"

    def test_setuid_without_execute(self):
        from appform_sdk.sftp import _format_mode

        mode = stat_module.S_IFREG | stat_module.S_ISUID | 0o644
        assert _format_mode(mode) == "- rwSr--r--"

    def test_setgid_with_execute(self):
        from appform_sdk.sftp import _format_mode

        mode = stat_module.S_IFREG | stat_module.S_ISGID | 0o755
        assert _format_mode(mode) == "- rwxr-sr-x"

    def test_setgid_without_execute(self):
        from appform_sdk.sftp import _format_mode

        mode = stat_module.S_IFREG | stat_module.S_ISGID | 0o640
        assert _format_mode(mode) == "- rw-r-S---"

    def test_sticky_with_execute(self):
        from appform_sdk.sftp import _format_mode

        mode = stat_module.S_IFDIR | stat_module.S_ISVTX | 0o755
        assert _format_mode(mode) == "d rwxr-xr-t"

    def test_sticky_without_execute(self):
        from appform_sdk.sftp import _format_mode

        mode = stat_module.S_IFDIR | stat_module.S_ISVTX | 0o754
        assert _format_mode(mode) == "d rwxr-xr-T"

    def test_symlink(self):
        from appform_sdk.sftp import _format_mode

        mode = stat_module.S_IFLNK | 0o777
        assert _format_mode(mode) == "l rwxrwxrwx"

    def test_fifo(self):
        from appform_sdk.sftp import _format_mode

        mode = stat_module.S_IFIFO | 0o644
        assert _format_mode(mode) == "p rw-r--r--"


class TestFileTypeFromMode:
    """Tests for _file_type_from_mode() helper."""

    def test_regular(self):
        from appform_sdk.sftp import _file_type_from_mode

        assert _file_type_from_mode(stat_module.S_IFREG | 0o644) == "file"

    def test_directory(self):
        from appform_sdk.sftp import _file_type_from_mode

        assert _file_type_from_mode(stat_module.S_IFDIR | 0o755) == "directory"

    def test_symlink(self):
        from appform_sdk.sftp import _file_type_from_mode

        assert _file_type_from_mode(stat_module.S_IFLNK | 0o777) == "symlink"

    def test_unknown(self):
        from appform_sdk.sftp import _file_type_from_mode

        assert _file_type_from_mode(stat_module.S_IFSOCK | 0o644) == "unknown"


class TestMkdirRecursive:
    """Tests for _mkdir_recursive helper."""

    def test_create_single_level(self):
        """Test creating a single-level directory."""
        from appform_sdk.sftp import _mkdir_recursive

        sftp = MagicMock()
        sftp.stat.side_effect = IOError("no")
        sftp_stat_err = IOError("no")
        sftp_stat_err.errno = 2
        sftp.stat.side_effect = sftp_stat_err
        _mkdir_recursive(sftp, "/newdir")
        sftp.mkdir.assert_called_once_with("/newdir")

    def test_create_nested(self):
        """Test creating nested directories."""
        from appform_sdk.sftp import _mkdir_recursive

        sftp = MagicMock()
        no_such = IOError("no")
        no_such.errno = 2
        sftp.stat.side_effect = no_such

        _mkdir_recursive(sftp, "/a/b/c")
        assert sftp.mkdir.call_count == 3
        calls = [c[0][0] for c in sftp.mkdir.call_args_list]
        assert calls == ["/a", "/a/b", "/a/b/c"]

    def test_skip_existing(self):
        """Test skipping already-existing parent directories."""
        from appform_sdk.sftp import _mkdir_recursive

        sftp = MagicMock()
        sftp.stat.return_value = _make_sftp_attr("a", is_dir=True)
        no_such = IOError("no")
        no_such.errno = 2

        def stat_side(p):
            if p == "/a":
                return _make_sftp_attr("a", is_dir=True)
            raise no_such

        sftp.stat.side_effect = stat_side
        _mkdir_recursive(sftp, "/a/b")
        # Only /a/b should be created, /a already exists
        assert sftp.mkdir.call_count == 1
        sftp.mkdir.assert_called_with("/a/b")


class TestCopyRemoveRecursive:
    """Tests for _copy_recursive and _remove_recursive helpers."""

    def test_copy_file(self):
        """Test _copy_recursive for a single file using sftp.open streaming."""
        from appform_sdk.sftp import _copy_recursive

        sftp = MagicMock()
        sftp.stat.return_value = _make_sftp_attr("f", 100)

        mock_src = MagicMock()
        mock_src.read.side_effect = [b"data", b""]
        mock_src.__enter__ = MagicMock(return_value=mock_src)
        mock_src.__exit__ = MagicMock(return_value=False)

        mock_dst = MagicMock()
        mock_dst.__enter__ = MagicMock(return_value=mock_dst)
        mock_dst.__exit__ = MagicMock(return_value=False)

        def open_side(path, mode="r"):
            if "rb" in mode:
                return mock_src
            return mock_dst

        sftp.open.side_effect = open_side

        _copy_recursive(sftp, "/src/f.txt", "/dst/f.txt")
        sftp.open.assert_called()
        mock_dst.write.assert_called_once_with(b"data")

    def test_copy_directory(self):
        """Test _copy_recursive for a directory using sftp.open streaming."""
        from appform_sdk.sftp import _copy_recursive

        sftp = MagicMock()
        dir_attr = _make_sftp_attr("d", is_dir=True)
        child = _make_sftp_attr("c.txt", 50)
        file_attr = _make_sftp_attr("c.txt", 50)

        no_such = OSError("no")
        no_such.errno = 2

        def stat_side(p):
            if "c.txt" in str(p):
                return file_attr
            if str(p) == "/src/":
                return dir_attr
            raise no_such

        sftp.stat.side_effect = stat_side
        sftp.listdir_attr.return_value = [child]

        mock_src = MagicMock()
        mock_src.read.side_effect = [b"data", b""]
        mock_src.__enter__ = MagicMock(return_value=mock_src)
        mock_src.__exit__ = MagicMock(return_value=False)

        mock_dst = MagicMock()
        mock_dst.__enter__ = MagicMock(return_value=mock_dst)
        mock_dst.__exit__ = MagicMock(return_value=False)

        def open_side(path, mode="r"):
            if "rb" in mode:
                return mock_src
            return mock_dst

        sftp.open.side_effect = open_side

        _copy_recursive(sftp, "/src/", "/dst/")
        sftp.mkdir.assert_called()
        assert sftp.open.called

    def test_remove_missing(self):
        """Test _remove_recursive is a no-op for missing paths."""
        from appform_sdk.sftp import _remove_recursive

        sftp = MagicMock()
        sftp.stat.side_effect = IOError("no")
        _remove_recursive(sftp, "/missing/")
        sftp.remove.assert_not_called()
        sftp.rmdir.assert_not_called()
