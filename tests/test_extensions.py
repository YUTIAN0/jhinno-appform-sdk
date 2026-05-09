"""
Tests for extensions system
"""

import json
from unittest.mock import MagicMock

import pytest

from appform_sdk.extensions import (
    DEFAULT_ENDPOINTS,
    ENDPOINTS_6_5,
    ENDPOINTS_6_6,
    DynamicAPI,
    Extension,
    ExtensionConfig,
    ExtensionManager,
    _compare_versions,
    create_version_specific_registry,
    init_default_registry,
)
from appform_sdk.registry import APIRegistry


class TestCompareVersions:
    def test_equal_versions(self):
        assert _compare_versions("6.0", "6.0") == 0
        assert _compare_versions("6.5", "6.5") == 0

    def test_less_than(self):
        assert _compare_versions("6.0", "6.5") == -1
        assert _compare_versions("6.3", "6.6") == -1
        assert _compare_versions("6.0", "7.0") == -1

    def test_greater_than(self):
        assert _compare_versions("6.5", "6.0") == 1
        assert _compare_versions("7.0", "6.0") == 1

    def test_three_part_versions(self):
        assert _compare_versions("6.0.1", "6.0.2") == -1
        assert _compare_versions("6.0.2", "6.0.1") == 1

    def test_different_lengths(self):
        assert _compare_versions("6.0", "6.0.1") == -1
        assert _compare_versions("6.0.1", "6.0") == 1


class TestInitDefaultRegistry:
    def test_base_endpoints_loaded(self):
        reg = init_default_registry("6.0")
        ep = reg.get("auth.login")
        assert ep is not None
        assert ep.path == "/appform/ws/api/auth/login"

    def test_65_includes_65_endpoints(self):
        reg = init_default_registry("6.5")
        assert reg.get("files.getConfidentiality") is not None
        assert reg.get("files.setConfidentiality") is not None
        # Also includes base endpoints
        assert reg.get("auth.login") is not None

    def test_66_includes_all(self):
        reg = init_default_registry("6.6")
        assert reg.get("files.getConfidentiality") is not None
        assert reg.get("jobs.getForm") is not None
        assert reg.get("sessions.startV2") is not None
        assert reg.get("apps.listV2") is not None
        assert reg.get("quota.storage") is not None

    def test_63_no_65_endpoints(self):
        reg = init_default_registry("6.3")
        assert reg.get("files.getConfidentiality") is None
        assert reg.get("jobs.getForm") is None


class TestCreateVersionSpecificRegistry:
    def test_custom_endpoints(self):
        endpoints = {
            "custom.hello": {
                "path": "/api/hello",
                "method": "GET",
                "description": "Say hello",
            }
        }
        reg = create_version_specific_registry("7.0", endpoints)
        ep = reg.get("custom.hello")
        assert ep is not None
        assert ep.method == "GET"
        assert ep.path == "/api/hello"


class TestExtensionConfig:
    def test_defaults(self):
        cfg = ExtensionConfig(name="test", version="1.0")
        assert cfg.endpoints == {}
        assert cfg.overrides == {}
        assert cfg.requires == []

    def test_custom_values(self):
        cfg = ExtensionConfig(
            name="my_ext",
            version="2.0",
            endpoints={"ep1": {"path": "/a"}},
            overrides={"ep2": {"path": "/b"}},
            requires=["other_ext"],
        )
        assert cfg.name == "my_ext"
        assert "ep1" in cfg.endpoints
        assert "ep2" in cfg.overrides
        assert "other_ext" in cfg.requires


