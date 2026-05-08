"""
Tests for appform_sdk.files utility functions:
parse_size, _is_remote_path, _resolve_remote_path, _ProgressTracker.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from appform_sdk.files import (
    _is_remote_path,
    _MultipartBody,
    _ProgressTracker,
    _resolve_remote_path,
    parse_size,
)

# ── parse_size ───────────────────────────────────────────────────────────


class TestParseSize:
    def test_raw_bytes_int(self):
        assert parse_size(1024) == 1024

    def test_raw_bytes_float(self):
        assert parse_size(1024.5) == 1024

    def test_raw_bytes_string(self):
        assert parse_size("1048576") == 1048576

    def test_kilobytes(self):
        assert parse_size("256K") == 256 * 1024
        assert parse_size("256KB") == 256 * 1024
        assert parse_size("256k") == 256 * 1024
        assert parse_size("256kb") == 256 * 1024

    def test_megabytes(self):
        assert parse_size("30M") == 30 * 1024**2
        assert parse_size("30MB") == 30 * 1024**2

    def test_gigabytes(self):
        assert parse_size("1G") == 1024**3
        assert parse_size("1GB") == 1024**3

    def test_terabytes(self):
        assert parse_size("1T") == 1024**4
        assert parse_size("1TB") == 1024**4

    def test_decimal(self):
        assert parse_size("1.5G") == int(1.5 * 1024**3)

    def test_bytes_unit(self):
        assert parse_size("100B") == 100

    def test_whitespace_stripped(self):
        assert parse_size("  256K  ") == 256 * 1024

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid size format"):
            parse_size("abc")

    def test_invalid_unit(self):
        with pytest.raises(ValueError, match="Invalid size format"):
            parse_size("100XB")


# ── _is_remote_path ──────────────────────────────────────────────────────


class TestIsRemotePath:
    def test_remote_absolute(self):
        assert _is_remote_path("/home/user/file.txt") is True

    def test_remote_root(self):
        assert _is_remote_path("/") is True

    def test_local_relative(self):
        assert _is_remote_path("file.txt") is False

    def test_local_relative_dir(self):
        assert _is_remote_path("dir/file.txt") is False

    def test_empty(self):
        assert _is_remote_path("") is False


# ── _resolve_remote_path ─────────────────────────────────────────────────


class TestResolveRemotePath:
    def test_already_remote(self):
        assert _resolve_remote_path("/home/user/file.txt") == "/home/user/file.txt"

    def test_relative_default_root(self):
        assert _resolve_remote_path("file.txt") == "/file.txt"

    def test_relative_custom_default(self):
        assert _resolve_remote_path("file.txt", "/data") == "/data/file.txt"

    def test_relative_with_subdir(self):
        assert _resolve_remote_path("sub/file.txt", "/data") == "/data/sub/file.txt"

    def test_default_trailing_slash(self):
        assert _resolve_remote_path("file.txt", "/data/") == "/data/file.txt"


# ── _ProgressTracker ─────────────────────────────────────────────────────


class TestProgressTracker:
    def test_init(self):
        t = _ProgressTracker(label="Upload", total=100)
        assert t.label == "Upload"
        assert t.total == 100
        assert t.current == 0

    def test_update_with_3_args(self, capsys):
        t = _ProgressTracker(label="Test", total=100)
        t.update("ignored", 50, 100)
        assert t.current == 50
        assert t.total == 100

    def test_update_with_2_args(self, capsys):
        t = _ProgressTracker(label="Test", total=0)
        t.update(30, 100)
        assert t.current == 30
        assert t.total == 100

    def test_update_with_1_arg(self, capsys):
        t = _ProgressTracker(label="Test", total=100)
        t.update(75)
        assert t.current == 75

    def test_progress_bar_output(self, capsys):
        t = _ProgressTracker(label="Test", total=100)
        t.update(50)
        captured = capsys.readouterr()
        assert "50%" in captured.err
        assert "█" in captured.err

    def test_zero_total(self, capsys):
        t = _ProgressTracker(label="Test", total=0)
        t.update(10)
        captured = capsys.readouterr()
        assert "10 items" in captured.err

    def test_finish(self, capsys):
        t = _ProgressTracker(label="Test", total=100)
        t.finish()
        captured = capsys.readouterr()
        assert "\n" in captured.err


# ── _MultipartBody ───────────────────────────────────────────────────────


class TestMultipartBody:
    def _make_temp_file(self, content=b"hello world"):
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        f.write(content)
        f.close()
        return f.name

    def test_len(self):
        filepath = self._make_temp_file()
        try:
            body = _MultipartBody(filepath, {"key": "val"}, "boundary123")
            expected = len(body._prefix) + len(b"hello world") + len(body._suffix)
            assert len(body) == expected
        finally:
            os.unlink(filepath)

    def test_read_all(self):
        filepath = self._make_temp_file(b"test data")
        try:
            body = _MultipartBody(filepath, {"k": "v"}, "bound")
            chunks = []
            while True:
                chunk = body.read(8192)
                if not chunk:
                    break
                chunks.append(chunk)
            full = b"".join(chunks)
            assert b"test data" in full
            assert b"--bound--" in full
            assert b'Content-Disposition: form-data; name="k"' in full
        finally:
            os.unlink(filepath)

    def test_progress_callback(self):
        filepath = self._make_temp_file(b"x" * 100)
        try:
            progress_calls = []
            body = _MultipartBody(
                filepath, {}, "bound", on_progress=lambda *a: progress_calls.append(a)
            )
            while body.read(8192):
                pass
            assert len(progress_calls) > 0
        finally:
            os.unlink(filepath)

    def test_seek_tell(self):
        """seek() is a no-op and tell() always returns 0 (streaming body)."""
        filepath = self._make_temp_file()
        try:
            body = _MultipartBody(filepath, {}, "bound")
            assert body.tell() == 0
            body.read(5)
            assert body.tell() == 0  # always 0 — streaming body
            body.seek(0)
            assert body.tell() == 0
        finally:
            os.unlink(filepath)
