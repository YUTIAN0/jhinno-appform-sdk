"""
Tests for job profile management
"""

import os
import tempfile
from unittest.mock import MagicMock

import pytest

from appform_sdk.job_profiles import (
    AppProfile,
    JobProfileManager,
    ParameterDef,
)


class TestParameterDef:
    def test_basic_creation(self):
        p = ParameterDef(name="cores", param_type="text", default="1")
        assert p.name == "cores"
        assert p.param_type == "text"
        assert p.required is False
        assert p.default == "1"

    def test_effective_cli_name_from_cli_arg(self):
        p = ParameterDef(name="JH_CORES", cli_arg="core-count")
        assert p.effective_cli_name == "core-count"

    def test_effective_cli_name_derived(self):
        p = ParameterDef(name="JH_CORES")
        assert p.effective_cli_name == "cores"

    def test_effective_cli_name_no_prefix(self):
        p = ParameterDef(name="input_file")
        assert p.effective_cli_name == "input-file"

    def test_validate_valid_value(self):
        p = ParameterDef(name="num", validation=r"^\d+$")
        assert p.validate("123") is True
        assert p.validate("abc") is False

    def test_validate_required_empty(self):
        p = ParameterDef(name="req", required=True)
        assert p.validate("") is False
        assert p.validate(None) is False
        assert p.validate("value") is True

    def test_validate_optional_empty(self):
        p = ParameterDef(name="opt", required=False)
        assert p.validate("") is True
        assert p.validate(None) is True

    def test_to_dict(self):
        p = ParameterDef(
            name="JH_CORES",
            param_type="text",
            required=True,
            default="1",
            description="Number of cores",
            validation=r"^\d+$",
            cli_arg="cores",
            short_arg="c",
        )
        d = p.to_dict()
        assert d["name"] == "JH_CORES"
        assert d["type"] == "text"
        assert d["required"] is True
        assert d["default"] == "1"
        assert d["description"] == "Number of cores"
        assert d["validation"] == r"^\d+$"
        assert d["cli_arg"] == "cores"
        assert d["short_arg"] == "c"


class TestAppProfile:
    def _make_profile(self):
        p = AppProfile(app_id="test_app", name="Test App")
        p.parameters.append(
            ParameterDef(
                name="JH_CORES",
                param_type="text",
                required=True,
                default="1",
                cli_arg="cores",
            )
        )
        p.parameters.append(
            ParameterDef(
                name="JH_INPUT", param_type="text", required=False, cli_arg="input"
            )
        )
        p.parameters.append(
            ParameterDef(name="JH_SCRIPT", param_type="upload", cli_arg="script")
        )
        return p

    def test_get_required_params(self):
        p = self._make_profile()
        req = p.get_required_params()
        assert len(req) == 1
        assert req[0].name == "JH_CORES"

    def test_get_optional_params(self):
        p = self._make_profile()
        opt = p.get_optional_params()
        assert len(opt) == 2

    def test_get_upload_params(self):
        p = self._make_profile()
        ups = p.get_upload_params()
        assert len(ups) == 1
        assert ups[0].name == "JH_SCRIPT"

    def test_get_param(self):
        p = self._make_profile()
        assert p.get_param("JH_CORES") is not None
        assert p.get_param("NONEXIST") is None

    def test_get_param_by_cli(self):
        p = self._make_profile()
        assert p.get_param_by_cli("cores") is not None
        assert p.get_param_by_cli("nonexist") is None

    def test_get_param_by_short_arg(self):
        p = AppProfile(app_id="x")
        p.parameters.append(ParameterDef(name="JH_A", short_arg="a"))
        assert p.get_param_by_cli("a") is not None

    def test_resolve_cli_args(self):
        p = self._make_profile()
        result = p.resolve_cli_args({"cores": "4", "input": "/path/in"})
        assert result["JH_CORES"] == "4"
        assert result["JH_INPUT"] == "/path/in"

    def test_resolve_cli_args_passthrough(self):
        p = self._make_profile()
        result = p.resolve_cli_args({"JH_CORES": "8"})
        assert result["JH_CORES"] == "8"

    def test_validate_params_ok(self):
        p = self._make_profile()
        errors = p.validate_params({"JH_CORES": "4", "JH_INPUT": "file.txt"})
        assert errors == []

    def test_validate_params_missing_required(self):
        p = AppProfile(app_id="x")
        p.parameters.append(ParameterDef(name="NO_DEFAULT", required=True))
        errors = p.validate_params({})
        assert len(errors) == 1
        assert "NO_DEFAULT" in errors[0]

    def test_validate_params_default_satisfies_required(self):
        p = self._make_profile()
        # JH_CORES has default="1" so missing value is OK
        errors = p.validate_params({"JH_CORES": "1"})
        assert errors == []

    def test_validate_params_invalid_value(self):
        p = AppProfile(app_id="x")
        p.parameters.append(
            ParameterDef(name="NUM", required=True, validation=r"^\d+$")
        )
        errors = p.validate_params({"NUM": "abc"})
        assert len(errors) == 1
        assert "does not match pattern" in errors[0]

    def test_build_params_defaults(self):
        p = AppProfile(app_id="x")
        p.parameters.append(ParameterDef(name="A", required=True, default="1"))
        p.parameters.append(ParameterDef(name="B", required=False, default="hello"))
        result = p.build_params()
        assert result == {"A": "1", "B": "hello"}

    def test_build_params_override(self):
        p = AppProfile(app_id="x")
        p.parameters.append(ParameterDef(name="A", required=True, default="1"))
        result = p.build_params(overrides={"A": "10"})
        assert result["A"] == "10"

    def test_build_params_missing_required_raises(self):
        p = AppProfile(app_id="x")
        p.parameters.append(ParameterDef(name="REQ", required=True))
        with pytest.raises(ValueError, match="Required parameter missing"):
            p.build_params()

    def test_build_params_switch_off_skipped(self):
        p = AppProfile(app_id="x")
        p.parameters.append(ParameterDef(name="SW", param_type="switch", default="off"))
        result = p.build_params()
        assert "SW" not in result

    def test_to_dict(self):
        p = AppProfile(app_id="test", name="Test", description="Desc")
        p.parameters.append(ParameterDef(name="A"))
        d = p.to_dict()
        assert d["app_id"] == "test"
        assert d["name"] == "Test"
        assert len(d["parameters"]) == 1