class TestExtension:
    def test_register_endpoints(self):
        cfg = ExtensionConfig(
            name="test_ext",
            version="1.0",
            endpoints={"test.echo": {"path": "/echo", "method": "POST"}},
        )
        ext = Extension(cfg)
        reg = APIRegistry("6.5")
        ext.register(reg)
        assert reg.get("test.echo") is not None
        assert reg.get("test.echo").method == "POST"

    def test_register_overrides(self):
        reg = APIRegistry("6.5")
        reg.register(name="auth.ping", path="/old/ping", method="GET")

        cfg = ExtensionConfig(
            name="override_ext",
            version="1.0",
            overrides={"auth.ping": {"path": "/new/ping", "method": "POST"}},
        )
        ext = Extension(cfg)
        ext.register(reg)
        ep = reg.get("auth.ping")
        assert ep.path == "/new/ping"
        assert ep.method == "POST"

    def test_register_idempotent(self):
        cfg = ExtensionConfig(
            name="idem_ext",
            version="1.0",
            endpoints={"x.get": {"path": "/x"}},
        )
        ext = Extension(cfg)
        reg = APIRegistry("6.5")
        ext.register(reg)
        ext.register(reg)  # second time should be no-op
        # Extension name should appear once
        assert reg.get_extensions().count("idem_ext") == 1

    def test_unregister(self):
        cfg = ExtensionConfig(
            name="rem_ext",
            version="1.0",
            endpoints={"rem.test": {"path": "/rem"}},
        )
        ext = Extension(cfg)
        reg = APIRegistry("6.5")
        ext.register(reg)
        ext.unregister(reg)
        assert reg.get("rem.test") is None


class TestExtensionManager:
    def _make_manager(self):
        reg = APIRegistry("6.5")
        return ExtensionManager(registry=reg)

    def test_register_and_list(self):
        mgr = self._make_manager()
        cfg = ExtensionConfig(
            name="list_test",
            version="1.0",
            endpoints={"lt.get": {"path": "/lt"}},
        )
        ext = Extension(cfg)
        mgr.register(ext)
        assert "list_test" in mgr.list_extensions()

    def test_duplicate_registration_raises(self):
        mgr = self._make_manager()
        cfg = ExtensionConfig(name="dup", version="1.0")
        ext1 = Extension(cfg)
        ext2 = Extension(cfg)
        mgr.register(ext1)
        with pytest.raises(ValueError, match="already registered"):
            mgr.register(ext2)

    def test_dependency_check(self):
        mgr = self._make_manager()
        cfg_parent = ExtensionConfig(name="parent", version="1.0")
        cfg_child = ExtensionConfig(name="child", version="1.0", requires=["parent"])
        mgr.register(Extension(cfg_parent))
        mgr.register(Extension(cfg_child))
        assert "child" in mgr.list_extensions()

    def test_missing_dependency_raises(self):
        mgr = self._make_manager()
        cfg = ExtensionConfig(name="orphan", version="1.0", requires=["missing"])
        with pytest.raises(ValueError, match="requires"):
            mgr.register(Extension(cfg))

    def test_unregister(self):
        mgr = self._make_manager()
        cfg = ExtensionConfig(
            name="unreg",
            version="1.0",
            endpoints={"un.x": {"path": "/u"}},
        )
        mgr.register(Extension(cfg))
        assert mgr.unregister("unreg") is True
        assert "unreg" not in mgr.list_extensions()

    def test_unregister_nonexistent(self):
        mgr = self._make_manager()
        assert mgr.unregister("nope") is False

    def test_get_extension(self):
        mgr = self._make_manager()
        cfg = ExtensionConfig(name="get_me", version="1.0")
        ext = Extension(cfg)
        mgr.register(ext)
        assert mgr.get("get_me") is ext
        assert mgr.get("missing") is None

    def test_load_from_dict(self, tmp_path):
        mgr = self._make_manager()
        cfg_dict = {
            "name": "dict_ext",
            "version": "1.0",
            "endpoints": {"dict.get": {"path": "/dict", "method": "GET"}},
        }
        mgr.load_from_dict(cfg_dict)
        assert "dict_ext" in mgr.list_extensions()
        assert mgr.registry.get("dict.get") is not None

    def test_load_from_file(self, tmp_path):
        mgr = self._make_manager()
        file_data = {
            "name": "file_ext",
            "version": "2.0",
            "endpoints": {"file.get": {"path": "/file"}},
        }
        fpath = tmp_path / "ext.json"
        fpath.write_text(json.dumps(file_data))

        ext = mgr.load_from_file(str(fpath))
        assert isinstance(ext, Extension)
        assert "file_ext" in mgr.list_extensions()

    def test_load_from_file_not_found(self):
        mgr = self._make_manager()
        with pytest.raises(FileNotFoundError):
            mgr.load_from_file("/nonexistent/ext.json")


