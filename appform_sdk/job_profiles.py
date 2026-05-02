"""
Job profile management for Appform SDK.

Loads application parameter definitions from YAML configuration files
(like job_submit.yaml), validates parameters, and builds job submission
payloads compatible with the Appform API.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


DEFAULT_CONFIG_FILES = [
    "job_submit.yaml",
    os.path.expanduser("~/.appform/job_submit.yaml"),
    "/apps/software/script/job_submit.yaml",
]


class ParameterDef:
    """Definition of a single application parameter."""

    def __init__(
        self,
        name: str,
        param_type: str = "text",
        required: bool = False,
        default: Optional[str] = None,
        description: str = "",
        validation: Optional[str] = None,
        cli_arg: Optional[str] = None,
        short_arg: Optional[str] = None,
    ):
        self.name = name
        self.param_type = param_type
        self.required = required
        self.default = default
        self.description = description
        self.validation = validation
        self.cli_arg = cli_arg
        self.short_arg = short_arg

    @property
    def effective_cli_name(self) -> str:
        """Get the CLI argument name: cli_arg if set, else auto-derived from param name."""
        if self.cli_arg:
            return self.cli_arg
        return self.name.lower().replace("jh_", "").replace("_", "-")

    def validate(self, value: str) -> bool:
        if value is None or value == "":
            return not self.required
        if self.validation:
            return bool(re.match(self.validation, str(value)))
        return True

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "name": self.name,
            "type": self.param_type,
            "required": self.required,
            "default": self.default,
            "description": self.description,
            "validation": self.validation,
        }
        if self.cli_arg:
            d["cli_arg"] = self.cli_arg
        if self.short_arg:
            d["short_arg"] = self.short_arg
        return d


class AppProfile:
    """Profile for a single application, defining its parameters."""

    def __init__(self, app_id: str, name: str = "", description: str = ""):
        self.app_id = app_id
        self.name = name
        self.description = description
        self.parameters: List[ParameterDef] = []

    def get_required_params(self) -> List[ParameterDef]:
        return [p for p in self.parameters if p.required]

    def get_optional_params(self) -> List[ParameterDef]:
        return [p for p in self.parameters if not p.required]

    def get_upload_params(self) -> List[ParameterDef]:
        return [p for p in self.parameters if p.param_type == "upload"]

    def get_param(self, name: str) -> Optional[ParameterDef]:
        for p in self.parameters:
            if p.name == name:
                return p
        return None

    def get_param_by_cli(self, cli_name: str) -> Optional[ParameterDef]:
        """Find parameter by CLI name (cli_arg or short_arg)."""
        for p in self.parameters:
            if p.cli_arg == cli_name or p.short_arg == cli_name:
                return p
            if (
                not p.cli_arg
                and p.name.lower().replace("jh_", "").replace("_", "-") == cli_name
            ):
                return p
        return None

    def resolve_cli_args(self, cli_overrides: Dict[str, str]) -> Dict[str, str]:
        """
        Convert CLI argument names (cli_arg/short_arg) back to JH_* parameter names.

        Args:
            cli_overrides: Dict of cli_name -> value

        Returns:
            Dict of JH_* param_name -> value
        """
        result = {}
        for cli_name, value in cli_overrides.items():
            param = self.get_param_by_cli(cli_name)
            if param:
                result[param.name] = value
            else:
                # Pass through as-is (might be a direct JH_* name)
                result[cli_name] = value
        return result

    def validate_params(self, params: Dict[str, str]) -> List[str]:
        errors = []
        for param_def in self.parameters:
            value = params.get(param_def.name)
            if param_def.required and (value is None or value == ""):
                if param_def.default:
                    continue
                errors.append(
                    f"Required parameter missing: {param_def.name} ({param_def.description})"
                )
            elif value is not None and value != "":
                if not param_def.validate(value):
                    errors.append(
                        f"Parameter {param_def.name}='{value}' does not match pattern '{param_def.validation}'"
                    )
        return errors

    def build_params(
        self, overrides: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        result = {}
        overrides = overrides or {}

        for param_def in self.parameters:
            if param_def.name in overrides:
                value = overrides[param_def.name]
                if value is not None and value != "":
                    result[param_def.name] = str(value)
            elif param_def.default is not None and param_def.default != "":
                if param_def.param_type == "switch" and param_def.default == "off":
                    continue
                result[param_def.name] = str(param_def.default)
            elif param_def.required:
                raise ValueError(
                    f"Required parameter missing: {param_def.name} ({param_def.description})"
                )

        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "app_id": self.app_id,
            "name": self.name,
            "description": self.description,
            "parameters": [p.to_dict() for p in self.parameters],
        }


class JobProfileManager:
    """
    Manages job submission profiles loaded from YAML configuration files.

    Supports the same config format as job_submit.py.
    """

    def __init__(self, config_file: Optional[str] = None):
        self._config_file: Optional[str] = None
        self._profiles: Dict[str, AppProfile] = {}

        if config_file:
            self.load(config_file)
        else:
            self._auto_load()

    def _auto_load(self):
        env_config = os.getenv("JOB_SUBMIT_CONFIG")
        if env_config and os.path.isfile(env_config):
            self.load(env_config)
            return

        for path in DEFAULT_CONFIG_FILES:
            if os.path.isfile(path):
                self.load(path)
                return

    def load(self, config_file: str) -> None:
        if not YAML_AVAILABLE:
            raise ImportError(
                "PyYAML is required for YAML config files. Install: pip install PyYAML"
            )

        path = Path(config_file)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")

        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        job_config = config.get("job_submit_config", {})
        applications = job_config.get("applications", {})

        self._profiles.clear()
        for app_id, app_info in applications.items():
            profile = AppProfile(
                app_id=app_id,
                name=app_info.get("name", app_id),
                description=app_info.get("description", ""),
            )

            for param in app_info.get("parameters", []):
                param_def = ParameterDef(
                    name=param.get("name", ""),
                    param_type=param.get("type", "text"),
                    required=param.get("required", False),
                    default=(
                        str(param.get("default", ""))
                        if param.get("default") is not None
                        else None
                    ),
                    description=param.get("description", ""),
                    validation=param.get("validation") or None,
                    cli_arg=param.get("cli_arg") or None,
                    short_arg=param.get("short_arg") or None,
                )
                profile.parameters.append(param_def)

            self._profiles[app_id] = profile

        self._config_file = str(path)

    @property
    def config_file(self) -> Optional[str]:
        return self._config_file

    def list_apps(self) -> List[Dict[str, str]]:
        return [
            {"app_id": p.app_id, "name": p.name, "description": p.description}
            for p in self._profiles.values()
        ]

    def get_profile(self, app_id: str) -> Optional[AppProfile]:
        return self._profiles.get(app_id)

    def build_submit_params(
        self,
        app_id: str,
        overrides: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        profile = self._profiles.get(app_id)
        if not profile:
            raise ValueError(
                f"Unknown application: {app_id}. Available: {', '.join(self._profiles.keys())}"
            )

        params = profile.build_params(overrides)

        errors = profile.validate_params(params)
        if errors:
            raise ValueError(
                "Parameter validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        return params

    def submit_job(
        self,
        client,
        app_id: str,
        overrides: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        params = self.build_submit_params(app_id, overrides)
        return client.jobs.submit(app_id=app_id, params=params)
