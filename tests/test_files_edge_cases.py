"""Tests for files.py edge cases - move/copy cross-directory operations."""

from unittest.mock import MagicMock

import pytest


def _make_files_api(mock_client=None):
    """Create a FilesAPI with a mocked client."""
    from appform_sdk.files import FilesAPI

    if mock_client is None:
        mock_client = MagicMock()
    return FilesAPI(mock_client)


class TestCrossDirectoryMove:
    """Tests for cross-directory move atomicity in files.py."""

    def test_simple_rename_same_directory(self):
        """Test move without / in dest_dir uses rename directly."""
        api = _make_files_api()
        api.rename = MagicMock(return_value={"result": True})

        result = api.move("/src/file.txt", "newname.txt")
        assert result == {"result": True}
        api.rename.assert_called_once_with("/src/file.txt", "newname.txt")
        api._client.delete.assert_not_called()

    def test_same_dir_different_name_uses_rename(self):
        """Test move with full path but same directory uses rename directly."""
        api = _make_files_api()
        api.rename = MagicMock(return_value={"result": True})

        result = api.move("/src/file.txt", "/src/newname.txt")
        assert result == {"result": True}
        api.rename.assert_called_once_with("/src/file.txt", "newname.txt")
        # Should NOT call copy or delete
        api._client.put.assert_not_called()
        api._client.delete.assert_not_called()

    def test_cross_dir_move_same_name(self):
        """Test cross-directory move preserving the filename."""
        api = _make_files_api()
        api.copy = MagicMock(return_value={"result": True})
        api.delete = MagicMock(return_value={"result": True})

        result = api.move("/src/file.txt", "/dst/file.txt")
        assert result == {"result": True}
        api.copy.assert_called_once_with("/src/file.txt", "/dst")
        # delete src_path should be called after copy
        api.delete.assert_called_once_with("/src/file.txt")

    def test_cross_dir_move_different_name(self):
        """Test cross-directory move with rename."""
        api = _make_files_api()
        api.copy = MagicMock(return_value={"result": True})
        api.rename = MagicMock(return_value={"result": True})
        api.delete = MagicMock(return_value={"result": True})

        result = api.move("/src/file.txt", "/dst/newname.txt")
        assert result == {"result": True}
        # Should copy to parent, rename, then delete source
        api.copy.assert_called_once()
        api.rename.assert_called_once()
        delete_calls = api.delete.call_args_list
        # First delete call should be for source
        assert len(delete_calls) == 1
        api.delete.assert_called_with("/src/file.txt")

    def test_cross_dir_rename_failure_rolls_back(self):
        """Test that rename failure deletes the copy and keeps source."""
        api = _make_files_api()
        api.copy = MagicMock(return_value={"result": True})
        api.rename = MagicMock(side_effect=Exception("rename failed"))
        api.delete = MagicMock(return_value={"result": True})

        with pytest.raises(Exception, match="rename failed"):
            api.move("/src/file.txt", "/dst/newname.txt")

        # copy should have been attempted
        api.copy.assert_called_once()
        # rename should have been attempted
        api.rename.assert_called_once()
        # The copied file should have been deleted on rename failure
        delete_calls = api.delete.call_args_list
        assert len(delete_calls) == 1
        # First delete is the orphaned copy cleanup
        deleted_path = delete_calls[0][0][0]
        assert "newname" in deleted_path or "file.txt" in deleted_path
        # Source should NOT have been deleted
        api.delete.assert_any_call(deleted_path)

    def test_cross_dir_to_root(self):
        """Test cross-directory move where dest parent is root."""
        api = _make_files_api()
        api.copy = MagicMock(return_value={"result": True})
        api.delete = MagicMock(return_value={"result": True})

        result = api.move("/src/file.txt", "/top.txt")
        assert result == {"result": True}
        # dest_parent should be "/", dest_name is "top.txt"
        # src_name is "file.txt", so rename needed
        api.copy.assert_called_once_with("/src/file.txt", "/")

    def test_cross_dir_dest_parent_extraction(self):
        """Test dest_parent extraction for nested paths."""
        api = _make_files_api()
        api.copy = MagicMock(return_value={"result": True})
        api.rename = MagicMock(return_value={"result": True})
        api.delete = MagicMock(return_value={"result": True})

        api.move("/a/b.txt", "/x/y/z/b.txt")
        # dest_parts = ["x", "y", "z", "b.txt"]
        # dest_name = "b.txt", dest_parent = "/x/y/z"
        # src_name = "b.txt", so no rename needed
        api.copy.assert_called_once_with("/a/b.txt", "/x/y/z")
        api.delete.assert_called_once_with("/a/b.txt")
        # No rename since src_name == dest_name
        api.rename.assert_not_called()

    def test_sftp_transfer_method(self):
        """Test move delegates to sftp when transfer_method='sftp'."""
        api = _make_files_api()
        api._client.sftp.move = MagicMock(return_value={"result": True})

        result = api.move("/src/f.txt", "/dst/f.txt", transfer_method="sftp")
        assert result == {"result": True}
        api._client.sftp.move.assert_called_once_with(
            src_path="/src/f.txt", dest_dir="/dst/f.txt"
        )


