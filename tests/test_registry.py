"""
Tests for appform_sdk.registry — APIRegistry and EndpointDefinition.
"""

import pytest

from appform_sdk.registry import (
    APIRegistry,
    EndpointDefinition,
    get_registry,
    reset_registry,
)

# ── EndpointDefinition ───────────────────────────────────────────────────


class TestEndpointDefinition:
    def test_defaults(self):
        ep = EndpointDefinition(path="/api/test", method="GET", name="test")
        assert ep.path == "/api/test"
        assert ep.method == "GET"
        assert ep.name == "test"
        assert ep.description == ""
        assert ep.params == {}
        assert ep.headers == {}
        assert ep.deprecated is False
        assert ep.version_added == "1.0.0"
        assert ep.version_deprecated is None

    def test_full_init(self):
        ep = EndpointDefinition(
            path="/api/v2/test",
            method="POST",
            name="test.post",
            description="Test endpoint",
            params={"key": "value"},
            headers={"X-Custom": "1"},
            deprecated=True,
            version_added="2.0.0",
            version_deprecated="3.0.0",
        )
        assert ep.deprecated is True
        assert ep.version_added == "2.0.0"
        assert ep.version_deprecated == "3.0.0"


# ── APIRegistry ──────────────────────────────────────────────────────────


class TestAPIRegistry:
    def test_version_property(self):
        reg = APIRegistry(version="2.0.0")
        assert reg.version == "2.0.0"
        reg.version = "3.0.0"
        assert reg.version == "3.0.0"

    def test_register_and_get(self):
        reg = APIRegistry()
        reg.register("jobs.list", "/api/jobs", "GET", description="List jobs")
        ep = reg.get("jobs.list")
        assert ep is not None
        assert ep.path == "/api/jobs"
        assert ep.method == "GET"
        assert ep.description == "List jobs"

    def test_register_returns_self(self):
        reg = APIRegistry()
        result = reg.register("a", "/a")
        assert result is reg

    def test_register_duplicate_raises(self):
        reg = APIRegistry()
        reg.register("dup", "/a")
        with pytest.raises(ValueError, match="already exists"):
            reg.register("dup", "/b")

    def test_register_override(self):
        reg = APIRegistry()
        reg.register("ep", "/old")
        reg.register("ep", "/new", override=True)
        assert reg.get("ep").path == "/new"

    def test_register_method_uppercase(self):
        reg = APIRegistry()
        reg.register("ep", "/api", method="post")
        assert reg.get("ep").method == "POST"

    def test_unregister(self):
        reg = APIRegistry()
        reg.register("ep", "/api")
        assert reg.unregister("ep") is True
        assert reg.get("ep") is None

    def test_unregister_not_found(self):
        reg = APIRegistry()
        assert reg.unregister("nonexistent") is False

    def test_get_not_found(self):
        reg = APIRegistry()
        assert reg.get("nope") is None

    def test_get_all_returns_copy(self):
        reg = APIRegistry()
        reg.register("a", "/a")
        all_eps = reg.get_all()
        all_eps["b"] = EndpointDefinition(path="/b", method="GET", name="b")
        assert reg.get("b") is None  # original not modified

    def test_get_for_version(self):
        reg = APIRegistry(version="2.0.0")
        reg.register("old", "/old", version_added="1.0.0")
        reg.register("current", "/cur", version_added="2.0.0")
        reg.register("future", "/fut", version_added="3.0.0")
        eps = reg.get_for_version("2.0.0")
        assert "old" in eps
        assert "current" in eps
        assert "future" not in eps

    def test_get_for_version_deprecated(self):
        reg = APIRegistry(version="2.0.0")
        reg.register(
            "deprecated", "/dep", version_added="1.0.0", version_deprecated="2.0.0"
        )
        eps = reg.get_for_version("2.0.0")
        assert "deprecated" not in eps

    def test_get_for_version_deprecated_future(self):
        reg = APIRegistry(version="2.0.0")
        reg.register("soon", "/soon", version_added="1.0.0", version_deprecated="3.0.0")
        eps = reg.get_for_version("2.0.0")
        assert "soon" in eps  # not yet deprecated

    def test_compare_versions(self):
        from appform_sdk.registry import _compare_versions

        assert _compare_versions("1.0", "1.0") == 0
        assert _compare_versions("1.0", "2.0") == -1
        assert _compare_versions("2.0", "1.0") == 1
        assert _compare_versions("1.0.0", "1.0") == 1  # longer
        assert _compare_versions("1.0", "1.0.0") == -1  # shorter

    def test_register_handler(self):
        reg = APIRegistry()

        def handler():
            return "result"

        reg.register_handler("custom", handler)
        assert reg.get_handler("custom") is handler

    def test_get_handler_not_found(self):
        reg = APIRegistry()
        assert reg.get_handler("nope") is None

    def test_add_extension(self):
        reg = APIRegistry()
        reg.add_extension("ext1").add_extension("ext2")
        assert reg.get_extensions() == ["ext1", "ext2"]

    def test_add_extension_no_duplicates(self):
        reg = APIRegistry()
        reg.add_extension("ext1").add_extension("ext1")
        assert reg.get_extensions() == ["ext1"]

    def test_get_extensions_returns_copy(self):
        reg = APIRegistry()
        reg.add_extension("ext1")
        exts = reg.get_extensions()
        exts.append("ext2")
        assert reg.get_extensions() == ["ext1"]

    def test_load_from_dict(self):
        reg = APIRegistry()
        config = {
            "jobs.list": {"path": "/api/jobs", "method": "GET"},
            "jobs.submit": {
                "path": "/api/jobs",
                "method": "POST",
                "description": "Submit a job",
            },
        }
        reg.load_from_dict(config)
        assert reg.get("jobs.list").path == "/api/jobs"
        assert reg.get("jobs.submit").method == "POST"

    def test_load_from_dict_override(self):
        reg = APIRegistry()
        reg.register("old", "/old")
        config = {"old": {"path": "/new"}}
        reg.load_from_dict(config, override=True)
        assert reg.get("old").path == "/new"

    def test_to_dict(self):
        reg = APIRegistry()
        reg.register("ep", "/api", "GET", description="test")
        d = reg.to_dict()
        assert "ep" in d
        assert d["ep"]["path"] == "/api"
        assert d["ep"]["method"] == "GET"
        assert d["ep"]["description"] == "test"
        assert "deprecated" in d["ep"]

    def test_chaining(self):
        reg = APIRegistry()
        result = (
            reg.register("a", "/a")
            .register("b", "/b")
            .register_handler("a", lambda: None)
            .add_extension("ext")
        )
        assert result is reg
        assert len(reg.get_all()) == 2


# ── Global registry ──────────────────────────────────────────────────────


class TestGlobalRegistry:
    def setup_method(self):
        reset_registry()

    def teardown_method(self):
        reset_registry()

    def test_get_registry_creates(self):
        reg = get_registry("2.0.0")
        assert isinstance(reg, APIRegistry)
        assert reg.version == "2.0.0"

    def test_get_registry_singleton(self):
        reg1 = get_registry()
        reg2 = get_registry()
        assert reg1 is reg2

    def test_reset_registry(self):
        reg1 = get_registry()
        reset_registry()
        reg2 = get_registry()
        assert reg1 is not reg2