class TestDynamicAPI:
    def _make_api(self, endpoints=None):
        reg = APIRegistry("6.5")
        if endpoints:
            for name, cfg in endpoints.items():
                reg.register(
                    name=name,
                    path=cfg.get("path", ""),
                    method=cfg.get("method", "GET"),
                    params=cfg.get("params"),
                    headers=cfg.get("headers"),
                )
        client = MagicMock()
        client.request = MagicMock(return_value={"data": "ok"})
        return DynamicAPI(client, reg), client

    def test_call_by_name(self):
        endpoints = {"my.echo": {"path": "/echo", "method": "POST"}}
        api, client = self._make_api(endpoints)
        api.call("my.echo")
        client.request.assert_called_once()
        call_kwargs = client.request.call_args
        assert call_kwargs.kwargs["method"] == "POST"
        assert call_kwargs.kwargs["path"] == "/echo"

    def test_call_unknown_endpoint(self):
        api, _ = self._make_api()
        with pytest.raises(ValueError, match="not found"):
            api.call("unknown.endpoint")

    def test_path_params(self):
        endpoints = {"job.get": {"path": "/jobs/{id}", "method": "GET"}}
        api, client = self._make_api(endpoints)
        api.call("job.get", path_params={"id": "42"})
        call_kwargs = client.request.call_args
        assert call_kwargs.kwargs["path"] == "/jobs/42"

    def test_param_merging(self):
        endpoints = {
            "x.list": {"path": "/x", "method": "GET", "params": {"default_p": "1"}}
        }
        api, client = self._make_api(endpoints)
        api.call("x.list", params={"override": "2"})
        call_kwargs = client.request.call_args
        assert call_kwargs.kwargs["params"]["default_p"] == "1"
        assert call_kwargs.kwargs["params"]["override"] == "2"

    def test_header_merging(self):
        endpoints = {
            "x.get": {"path": "/x", "method": "GET", "headers": {"X-Custom": "a"}}
        }
        api, client = self._make_api(endpoints)
        api.call("x.get", headers={"X-Extra": "b"})
        call_kwargs = client.request.call_args
        assert call_kwargs.kwargs["headers"]["X-Custom"] == "a"
        assert call_kwargs.kwargs["headers"]["X-Extra"] == "b"

    def test_getattr_exact_match(self):
        endpoints = {"a": {"path": "/a", "method": "GET"}}
        api, client = self._make_api(endpoints)
        api.a()
        client.request.assert_called_once()

    def test_getattr_underscore_to_dot(self):
        endpoints = {"a.get": {"path": "/a", "method": "GET"}}
        api, client = self._make_api(endpoints)
        api.a_get()
        client.request.assert_called_once()

    def test_getattr_missing_raises(self):
        api, _ = self._make_api()
        with pytest.raises(AttributeError, match="No endpoint"):
            api.missing_endpoint()

    def test_custom_handler(self):
        reg = APIRegistry("6.5")
        reg.register(name="x.hello", path="/hello", method="GET")
        handler_called = []

        def handler(client, **kw):
            handler_called.append(True)
            return {"custom": True}

        reg.register_handler("x.hello", handler)
        client = MagicMock()
        api = DynamicAPI(client, reg)
        result = api.call("x.hello")
        assert result == {"custom": True}
        assert handler_called
        client.request.assert_not_called()


class TestDefaultEndpoints:
    def test_default_endpoints_not_empty(self):
        assert len(DEFAULT_ENDPOINTS) > 20

    def test_required_categories_exist(self):
        names = list(DEFAULT_ENDPOINTS.keys())
        name_str = ".".join(names)
        assert "auth.login" in name_str
        assert "jobs.submit" in name_str
        assert "sessions.start" in name_str
        assert "files.list" in name_str

    def test_65_endpoints(self):
        assert "files.getConfidentiality" in ENDPOINTS_6_5
        assert "files.setConfidentiality" in ENDPOINTS_6_5

    def test_66_endpoints(self):
        assert "jobs.getForm" in ENDPOINTS_6_6
        assert "sessions.startV2" in ENDPOINTS_6_6
        assert "apps.listV2" in ENDPOINTS_6_6