class TestCopy:
    """Tests for copy operation."""

    def test_copy_http(self):
        """Test HTTP API copy."""
        api = _make_files_api()

        api.copy("/src/f.txt", "/dst/")
        api._client.put.assert_called_once()
        call_kwargs = api._client.put.call_args
        assert call_kwargs[1]["json"]["sourceFileName"] == "/src/f.txt"
        assert call_kwargs[1]["json"]["targetDirectory"] == "/dst/"

    def test_copy_sftp(self):
        """Test SFTP copy delegation."""
        api = _make_files_api()
        api._client.sftp.copy = MagicMock(return_value={"result": True})

        api.copy("/src/f.txt", "/dst/", transfer_method="sftp")
        api._client.sftp.copy.assert_called_once()


class TestDelete:
    """Tests for delete operation."""

    def test_delete_http(self):
        """Test HTTP API delete."""
        api = _make_files_api()

        api.delete("/remote/f.txt")
        api._client.delete.assert_called_once()
        call_kwargs = api._client.delete.call_args
        assert call_kwargs[1]["params"]["fileName"] == "/remote/f.txt"

    def test_delete_sftp(self):
        """Test SFTP delete delegation."""
        api = _make_files_api()
        api._client.sftp.delete = MagicMock(return_value={"result": True})

        api.delete("/f.txt", transfer_method="sftp")
        api._client.sftp.delete.assert_called_once()


class TestMkdir:
    """Tests for mkdir operation."""

    def test_mkdir_http(self):
        """Test HTTP API mkdir."""
        api = _make_files_api()

        api.mkdir("/new/dir", force=False)
        api._client.post.assert_called_once()
        call_kwargs = api._client.post.call_args
        assert call_kwargs[1]["json"]["dirPath"] == "/new/dir"
        assert call_kwargs[1]["json"]["isForce"] == "false"

    def test_mkdir_sftp(self):
        """Test SFTP mkdir delegation."""
        api = _make_files_api()
        api._client.sftp.mkdir = MagicMock(return_value={"result": True})

        api.mkdir("/new/dir", transfer_method="sftp")
        api._client.sftp.mkdir.assert_called_once()


class TestList:
    """Tests for list operations."""

    def test_list_http(self):
        """Test HTTP API list."""
        api = _make_files_api()

        api.list("/path", page=2, page_size=50)
        api._client.get.assert_called_once()
        call_kwargs = api._client.get.call_args
        assert call_kwargs[1]["params"]["dir"] == "/path"
        assert call_kwargs[1]["params"]["page"] == 2
        assert call_kwargs[1]["params"]["pageSize"] == 50

    def test_list_sftp(self):
        """Test SFTP list delegation."""
        api = _make_files_api()
        api._client.sftp.list = MagicMock(return_value={"data": []})

        api.list("/path", transfer_method="sftp")
        api._client.sftp.list.assert_called_once()

    def test_list_all_http_empty(self):
        """Test list_all with empty response."""
        api = _make_files_api()
        api._client.get.return_value = {"data": []}

        result = api.list_all("/path")
        assert result == []

    def test_list_all_http_pagination(self):
        """Test list_all auto-paginates until empty."""
        api = _make_files_api()
        api._client.get.side_effect = [
            {"data": [{"id": i} for i in range(100)]},  # full page
            {"data": [{"id": i + 100} for i in range(50)]},  # partial page
            {"data": []},  # done
        ]

        result = api.list_all("/path")
        assert len(result) == 150

    def test_list_all_http_dict_records(self):
        """Test list_all handles dict with 'records' key."""
        api = _make_files_api()
        api._client.get.side_effect = [
            {"data": {"records": [{"id": i} for i in range(10)], "total": 10}},
            {"data": {"records": [], "total": 10}},
        ]

        result = api.list_all("/path")
        assert len(result) == 10

    def test_list_all_sftp(self):
        """Test list_all delegates to SFTP."""
        api = _make_files_api()
        api._client.sftp.list_all = MagicMock(return_value=[{"id": 1}])

        api.list_all("/path", transfer_method="sftp")
        api._client.sftp.list_all.assert_called_once_with(path="/path", hidden=False)


