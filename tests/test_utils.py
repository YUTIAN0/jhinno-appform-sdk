"""
Tests for appform_sdk.utils utility functions:
check_cluster_environment, build_filter_condition, build_filter_group.

Note: SignatureGenerator and AESEncryptor are tested in test_sdk.py.
"""

from unittest.mock import MagicMock, patch


from appform_sdk.utils import (
    build_filter_condition,
    build_filter_group,
    check_cluster_environment,
)

# ── build_filter_condition ───────────────────────────────────────────────


class TestBuildFilterCondition:
    def test_basic(self):
        result = build_filter_condition("status", "eq", "RUN")
        assert result == {
            "type": "string",
            "operator": "eq",
            "ignoreCase": True,
            "field": "status",
            "value": "RUN",
        }

    def test_custom_type(self):
        result = build_filter_condition("slots", "gt", "8", field_type="number")
        assert result["type"] == "number"
        assert result["operator"] == "gt"

    def test_ignore_case_false(self):
        result = build_filter_condition("name", "contains", "test", ignore_case=False)
        assert result["ignoreCase"] is False

    def test_contains_operator(self):
        result = build_filter_condition("name", "contains", "sim")
        assert result["operator"] == "contains"


# ── build_filter_group ───────────────────────────────────────────────────


class TestBuildFilterGroup:
    def test_and_logic(self):
        f1 = build_filter_condition("status", "eq", "RUN")
        f2 = build_filter_condition("owner", "eq", "alice")
        result = build_filter_group([f1, f2], logic="and")
        assert result["logic"] == "and"
        assert len(result["filters"]) == 2

    def test_or_logic(self):
        f1 = build_filter_condition("status", "eq", "RUN")
        f2 = build_filter_condition("status", "eq", "PEND")
        result = build_filter_group([f1, f2], logic="or")
        assert result["logic"] == "or"

    def test_default_logic(self):
        result = build_filter_group([])
        assert result["logic"] == "and"

    def test_nested_groups(self):
        f1 = build_filter_condition("a", "eq", "1")
        f2 = build_filter_condition("b", "eq", "2")
        inner = build_filter_group([f1, f2], logic="or")
        f3 = build_filter_condition("c", "eq", "3")
        outer = build_filter_group([inner, f3])
        assert len(outer["filters"]) == 2
        assert outer["filters"][0]["logic"] == "or"


# ── check_cluster_environment ────────────────────────────────────────────


class TestCheckClusterEnvironment:
    def test_jversion_not_found(self):
        with patch("appform_sdk.utils.subprocess.run", side_effect=FileNotFoundError):
            result = check_cluster_environment()
        assert result["in_cluster"] is False
        assert result["error"] == "jversion command not found"

    def test_jversion_fails(self):
        proc = MagicMock(returncode=1)
        with patch("appform_sdk.utils.subprocess.run", return_value=proc):
            result = check_cluster_environment()
        assert result["in_cluster"] is False
        assert result["error"] == "jversion command failed"

    def test_jversion_ok_jhosts_not_found(self):
        jversion_proc = MagicMock(returncode=0)
        jversion_proc.stdout = b"JHPC 6.5.0"

        def side_effect(cmd, **kwargs):
            if cmd[0] == "jversion":
                return jversion_proc
            raise FileNotFoundError

        with patch("appform_sdk.utils.subprocess.run", side_effect=side_effect), patch(
            "socket.gethostname", return_value="node01"
        ):
            result = check_cluster_environment()
        assert result["in_cluster"] is False
        assert result["jversion"] == "JHPC 6.5.0"
        assert result["hostname"] == "node01"
        assert result["error"] == "jhosts command not found"

    def test_host_found_in_jhosts(self):
        jversion_proc = MagicMock(returncode=0)
        jversion_proc.stdout = b"JHPC 6.5.0"
        jhosts_proc = MagicMock(returncode=0)
        jhosts_proc.stdout = b"HOSTNAME  STATUS\nnode01    ok\nnode02    ok"

        def side_effect(cmd, **kwargs):
            if cmd[0] == "jversion":
                return jversion_proc
            if cmd[0] == "jhosts":
                return jhosts_proc

        with patch("appform_sdk.utils.subprocess.run", side_effect=side_effect), patch(
            "socket.gethostname", return_value="node01"
        ):
            result = check_cluster_environment()
        assert result["in_cluster"] is True
        assert result["jversion"] == "JHPC 6.5.0"
        assert result["hostname"] == "node01"
        assert result["host_status"] == "ok"

    def test_host_not_found_in_jhosts(self):
        jversion_proc = MagicMock(returncode=0)
        jversion_proc.stdout = b"JHPC 6.5.0"
        jhosts_proc = MagicMock(returncode=0)
        jhosts_proc.stdout = b"HOSTNAME  STATUS\nnode02    ok"

        def side_effect(cmd, **kwargs):
            if cmd[0] == "jversion":
                return jversion_proc
            if cmd[0] == "jhosts":
                return jhosts_proc

        with patch("appform_sdk.utils.subprocess.run", side_effect=side_effect), patch(
            "socket.gethostname", return_value="node01"
        ):
            result = check_cluster_environment()
        assert result["in_cluster"] is False
        assert "not found" in result["error"]

    def test_jhosts_fails(self):
        jversion_proc = MagicMock(returncode=0)
        jversion_proc.stdout = b"JHPC 6.5.0"
        jhosts_proc = MagicMock(returncode=1)

        def side_effect(cmd, **kwargs):
            if cmd[0] == "jversion":
                return jversion_proc
            if cmd[0] == "jhosts":
                return jhosts_proc

        with patch("appform_sdk.utils.subprocess.run", side_effect=side_effect), patch(
            "socket.gethostname", return_value="node01"
        ):
            result = check_cluster_environment()
        assert result["in_cluster"] is False
        assert result["error"] == "jhosts -w command failed"

    def test_jversion_exception(self):
        with patch(
            "appform_sdk.utils.subprocess.run",
            side_effect=RuntimeError("unexpected"),
        ):
            result = check_cluster_environment()
        assert result["in_cluster"] is False
        assert "jversion error" in result["error"]
