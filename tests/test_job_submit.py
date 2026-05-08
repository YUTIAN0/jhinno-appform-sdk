"""
Tests for path conversion and upload logic in job_submit.py.

Covers:
- convert_windows_path: drive-letter, relative, absolute, mapped-CWD scenarios
- _is_path_mapped: drive-letter, Linux prefix, relative paths
- _resolve_remote_path: drive-letter, Linux prefix resolution
- _apply_path_conversion: comma-separated multi-file values, relative paths
- _apply_uploaded_paths: post-upload path replacement
"""

import os
from unittest.mock import patch

import pytest

from appform_sdk.job_submit import (
    _apply_path_conversion,
    _apply_uploaded_paths,
    _is_path_mapped,
    _resolve_remote_path,
    convert_windows_path,
)

DM = {"S:": "/apps"}  # standard disk_mapping used in most tests


# ── convert_windows_path ─────────────────────────────────────────────────


class TestConvertWindowsPath:
    # --- drive-letter paths (any platform) --------------------------------

    def test_drive_letter_backslash(self):
        assert (
            convert_windows_path(r"S:\home\user\test.k", DM) == "/apps/home/user/test.k"
        )

    def test_drive_letter_forward_slash(self):
        assert (
            convert_windows_path("S:/home/user/test.k", DM) == "/apps/home/user/test.k"
        )

    def test_drive_letter_root_only(self):
        r"""S:\ with nothing after the drive letter."""
        assert convert_windows_path("S:\\", DM) == "/apps"

    def test_drive_letter_unmapped_drive(self):
        """Drive letter present but not in disk_mapping → returned as-is."""
        assert convert_windows_path(r"D:\data\file.k", DM) == r"D:\data\file.k"

    def test_drive_letter_case_insensitive(self):
        """s: (lowercase) should match S: in disk_mapping."""
        assert convert_windows_path(r"s:\home\test.k", DM) == "/apps/home/test.k"

    # --- absolute Linux paths --------------------------------------------

    def test_linux_absolute_on_mapped_drive(self):
        assert (
            convert_windows_path("/apps/home/user/test.k", DM)
            == "/apps/home/user/test.k"
        )

    def test_linux_absolute_unrelated(self):
        assert convert_windows_path("/tmp/test.k", DM) == "/tmp/test.k"

    # --- relative paths with CWD on mapped drive --------------------------

    def test_relative_cwd_on_mapped_linux_prefix(self, tmp_path, monkeypatch):
        r"""CWD is /apps/home/user -> relative path resolved against /apps prefix."""
        # /apps may not exist locally, so patch os.getcwd and os.path.abspath
        with patch(
            "appform_sdk.job_submit.os.getcwd", return_value="/apps/home/user"
        ), patch(
            "appform_sdk.job_submit.os.path.abspath",
            return_value="/apps/home/user/test.k",
        ):
            assert convert_windows_path("test.k", DM) == "/apps/test.k"

    # --- relative paths with CWD on mapped Windows drive ------------------

    def test_relative_cwd_on_mapped_windows_drive(self, monkeypatch):
        r"""CWD is S:\home\p-user\subdir -> abspath gives S:\...\test.k -> converted."""
        with patch(
            "appform_sdk.job_submit.os.getcwd", return_value=r"S:\home\p-user\subdir"
        ), patch(
            "appform_sdk.job_submit.os.path.abspath",
            return_value=r"S:\home\p-user\subdir\test.k",
        ):
            result = convert_windows_path("test.k", DM)
        assert result == "/apps/home/p-user/subdir/test.k"

    def test_relative_cwd_not_on_mapped_drive(self, tmp_path, monkeypatch):
        """CWD is /tmp (not on a mapped drive) → resolves locally."""
        monkeypatch.chdir("/tmp")
        result = convert_windows_path("test.k", DM)
        assert result == "/tmp/test.k"

    # --- edge cases -------------------------------------------------------

    def test_empty_string(self):
        assert convert_windows_path("", DM) == ""

    def test_none_input(self):
        assert convert_windows_path(None, DM) is None

    def test_empty_disk_mapping(self):
        assert convert_windows_path("test.k", {}) == "test.k"

    def test_none_disk_mapping(self):
        assert convert_windows_path("test.k", None) == "test.k"


# ── _is_path_mapped ─────────────────────────────────────────────────────