class TestUploadDownload:
    """Tests for upload/download delegation."""

    def test_upload_sftp(self):
        """Test upload delegates to SFTP."""
        api = _make_files_api()
        api._client.sftp.upload = MagicMock(return_value={"result": True})

        api.upload(
            "/local/f.txt",
            "/remote/",
            on_progress=lambda *a: None,
            transfer_method="sftp",
        )
        api._client.sftp.upload.assert_called_once()

    def test_upload_missing_local_file(self):
        """Test upload raises for missing local file."""
        api = _make_files_api()

        with pytest.raises(FileNotFoundError):
            api.upload("/nonexistent/file.txt", "/remote/")

    def test_download_sftp(self):
        """Test download delegates to SFTP."""
        api = _make_files_api()
        api._client.sftp.download = MagicMock(return_value=b"data")

        api.download("/remote/f.txt", transfer_method="sftp")
        api._client.sftp.download.assert_called_once()

    def test_download_directory_sftp(self):
        """Test download_directory delegates to SFTP."""
        api = _make_files_api()
        api._client.sftp.download_directory = MagicMock(return_value=[])

        api.download_directory("/remote/dir", "/local/dir", transfer_method="sftp")
        api._client.sftp.download_directory.assert_called_once()

    def test_upload_directory_missing(self):
        """Test upload_directory raises for non-directory."""
        api = _make_files_api()

        with pytest.raises(NotADirectoryError):
            api.upload_directory("/not/a/dir", "/remote/")


class TestParseSize:
    """Tests for parse_size utility."""

    def test_raw_bytes(self):
        from appform_sdk.files import parse_size

        assert parse_size("1024") == 1024
        assert parse_size(1024) == 1024
        assert parse_size(1024.0) == 1024

    def test_kb(self):
        from appform_sdk.files import parse_size

        assert parse_size("256K") == 262144
        assert parse_size("256KB") == 262144
        assert parse_size("256k") == 262144

    def test_mb(self):
        from appform_sdk.files import parse_size

        assert parse_size("30M") == 31457280
        assert parse_size("30MB") == 31457280

    def test_gb(self):
        from appform_sdk.files import parse_size

        assert parse_size("1G") == 1073741824

    def test_invalid(self):
        from appform_sdk.files import parse_size

        with pytest.raises(ValueError):
            parse_size("abc")


class TestCompressUncompress:
    """Tests for compress/uncompress operations."""

    def test_compress(self):
        """Test compress API call."""
        api = _make_files_api()

        api.compress("/src/dir", "/dst/archive.zip")
        api._client.post.assert_called_once()
        call_kwargs = api._client.post.call_args
        assert call_kwargs[1]["params"]["sourceDirName"] == "/src/dir"
        assert call_kwargs[1]["params"]["targetFilePath"] == "/dst/archive.zip"

    def test_uncompress(self):
        """Test uncompress API call."""
        api = _make_files_api()

        api.uncompress("/archive.zip", "/dst/")
        api._client.post.assert_called_once()
        call_kwargs = api._client.post.call_args
        assert call_kwargs[1]["params"]["zipFile"] == "/archive.zip"

    def test_uncompress_with_password(self):
        """Test uncompress with password."""
        api = _make_files_api()

        api.uncompress("/archive.zip", "/dst/", password="secret")
        call_kwargs = api._client.post.call_args
        assert call_kwargs[1]["params"]["password"] == "secret"


class TestConfidentiality:
    """Tests for confidentiality level operations."""

    def test_get_confidentiality_levels(self):
        """Test getting confidentiality levels."""
        api = _make_files_api()

        api.get_confidentiality_levels()
        api._client.get.assert_called_once_with("/appform/ws/api/file/conf")

    def test_set_confidentiality(self):
        """Test setting file confidentiality."""
        api = _make_files_api()

        api.set_confidentiality("/file.txt", "level3")
        api._client.post.assert_called_once()
        call_kwargs = api._client.post.call_args
        assert call_kwargs[1]["json"]["path"] == "/file.txt"
        assert call_kwargs[1]["json"]["conf"] == "level3"