YAML_CONFIG = """\
job_submit_config:
  applications:
    my_app:
      name: "My Application"
      description: "Test app"
      parameters:
        - name: JH_CORES
          type: text
          required: true
          default: "1"
          cli_arg: cores
          description: "Number of cores"
        - name: JH_INPUT
          type: text
          required: false
          cli_arg: input
          description: "Input file"
        - name: JH_SCRIPT
          type: upload
          cli_arg: script
          description: "Script file"
        - name: JH_SWITCH
          type: switch
          default: "off"
"""


class TestJobProfileManager:
    def _make_config_file(self, content=None):
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        )
        f.write(content or YAML_CONFIG)
        f.close()
        return f.name

    def test_load_config(self):
        path = self._make_config_file()
        try:
            mgr = JobProfileManager(config_file=path)
            assert mgr.get_profile("my_app") is not None
            assert mgr.get_profile("my_app").name == "My Application"
        finally:
            os.unlink(path)

    def test_list_apps(self):
        path = self._make_config_file()
        try:
            mgr = JobProfileManager(config_file=path)
            apps = mgr.list_apps()
            assert len(apps) == 1
            assert apps[0]["app_id"] == "my_app"
            assert apps[0]["name"] == "My Application"
        finally:
            os.unlink(path)

    def test_build_submit_params(self):
        path = self._make_config_file()
        try:
            mgr = JobProfileManager(config_file=path)
            params = mgr.build_submit_params("my_app", overrides={"JH_CORES": "8"})
            assert params["JH_CORES"] == "8"
            assert "JH_SWITCH" not in params  # switch off skipped
        finally:
            os.unlink(path)

    def test_build_submit_params_validation_error(self):
        config = """\
job_submit_config:
  applications:
    strict:
      parameters:
        - name: NUM
          type: text
          required: true
          validation: '^[0-9]+$'
"""
        path = self._make_config_file(config)
        try:
            mgr = JobProfileManager(config_file=path)
            with pytest.raises(ValueError, match="does not match pattern"):
                mgr.build_submit_params("strict", overrides={"NUM": "abc"})
        finally:
            os.unlink(path)

    def test_build_submit_unknown_app(self):
        path = self._make_config_file()
        try:
            mgr = JobProfileManager(config_file=path)
            with pytest.raises(ValueError, match="Unknown application"):
                mgr.build_submit_params("nonexistent")
        finally:
            os.unlink(path)

    def test_config_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            JobProfileManager(config_file="/nonexistent/config.yaml")

    def test_submit_job(self):
        path = self._make_config_file()
        try:
            mgr = JobProfileManager(config_file=path)
            mock_client = MagicMock()
            mock_client.jobs.submit.return_value = {"data": {"jobId": "123"}}
            result = mgr.submit_job(mock_client, "my_app")
            assert result == {"data": {"jobId": "123"}}
            mock_client.jobs.submit.assert_called_once()
            call_kwargs = mock_client.jobs.submit.call_args
            assert call_kwargs.kwargs["app_id"] == "my_app"
            assert call_kwargs.kwargs["params"]["JH_CORES"] == "1"
        finally:
            os.unlink(path)

    def test_auto_load_from_env(self, monkeypatch):
        path = self._make_config_file()
        try:
            monkeypatch.setenv("JOB_SUBMIT_CONFIG", path)
            mgr = JobProfileManager()
            assert mgr.get_profile("my_app") is not None
        finally:
            os.unlink(path)
            monkeypatch.delenv("JOB_SUBMIT_CONFIG", raising=False)
