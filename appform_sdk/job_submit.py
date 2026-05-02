#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用作业提交工具（基于 Appform SDK）

兼容原有 job_submit.py 命令行参数格式，使用 SDK 的认证和配置管理。

用法:
    job_submit -l                                    # 列出支持的应用
    job_submit -a starccm -h                         # 查看应用参数帮助
    job_submit -a starccm -i file.sim -n 8           # 提交作业
    job_submit -a starccm -i file.sim -n 8 --wait    # 提交后等待完成
    job_submit -a starccm -i file.sim -n 8 --wait 5  # 每5分钟查询一次

认证方式（优先级从高到低）:
    1. -u/-p 用户名密码认证（SDK auth.login）
    2. AccessKey 配置（~/.appform/config.json 或环境变量）
    3. Token 配置
    4. AES Token（集群环境，已废弃）
"""

import argparse
import json
import os
import platform
import subprocess
import sys
import textwrap
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 终态状态集合（作业已完成或异常退出）
TERMINAL_STATUSES = {"DONE", "EXIT", "ZOMBI"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_current_username() -> Optional[str]:
    """Get current system username with multiple fallback methods."""
    username = os.getenv("USER") or os.getenv("USERNAME")
    if username:
        return username
    try:
        import getpass

        username = getpass.getuser()
        if username:
            return username
    except Exception:
        pass
    try:
        import pwd

        username = pwd.getpwuid(os.getuid()).pw_name
        if username:
            return username
    except Exception:
        pass
    try:
        username = os.getlogin()
        if username:
            return username
    except Exception:
        pass
    return None


def _check_jcluster() -> bool:
    """Check if jcluster command is available (cluster environment)."""
    try:
        subprocess.run(
            ["jcluster", "-V"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


# ---------------------------------------------------------------------------
# Windows path conversion
# ---------------------------------------------------------------------------


def convert_windows_path(file_path: str, disk_mapping: Dict[str, str]) -> str:
    """
    Convert a Windows path to Linux path using disk mapping config.

    Args:
        file_path: Windows file path (e.g., S:\\project\\file.sim)
        disk_mapping: Drive letter mapping (e.g., {'S:': '/apps'})

    Returns:
        Converted Linux path
    """
    if not file_path:
        return file_path

    is_windows = platform.system() == "Windows"
    if not is_windows:
        return file_path

    normalized = os.path.normpath(file_path)

    if len(normalized) >= 2 and normalized[1] == ":":
        drive = normalized[:2].upper()
        if drive in disk_mapping:
            linux_base = disk_mapping[drive]
            relative = normalized[2:].lstrip("\\").replace("\\", "/")
            linux_path = (
                linux_base.rstrip("/") + "/" + relative if relative else linux_base
            )
            print(f"  Path conversion: {file_path} -> {linux_path}")
            return linux_path
        else:
            print(f"  Warning: no mapping for drive {drive}")
            return file_path

    return file_path.replace("\\", "/")


# ---------------------------------------------------------------------------
# Path mapping and file upload helpers
# ---------------------------------------------------------------------------


def _is_path_mapped(file_path: str, disk_mapping: Dict[str, str]) -> bool:
    """Check if a file path is already on a remote (mapped) path.

    Uses the values of disk_mapping (e.g. {'S:': '/apps'}) as the set of
    remote prefixes.  If *file_path* starts with any of them it is already
    on the server and does not need uploading.
    """
    if not disk_mapping or not file_path:
        return False
    remote_prefixes = [p.rstrip("/") for p in disk_mapping.values()]
    for prefix in remote_prefixes:
        if file_path.startswith(prefix + "/") or file_path == prefix:
            return True
    return False


def _get_default_upload_path() -> str:
    """Generate default upload path as $HOME/<YYYYMMDD_HHMMSS>/."""
    home = os.path.expanduser("~")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{home}/{timestamp}"


def _upload_files(
    client,
    local_paths: List[str],
    remote_path: str,
    transfer_method: str,
) -> Dict[str, str]:
    """Upload local files/dirs to a remote directory.

    Returns a ``{local_path: remote_path}`` mapping.  Directories are
    uploaded recursively; every contained file gets its own entry.
    """
    uploaded: Dict[str, str] = {}
    seen_local: set = set()

    for local_path in local_paths:
        lp = os.path.abspath(local_path)
        if lp in seen_local:
            continue
        seen_local.add(lp)
        p = Path(lp)
        if not p.exists():
            print(f"  Warning: not found, skipping: {local_path}", file=sys.stderr)
            continue

        remote_dir = remote_path.rstrip("/")
        if p.is_dir():
            print(f"  Uploading directory: {local_path}")
            if transfer_method == "sftp":
                client.sftp.upload_directory(str(p), remote_dir)
            else:
                client.files.upload_directory(
                    str(p), remote_dir, transfer_method="http"
                )
            for f in p.rglob("*"):
                if f.is_file():
                    rel = str(f.relative_to(p)).replace(os.sep, "/")
                    uploaded[str(f)] = f"{remote_dir}/{rel}"
        else:
            print(f"  Uploading file: {local_path}")
            if transfer_method == "sftp":
                client.sftp.upload(str(p), remote_dir)
            else:
                client.files.upload(str(p), remote_dir, transfer_method="http")
            uploaded[str(p)] = f"{remote_dir}/{p.name}"

    return uploaded


def _apply_uploaded_paths(
    overrides: Dict[str, str],
    upload_params: List[Any],
    path_mapping: Dict[str, str],
) -> Dict[str, str]:
    """Replace local paths with remote ones for upload-type params.

    Handles comma-separated multi-file values.
    """
    upload_param_names = {p.name for p in upload_params}
    result = dict(overrides)
    for key in upload_param_names:
        value = result.get(key, "")
        if not value:
            continue
        parts = [p.strip() for p in value.split(",")]
        new_parts = []
        for part in parts:
            abs_part = os.path.abspath(part)
            mapped = path_mapping.get(abs_part, part)
            new_parts.append(mapped)
        result[key] = ",".join(new_parts)
    return result


# ---------------------------------------------------------------------------
# Wait for job completion
# ---------------------------------------------------------------------------


def _wait_for_job(client, job_id: str, interval_minutes: int = 10) -> int:
    """
    Poll job status until it reaches a terminal state.

    Args:
        client: Authenticated AppformClient
        job_id: Job ID to monitor
        interval_minutes: Polling interval in minutes (default: 10)

    Returns:
        Exit code: 0 for success (DONE), 1 for failure (EXIT/ERROR)
    """
    interval_seconds = interval_minutes * 60
    start_time = time.time()
    check_count = 0

    print(
        f"\nWaiting for job {job_id} to complete (polling every {interval_minutes} min, Ctrl+C to stop)..."
    )
    print(f"{'Time':>10s}  {'Status':<10s}  Message")
    print("-" * 60)

    while True:
        check_count += 1
        elapsed = int(time.time() - start_time)
        elapsed_str = (
            f"{elapsed // 3600:02d}:{(elapsed % 3600) // 60:02d}:{elapsed % 60:02d}"
        )

        try:
            result = client.jobs.get_job(job_id)
        except KeyboardInterrupt:
            print(f"\nInterrupted. Job {job_id} is still running.")
            return 130
        except Exception as e:
            print(f"{elapsed_str:>10s}  {'ERROR':<10s}  Query failed: {e}")
            time.sleep(interval_seconds)
            continue

        if not isinstance(result, dict) or result.get("code") != 200:
            print(f"{elapsed_str:>10s}  {'ERROR':<10s}  Invalid response: {result}")
            time.sleep(interval_seconds)
            continue

        job_info = result.get("data", {})
        if isinstance(job_info, list):
            job_info = job_info[0] if job_info else {}

        status = job_info.get("status", "UNKNOWN")
        message = job_info.get("message", "") or job_info.get("jobName", "")

        print(f"{elapsed_str:>10s}  {status:<10s}  {message}")

        if status in TERMINAL_STATUSES:
            print(f"\nJob {job_id} finished with status: {status}")
            if status == "DONE":
                return 0
            return 1

        try:
            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print(f"\nInterrupted. Job {job_id} is still running (status: {status}).")
            return 130


# ---------------------------------------------------------------------------
# CLI formatter
# ---------------------------------------------------------------------------


class _HelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom help formatter with better Chinese text support."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._max_help_position = 35
        self._width = 100

    def _format_action_invocation(self, action):
        if not action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            (metavar,) = self._metavar_formatter(action, default)(1)
            return metavar
        parts = list(action.option_strings)
        if action.nargs != 0:
            default = self._get_default_metavar_for_optional(action)
            args_string = self._format_args(action, default)
            parts[-1] += " %s" % args_string
        return ", ".join(parts)

    def _split_lines(self, text, width):
        if not text:
            return []
        lines = []
        for paragraph in text.split("\n"):
            if len(paragraph) <= width:
                lines.append(paragraph)
            else:
                wrapped = textwrap.fill(
                    paragraph,
                    width=width,
                    break_long_words=False,
                    break_on_hyphens=False,
                )
                lines.extend(wrapped.split("\n"))
        return lines

    def _format_usage(self, usage, actions, groups, prefix):
        if prefix is None:
            prefix = "usage: "
        prog = self._prog
        basic_args = []
        app_args = []
        for action in actions:
            if action.option_strings:
                arg_str = "/".join(action.option_strings)
                if action.dest in ("app", "list_apps", "username", "password", "help"):
                    basic_args.append(
                        "[%s]" % arg_str
                        if action.nargs == 0
                        else "[%s %s]" % (arg_str, action.dest.upper())
                    )
                else:
                    if action.required:
                        app_args.append(
                            "%s" % arg_str
                            if action.nargs == 0
                            else "%s %s" % (arg_str, action.dest.upper())
                        )
                    else:
                        app_args.append(
                            "[%s]" % arg_str
                            if action.nargs == 0
                            else "[%s %s]" % (arg_str, action.dest.upper())
                        )
        usage_parts = [prog] + basic_args
        if app_args:
            if len(" ".join(app_args)) > 60:
                usage_parts.append("[APP_SPECIFIC_OPTIONS...]")
            else:
                usage_parts.extend(app_args)
        usage_str = " ".join(usage_parts)
        return prefix + (
            prog + " [OPTIONS...]\n" if len(usage_str) > 80 else usage_str + "\n"
        )


# ---------------------------------------------------------------------------
# Parser builder (mirrors job_submit.py interface)
# ---------------------------------------------------------------------------


def _build_epilog(
    profile, app_id: Optional[str] = None, disk_mapping: Optional[Dict] = None
) -> str:
    """Build help epilog text."""
    parts = []
    parts.append("Usage examples:")
    parts.append("  job_submit -a starccm -i /path/to/file.sim --ncpu 8")
    parts.append(
        "  job_submit -a starccm -i /path/to/file.sim -n 8 --wait       # submit and wait"
    )
    parts.append(
        "  job_submit -a starccm -i /path/to/file.sim -n 8 --wait 5    # poll every 5 min"
    )
    parts.append("  job_submit -a lsdyna2 -i /path/to/input.k --ncpu 16")
    parts.append("  job_submit -l")
    parts.append("")

    if disk_mapping:
        parts.append("Windows path mapping:")
        for drive, path in disk_mapping.items():
            parts.append(f"  {drive} -> {path}")
        parts.append("")

    if app_id and profile:
        required = profile.get_required_params()
        if required:
            parts.append(f"{profile.name} required parameters:")
            for pd in required:
                if pd.cli_arg and pd.short_arg:
                    arg_str = f"  -{pd.short_arg}, --{pd.cli_arg}"
                elif pd.cli_arg:
                    arg_str = f"  --{pd.cli_arg}"
                elif pd.short_arg:
                    arg_str = f"  -{pd.short_arg}, --{pd.effective_cli_name}"
                else:
                    arg_str = f"  --{pd.effective_cli_name}"
                parts.append(f"{arg_str:<30} {pd.description}")
            parts.append("")

    return "\n".join(parts)


def _build_parser(
    pm, app_id: Optional[str] = None, disk_mapping: Optional[Dict] = None
) -> argparse.ArgumentParser:
    """Build argparse parser compatible with original job_submit.py."""
    supported = [a["app_id"] for a in pm.list_apps()]

    parser = argparse.ArgumentParser(
        prog="job_submit",
        description="Universal job submission tool for multiple applications.",
        formatter_class=_HelpFormatter,
        epilog=_build_epilog(
            pm.get_profile(app_id) if app_id else None, app_id, disk_mapping
        ),
    )

    parser.add_argument(
        "-a",
        "--app",
        choices=supported,
        metavar="{%s}" % ",".join(supported),
        help="Select application type",
    )
    parser.add_argument(
        "-l",
        "--list-apps",
        action="store_true",
        dest="list_apps",
        help="List all supported applications",
    )
    parser.add_argument(
        "-u", "--username", metavar="USER", help="Authentication username"
    )
    parser.add_argument(
        "-p", "--password", metavar="PASS", help="Authentication password"
    )
    parser.add_argument(
        "--wait",
        nargs="?",
        const=10,
        type=int,
        metavar="MINUTES",
        help="Wait for job to complete after submit (default: poll every 10 min)",
    )
    parser.add_argument(
        "--upload-path",
        dest="upload_path",
        default=None,
        metavar="PATH",
        help="Remote directory for uploading local files (default: ~/<timestamp>/)",
    )

    # Add app-specific parameters
    if app_id:
        profile = pm.get_profile(app_id)
        if profile:
            required = [p for p in profile.parameters if p.required]
            optional = [p for p in profile.parameters if not p.required]
            if required:
                group = parser.add_argument_group(f"{profile.name} required parameters")
                _add_params(group, required)
            if optional:
                group = parser.add_argument_group(f"{profile.name} optional parameters")
                _add_params(group, optional)

    return parser


def _add_params(group, params):
    """Add ParameterDef objects as argparse arguments."""
    from .job_profiles import ParameterDef

    for pd in params:
        arg_options = []
        if pd.short_arg:
            arg_options.append(f"-{pd.short_arg}")
        arg_options.append(f"--{pd.effective_cli_name}")

        help_text = pd.description
        if pd.default:
            help_text += f" (default: {pd.default})"

        metavar = None
        if pd.param_type == "upload":
            metavar = "FILE"
        elif pd.default:
            metavar = str(pd.default).upper()
        else:
            metavar = pd.effective_cli_name.replace("-", "_").upper()

        kwargs = {
            "dest": f"param_{pd.effective_cli_name.replace('-', '_')}",
            "help": help_text,
        }

        if pd.param_type == "switch":
            kwargs["nargs"] = "?"
            kwargs["const"] = "on"
            kwargs["choices"] = ["on", "off"]
            kwargs["metavar"] = "{on,off}"
            kwargs["default"] = pd.default if pd.default else "off"
        elif pd.param_type == "upload":
            kwargs["nargs"] = "+"
            kwargs["metavar"] = "FILE..."
            kwargs["help"] = help_text + " (支持多个文件/目录)"
            if pd.required:
                kwargs["required"] = True
        else:
            kwargs["metavar"] = metavar
            if pd.required:
                kwargs["required"] = True

        group.add_argument(*arg_options, **kwargs)


# ---------------------------------------------------------------------------
# Build overrides from parsed args
# ---------------------------------------------------------------------------


def _collect_overrides(profile, parsed_args) -> Dict[str, str]:
    """Extract parameter overrides from parsed argparse namespace."""
    overrides = {}

    for pd in profile.parameters:
        attr = f"param_{pd.effective_cli_name.replace('-', '_')}"
        value = getattr(parsed_args, attr, None)
        if value is not None:
            if pd.param_type == "switch":
                overrides[pd.name] = str(value)
            elif pd.param_type == "upload":
                if isinstance(value, list):
                    overrides[pd.name] = ",".join(str(v) for v in value if v)
                elif value not in (None, ""):
                    overrides[pd.name] = str(value)
            elif value not in (None, ""):
                overrides[pd.name] = str(value)

    # Auto-fill JH_JOB_NAME from JH_CAS if not set
    if "JH_JOB_NAME" not in overrides:
        cas_value = overrides.get("JH_CAS")
        if cas_value:
            overrides["JH_JOB_NAME"] = os.path.splitext(os.path.basename(cas_value))[0]

    return overrides


def _apply_path_conversion(
    overrides: Dict[str, str], disk_mapping: Dict[str, str]
) -> Dict[str, str]:
    """Convert Windows paths in upload-type parameters."""
    is_windows = platform.system() == "Windows"
    if not is_windows or not disk_mapping:
        return overrides

    upload_params = {
        "JH_CAS",
        "JH_DAT",
        "JH_JAVA",
        "JH_JAVA2",
        "JH_JAVA_MESH",
        "JH_JAVA_RUN",
        "JH_RESTART_FILE",
        "JH_SEED_FILE",
        "JH_JSUB_POST_EXEC",
        "JH_INC",
        "JH_ODB",
        "JH_UF",
        "JH_INPUT",
        "JH_OFILE",
        "JH_IMPRES",
        "JH_FLOW_FILE",
        "JH_SCRIPT_FILE",
    }

    result = {}
    for key, value in overrides.items():
        if key in upload_params and value:
            value = convert_windows_path(value, disk_mapping)
            if not os.path.isabs(value):
                value = os.path.abspath(value)
        result[key] = value

    return result


# ---------------------------------------------------------------------------
# Resolve config from profile file or SDK config
# ---------------------------------------------------------------------------


def _resolve_base_url(pm) -> str:
    """Resolve the Appform base URL from config or defaults.

    Priority: SDK config (env vars / config.json) > profile config (job_submit.yaml) > default
    """
    base_url = None

    # 1. SDK config has highest priority (matches appform CLI behavior)
    from .config import Config

    cfg = Config()
    base_url = cfg.base_url

    # 2. Fall back to profile config's appform_base_url
    if not base_url and pm.config_file:
        try:
            import yaml

            with open(pm.config_file, "r", encoding="utf-8") as f:
                pconfig = yaml.safe_load(f)
            base_url = pconfig.get("job_submit_config", {}).get("appform_base_url")
        except Exception:
            pass

    # 3. Default fallback
    if not base_url:
        base_url = "https://10.241.219.230/appform"

    # SDK paths start with /appform/ws/api/..., so strip trailing /appform
    # from base_url to avoid double path: https://server/appform/appform/ws/...
    if base_url.endswith("/appform"):
        base_url = base_url[: -len("/appform")]

    return base_url


def _resolve_disk_mapping(pm) -> Dict[str, str]:
    """Resolve Windows disk mapping from config."""
    if pm.config_file:
        try:
            import yaml

            with open(pm.config_file, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            return cfg.get("job_submit_config", {}).get("windows_disk_mapping", {})
        except Exception:
            pass
    return {}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main(args=None):
    """
    Main entry point for job_submit command.

    Compatible with original job_submit.py CLI:
        job_submit -l                    # list apps
        job_submit -a starccm -h         # app help
        job_submit -a starccm -i file    # submit
        job_submit -a starccm -i file --wait       # submit and wait
        job_submit -a starccm -i file --wait 5     # poll every 5 min

    All authentication goes through the SDK:
        - Password login:  client.auth.login(username, password)
        - AES token login: client.auth.login_with_token(username)
        - AccessKey:       client.auth.login_with_access_key(...)
    """
    # Load profile config
    from .config import Config
    from .job_profiles import JobProfileManager

    sdk_config = Config()
    profile_config = sdk_config.job_profile_config

    try:
        pm = JobProfileManager(config_file=profile_config)
    except Exception as e:
        print(f"Error loading job profile config: {e}", file=sys.stderr)
        sys.exit(1)

    if not pm.list_apps():
        print("Error: No application configurations found.", file=sys.stderr)
        sys.exit(1)

    disk_mapping = _resolve_disk_mapping(pm)
    base_url = _resolve_base_url(pm)

    # --- Pass 1: find -a / -l / -u / -p / --wait / --upload-path ---
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("-a", "--app", dest="_app", default=None)
    pre.add_argument("-l", "--list-apps", action="store_true", dest="_list_apps")
    pre.add_argument("-u", "--username", dest="_username", default=None)
    pre.add_argument("-p", "--password", dest="_password", default=None)
    pre.add_argument(
        "--wait", nargs="?", const=10, type=int, dest="_wait", default=None
    )
    pre.add_argument("--upload-path", dest="_upload_path", default=None)
    pre_args, remaining = pre.parse_known_args(args)

    # List apps
    if pre_args._list_apps:
        print("Supported applications:")
        for app in pm.list_apps():
            print(f"  - {app['app_id']}")
        if disk_mapping:
            print("\nWindows path mapping:")
            for drive, path in disk_mapping.items():
                print(f"  {drive} -> {path}")
        return

    # Check for -h/--help in remaining args
    show_help = False
    filtered = []
    for a in remaining:
        if a in ("-h", "--help"):
            show_help = True
        else:
            filtered.append(a)

    app_id = pre_args._app

    if not app_id and not show_help:
        supported = [a["app_id"] for a in pm.list_apps()]
        print(f"Supported applications: {', '.join(supported)}")
        print(f"\nUsage:")
        print(f"  job_submit -a <app> [options]           # Submit a job")
        print(
            f"  job_submit -a <app> [options] --wait    # Submit and wait for completion"
        )
        print(f"  job_submit -l                           # List applications")
        print(f"  job_submit -a <app> -h                  # Show app-specific help")
        return

    # --- Pass 2: build full parser with app-specific args ---
    profile = pm.get_profile(app_id) if app_id else None
    if app_id and not profile:
        available = [a["app_id"] for a in pm.list_apps()]
        print(
            f"Error: Unknown application '{app_id}'. Available: {', '.join(available)}",
            file=sys.stderr,
        )
        sys.exit(1)

    full_parser = _build_parser(pm, app_id, disk_mapping)

    if show_help:
        full_parser.parse_args(["--help"] if not app_id else filtered + ["--help"])
        return

    try:
        parsed = full_parser.parse_args(filtered)
    except SystemExit:
        return

    if parsed.list_apps:
        print("Supported applications:")
        for app in pm.list_apps():
            print(f"  - {app['app_id']}")
        return

    if not app_id:
        app_id = getattr(parsed, "app", None)
        if not app_id:
            full_parser.print_help()
            return
        profile = pm.get_profile(app_id)

    # Resolve --wait: pre-parser value takes precedence (comes from global args)
    wait_minutes = pre_args._wait
    if wait_minutes is None:
        wait_minutes = getattr(parsed, "wait", None)

    # --- Environment check ---
    is_cluster = _check_jcluster()
    current_user = _get_current_username()

    if current_user == "root":
        print("Error: Please do not use the root account to execute this script.")
        sys.exit(1)

    # --- Build params ---
    overrides = _collect_overrides(profile, parsed)
    overrides = _apply_path_conversion(overrides, disk_mapping)

    # --- Create SDK client and authenticate ---
    from .client import AppformClient

    client_kwargs = {"base_url": base_url, "verify_ssl": False, "config": sdk_config}

    # Determine authentication method
    username = pre_args._username
    password = pre_args._password

    try:
        if username and password:
            # 1. Password auth via CLI args
            client = AppformClient(**client_kwargs)
            result = client.auth.login(username, password)
            if result.get("result") != "success" or not client.token:
                msg = (
                    result.get("message", "Unknown error")
                    if isinstance(result, dict)
                    else "Login failed"
                )
                print(
                    f"Error: Login failed for user '{username}': {msg}", file=sys.stderr
                )
                client.close()
                sys.exit(1)
            print(f"Authenticated as '{username}' (password login)")
        elif sdk_config.username and sdk_config.password:
            # 2. Password auth from config file (~/.appform/config.json)
            client = AppformClient(**client_kwargs)
            result = client.auth.login(sdk_config.username, sdk_config.password)
            if result.get("result") != "success" or not client.token:
                msg = (
                    result.get("message", "Unknown error")
                    if isinstance(result, dict)
                    else "Login failed"
                )
                print(
                    f"Error: Login failed for user '{sdk_config.username}': {msg}",
                    file=sys.stderr,
                )
                client.close()
                sys.exit(1)
            print(f"Authenticated as '{sdk_config.username}' (password from config)")
        elif sdk_config.access_key and sdk_config.access_key_secret:
            # 3. AccessKey auth (requires 6.4+)
            client_kwargs["access_key"] = sdk_config.access_key
            client_kwargs["access_key_secret"] = sdk_config.access_key_secret
            client_kwargs["username"] = sdk_config.username or current_user
            client = AppformClient(**client_kwargs)
            print(f"Authenticated via AccessKey (user: {client_kwargs['username']})")
        elif sdk_config.token:
            # 4. Token auth from config
            client_kwargs["token"] = sdk_config.token
            client = AppformClient(**client_kwargs)
            print("Authenticated via token from config")
        elif is_cluster and current_user and current_user != "root":
            # 5. Cluster AES token auth (requires aes_key configured)
            client_kwargs["aes_key"] = sdk_config.aes_key
            client = AppformClient(**client_kwargs)
            try:
                result = client.auth.login_with_token()
                if not client.token:
                    print("Error: Cluster authentication failed.", file=sys.stderr)
                    client.close()
                    sys.exit(1)
                print(f"Authenticated as '{current_user}' (AES token, cluster)")
            except Exception as e:
                print(f"Error: AES authentication failed: {e}", file=sys.stderr)
                client.close()
                sys.exit(1)
        else:
            print("Error: No authentication available.", file=sys.stderr)
            print("Options:", file=sys.stderr)
            print("  1. Provide -u and -p arguments", file=sys.stderr)
            print(
                "  2. Configure username and password in ~/.appform/config.json",
                file=sys.stderr,
            )
            print("  3. Configure AccessKey (requires Appform 6.4+)", file=sys.stderr)
            sys.exit(1)

        # --- Upload local files if needed ---
        upload_path = getattr(parsed, "upload_path", None) or pre_args._upload_path
        upload_params_list = profile.get_upload_params()
        transfer_method = sdk_config.default_method

        # Collect local files that need uploading
        files_to_upload: List[str] = []
        for param in upload_params_list:
            val = overrides.get(param.name, "")
            if val:
                for f in val.split(","):
                    f = f.strip()
                    if f and not _is_path_mapped(f, disk_mapping):
                        files_to_upload.append(f)

        path_mapping: Dict[str, str] = {}
        if files_to_upload:
            if not upload_path:
                upload_path = _get_default_upload_path()
            print(f"Uploading {len(files_to_upload)} local file(s) to {upload_path}...")
            path_mapping = _upload_files(
                client, files_to_upload, upload_path, transfer_method
            )
            overrides = _apply_uploaded_paths(
                overrides, upload_params_list, path_mapping
            )
            print("Upload complete.")

        # --- Build final params ---
        try:
            params = pm.build_submit_params(app_id, overrides)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            client.close()
            sys.exit(1)

        params_str = json.dumps(params, ensure_ascii=False)

        # --- Submit job via SDK ---
        result = client.jobs.submit(app_id=app_id, params=params)

        if isinstance(result, dict):
            code = result.get("code")
            if code == 200:
                job_data = result.get("data", [{}])
                job_id = job_data[0].get("jobid", "Unknown") if job_data else "Unknown"
                print(f"Job submitted successfully!")
                print(f"  Application: {app_id}")
                print(f"  Job ID: {job_id}")
                print(f"  Parameters: {params_str}")

                # --- Wait for job completion ---
                if wait_minutes is not None:
                    exit_code = _wait_for_job(client, job_id, wait_minutes)
                    client.close()
                    sys.exit(exit_code)

                client.close()
            else:
                client.close()
                print(
                    f"Job submission failed: {result.get('message', 'Unknown error')}",
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            client.close()
            print(f"Unexpected response: {result}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