class TestIsPathMapped:
    def test_linux_absolute_on_mapped_drive(self):
        assert _is_path_mapped("/apps/home/user/test.k", DM) is True

    def test_linux_absolute_not_mapped(self):
        assert _is_path_mapped("/tmp/test.k", DM) is False

    def test_drive_letter_path(self):
        r"""Drive-letter path detected directly — no abspath corruption."""
        assert _is_path_mapped(r"S:\home\user\test.k", DM) is True

    def test_drive_letter_unmapped_drive(self):
        """Different drive letter (D:) not in mapping."""
        assert _is_path_mapped(r"D:\data\file.k", DM) is False

    def test_drive_letter_case_insensitive(self):
        assert _is_path_mapped(r"s:\home\user\test.k", DM) is True

    def test_drive_letter_root_only(self):
        assert _is_path_mapped(r"S:\test.k", DM) is True

    def test_relative_not_mapped(self, tmp_path, monkeypatch):
        monkeypatch.chdir("/tmp")
        assert _is_path_mapped("test.k", DM) is False

    def test_relative_cwd_on_mapped_linux_prefix(self):
        """Relative path when CWD is under a mapped Linux prefix."""
        with patch(
            "appform_sdk.job_submit.os.path.abspath",
            return_value="/apps/home/user/test.k",
        ):
            assert _is_path_mapped("test.k", DM) is True

    def test_empty_path(self):
        assert _is_path_mapped("", DM) is False

    def test_empty_mapping(self):
        assert _is_path_mapped("/apps/test.k", {}) is False

    def test_none_path(self):
        assert _is_path_mapped(None, DM) is False

    def test_none_mapping(self):
        assert _is_path_mapped("/apps/test.k", None) is False

    def test_absolute_linux_path_skips_abspath(self):
        r"""Absolute Linux path must NOT go through os.path.abspath()
        which on Windows would prepend a drive letter (S:\apps\...)."""
        # Simulate Windows behavior: abspath prepends a drive letter
        with patch(
            "appform_sdk.job_submit.os.path.abspath",
            return_value=r"S:\apps\home\user\test.k",
        ):
            # Should still recognize /apps/... as mapped without calling abspath
            assert _is_path_mapped("/apps/home/user/test.k", DM) is True
            assert _is_path_mapped("/tmp/test.k", DM) is False


# ── _resolve_remote_path ────────────────────────────────────────────────


class TestResolveRemotePath:
    def test_linux_absolute_on_mapped_drive(self):
        assert (
            _resolve_remote_path("/apps/home/user/test.k", DM)
            == "/apps/home/user/test.k"
        )

    def test_linux_absolute_not_mapped(self):
        assert _resolve_remote_path("/tmp/test.k", DM) is None

    def test_drive_letter_path(self):
        r"""Drive-letter path detected directly — no abspath corruption."""
        assert (
            _resolve_remote_path(r"S:\home\user\test.k", DM) == "/apps/home/user/test.k"
        )

    def test_drive_letter_unmapped_drive(self):
        """Different drive letter (D:) not in mapping."""
        assert _resolve_remote_path(r"D:\data\file.k", DM) is None

    def test_drive_letter_case_insensitive(self):
        assert (
            _resolve_remote_path(r"s:\home\user\test.k", DM) == "/apps/home/user/test.k"
        )

    def test_drive_letter_root_only(self):
        r"""S:\ with nothing after drive letter."""
        assert _resolve_remote_path(r"S:\test.k", DM) == "/apps/test.k"

    def test_relative_cwd_on_mapped_linux_prefix(self):
        """Relative path when CWD is under a mapped Linux prefix."""
        with patch(
            "appform_sdk.job_submit.os.path.abspath",
            return_value="/apps/home/user/test.k",
        ):
            assert _resolve_remote_path("test.k", DM) == "/apps/home/user/test.k"

    def test_relative_not_mapped(self, monkeypatch):
        monkeypatch.chdir("/tmp")
        assert _resolve_remote_path("test.k", DM) is None

    def test_empty_path(self):
        assert _resolve_remote_path("", DM) is None

    def test_empty_mapping(self):
        assert _resolve_remote_path("/apps/test.k", {}) is None

    def test_absolute_linux_path_skips_abspath(self):
        r"""Absolute Linux path must NOT go through os.path.abspath()
        which on Windows would prepend a drive letter."""
        with patch(
            "appform_sdk.job_submit.os.path.abspath",
            return_value=r"S:\apps\home\user\test.k",
        ):
            assert (
                _resolve_remote_path("/apps/home/user/test.k", DM)
                == "/apps/home/user/test.k"
            )
            assert _resolve_remote_path("/tmp/test.k", DM) is None


