"""Tests for formatters.py — format_files_list mode detection."""

from appform_sdk.formatters import format_files_list


class TestFormatFilesList:
    """Tests for format_files_list with SFTP vs HTTP data."""

    def test_http_no_mode(self):
        """HTTP listing has no mode field, uses NAME/OWNER/SIZE/MODIFIED."""
        response = {
            "data": [
                {
                    "fileName": "a.txt",
                    "fileType": "file",
                    "owner": "root",
                    "size": 1024,
                    "ts": "2024-01-01",
                },
                {
                    "fileName": "subdir",
                    "fileType": "directory",
                    "owner": "root",
                    "size": 0,
                    "ts": "2024-01-01",
                },
            ]
        }
        result = format_files_list(response)
        assert "MODE" not in result
        assert "NAME" in result
        assert "OWNER" in result
        assert "[F] a.txt" in result
        assert "[D] subdir" in result

    def test_sftp_with_mode(self):
        """SFTP listing has mode field, uses MODE/NAME/UID/GID/SIZE/MODIFIED."""
        response = {
            "data": [
                {
                    "fileName": "a.txt",
                    "fileType": "file",
                    "mode": "- rw-r--r--",
                    "uid": 1000,
                    "gid": 1000,
                    "size": 1024,
                    "modifiedDate": "2024-01-01",
                },
                {
                    "fileName": "subdir",
                    "fileType": "directory",
                    "mode": "drwxr-xr-x",
                    "uid": 1000,
                    "gid": 1000,
                    "size": 0,
                    "modifiedDate": "2024-01-01",
                },
            ]
        }
        result = format_files_list(response)
        assert "MODE" in result
        assert "- rw-r--r--" in result
        assert "drwxr-xr-x" in result
        assert "OWNER" not in result
        assert "UID" in result

    def test_empty_list(self):
        """Empty file list returns (empty)."""
        response = {"data": []}
        result = format_files_list(response)
        assert result == "(empty)"

    def test_symlink_icon(self):
        """Symlink files show [L] icon."""
        response = {
            "data": [
                {
                    "fileName": "link",
                    "fileType": "symlink",
                    "mode": "lrwxrwxrwx",
                    "uid": 0,
                    "gid": 0,
                    "size": 10,
                    "modifiedDate": "2024-01-01",
                },
            ]
        }
        result = format_files_list(response)
        assert "[L] link" in result

    def test_mixed_mode_detection(self):
        """If any item has mode, all items use the mode column layout."""
        response = {
            "data": [
                {
                    "fileName": "a.txt",
                    "fileType": "file",
                    "mode": "- rw-r--r--",
                    "uid": 0,
                    "gid": 0,
                    "size": 10,
                    "modifiedDate": "2024-01-01",
                },
                {
                    "fileName": "b.txt",
                    "fileType": "file",
                    "uid": 0,
                    "gid": 0,
                    "size": 20,
                    "modifiedDate": "2024-01-01",
                },
            ]
        }
        result = format_files_list(response)
        assert "MODE" in result