# ── _apply_path_conversion ─────────────────────────────────────────────


class TestApplyPathConversion:
    def test_drive_letter_in_overrides(self):
        overrides = {"JH_CAS": r"S:\home\user\test.k"}
        result = _apply_path_conversion(overrides, DM)
        assert result["JH_CAS"] == "/apps/home/user/test.k"

    def test_comma_separated_multi_file(self):
        overrides = {"JH_CAS": r"S:\home\a.k, S:\home\b.k"}
        result = _apply_path_conversion(overrides, DM)
        # Note: spaces around commas are stripped by p.strip()
        assert result["JH_CAS"] == "/apps/home/a.k,/apps/home/b.k"

    def test_relative_path_cwd_on_windows_drive(self, monkeypatch):
        r"""Relative test.k when CWD is on a mapped Windows drive."""
        with patch(
            "appform_sdk.job_submit.os.getcwd", return_value=r"S:\home\p-user\dir"
        ), patch(
            "appform_sdk.job_submit.os.path.abspath",
            return_value=r"S:\home\p-user\dir\test.k",
        ):
            result = _apply_path_conversion({"JH_CAS": "test.k"}, DM)
        assert result["JH_CAS"] == "/apps/home/p-user/dir/test.k"

    def test_relative_path_cwd_not_mapped(self, tmp_path, monkeypatch):
        monkeypatch.chdir("/tmp")
        result = _apply_path_conversion({"JH_CAS": "test.k"}, DM)
        assert result["JH_CAS"] == "/tmp/test.k"

    def test_linux_absolute_path_unchanged(self):
        overrides = {"JH_CAS": "/apps/home/user/test.k"}
        result = _apply_path_conversion(overrides, DM)
        assert result["JH_CAS"] == "/apps/home/user/test.k"

    def test_non_upload_param_untouched(self):
        overrides = {"JH_QUEUE": "debug", "JH_CAS": r"S:\home\test.k"}
        result = _apply_path_conversion(overrides, DM)
        assert result["JH_QUEUE"] == "debug"
        assert result["JH_CAS"] == "/apps/home/test.k"

    def test_empty_mapping_passthrough(self):
        overrides = {"JH_CAS": r"S:\home\test.k"}
        result = _apply_path_conversion(overrides, {})
        assert result["JH_CAS"] == r"S:\home\test.k"

    def test_empty_value_ignored(self):
        overrides = {"JH_CAS": ""}
        result = _apply_path_conversion(overrides, DM)
        assert result["JH_CAS"] == ""


# ── _apply_uploaded_paths ───────────────────────────────────────────────


class TestApplyUploadedPaths:
    def test_basic_replacement(self):
        from appform_sdk.job_profiles import ParameterDef

        params = [ParameterDef(name="JH_CAS", param_type="upload")]
        path_mapping = {"/tmp/test.k": "/remote/1234/test.k"}
        overrides = {"JH_CAS": "/tmp/test.k"}
        result = _apply_uploaded_paths(overrides, params, path_mapping)
        assert result["JH_CAS"] == "/remote/1234/test.k"

    def test_comma_separated_replacement(self):
        from appform_sdk.job_profiles import ParameterDef

        params = [ParameterDef(name="JH_CAS", param_type="upload")]
        path_mapping = {
            "/tmp/a.k": "/remote/1234/a.k",
            "/tmp/b.k": "/remote/1234/b.k",
        }
        overrides = {"JH_CAS": "/tmp/a.k,/tmp/b.k"}
        result = _apply_uploaded_paths(overrides, params, path_mapping)
        assert result["JH_CAS"] == "/remote/1234/a.k,/remote/1234/b.k"

    def test_unmapped_path_kept(self):
        from appform_sdk.job_profiles import ParameterDef

        params = [ParameterDef(name="JH_CAS", param_type="upload")]
        path_mapping = {}
        overrides = {"JH_CAS": "/tmp/unknown.k"}
        result = _apply_uploaded_paths(overrides, params, path_mapping)
        assert result["JH_CAS"] == "/tmp/unknown.k"
