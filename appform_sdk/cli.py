#!/usr/bin/env python3
"""
Command-line interface for Appform SDK
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from . import __version__
from .client import AppformClient
from .config import Config
from .formatters import format_output
from .job_submit import _apply_path_conversion, _resolve_disk_mapping


def _get_completion_script(shell: str) -> Optional[str]:
    """Get shell completion script content."""
    import importlib.resources

    try:
        if sys.version_info >= (3, 9):
            return (
                importlib.resources.files("appform_sdk.completions")
                .joinpath(f"appform-completion.{shell}")
                .read_text()
            )
        else:
            return importlib.resources.read_text(
                "appform_sdk.completions", f"appform-completion.{shell}"
            )
    except (FileNotFoundError, ImportError):
        return None


class _SubmitHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom formatter for job submit help that shows app-specific params."""

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


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="appform",
        description="Appform SDK - Python client for Appform 6.0-6.6 API",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--generate-completion",
        choices=["bash", "zsh", "fish"],
        help="Generate shell completion script",
    )

    # Global options
    parser.add_argument(
        "--base-url",
        dest="base_url",
        help="API base URL (or set APPFORM_BASE_URL env var)",
    )
    parser.add_argument(
        "--access-key",
        dest="access_key",
        help="Access key (or set APPFORM_ACCESS_KEY env var)",
    )
    parser.add_argument(
        "--access-key-secret",
        dest="access_key_secret",
        help="Access key secret (or set APPFORM_ACCESS_KEY_SECRET env var)",
    )
    parser.add_argument(
        "--username",
        dest="auth_username",
        help="Username (or set APPFORM_USERNAME env var)",
    )
    parser.add_argument(
        "--password",
        dest="auth_password",
        help="Password (or set APPFORM_PASSWORD env var)",
    )
    parser.add_argument(
        "--token",
        dest="token",
        help="Authentication token (or set APPFORM_TOKEN env var)",
    )
    parser.add_argument(
        "--api-version",
        dest="api_version",
        help="API version (or set APPFORM_API_VERSION env var, default: 6.5)",
    )
    parser.add_argument(
        "--extensions-dir",
        dest="extensions_dir",
        help="Extensions directory (or set APPFORM_EXTENSIONS_DIR env var)",
    )
    parser.add_argument(
        "--config",
        dest="config_file",
        help="Path to configuration file (default: ~/.appform/config.json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["json", "raw", "table", "text"],
        default=None,
        help="Output format: raw (original API data), json (template-filtered), table (formatted, default), text",
    )

    parser.add_argument(
        "--output-template",
        dest="output_template",
        help="Output template file (.yaml/.yml/.json) to customize display fields",
    )
    parser.add_argument(
        "--profile-config",
        dest="profile_config",
        help="Job profile config file (or set APPFORM_JOB_PROFILE_CONFIG env var)",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Config
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_subparsers = config_parser.add_subparsers(
        dest="config_command", help="Config commands"
    )
    config_set_parser = config_subparsers.add_parser(
        "set", help="Set configuration values"
    )
    config_set_parser.add_argument("--base-url", help="API base URL")
    config_set_parser.add_argument("--access-key", help="Access key")
    config_set_parser.add_argument("--access-key-secret", help="Access key secret")
    config_set_parser.add_argument("--username", help="Username")
    config_set_parser.add_argument("--password", help="Password")
    config_set_parser.add_argument("--token", help="Authentication token")
    config_set_parser.add_argument(
        "--timeout", type=int, help="Request timeout in seconds"
    )
    config_set_parser.add_argument(
        "--verify-ssl", type=lambda x: x.lower() == "true", help="Verify SSL"
    )
    config_set_parser.add_argument("--api-version", help="API version")
    config_set_parser.add_argument("--extensions-dir", help="Extensions directory")
    config_set_parser.add_argument(
        "--job-profile-config",
        dest="job_profile_config",
        help="Job profile config file path (job_submit.yaml)",
    )
    config_set_parser.add_argument(
        "--output-format",
        dest="output_format",
        choices=["json", "raw", "table", "text"],
        help="Default output format",
    )
    config_set_parser.add_argument(
        "--output-template",
        dest="output_template",
        help="Output template file path (.yaml/.yml/.json)",
    )
    config_set_parser.add_argument(
        "--default-remote-path",
        dest="default_remote_path",
        help="Default remote path for file operations",
    )
    config_set_parser.add_argument(
        "--chunk-size",
        dest="chunk_size",
        help="Read chunk size for upload/download (e.g. '100M', '1G', or bytes, default: 100M)",
    )
    config_set_parser.add_argument(
        "--default-method",
        dest="default_method",
        choices=["http", "sftp"],
        help="Default transfer method for file operations (default: http)",
    )
    config_set_parser.add_argument("--config-file", help="Config file path")
    config_set_parser.add_argument(
        "--sftp-host",
        dest="sftp_host",
        help="SFTP server hostname (defaults to host from base_url)",
    )
    config_set_parser.add_argument(
        "--sftp-port",
        dest="sftp_port",
        type=int,
        help="SFTP server port (default: 22)",
    )
    config_set_parser.add_argument(
        "--sftp-username",
        dest="sftp_username",
        help="SFTP username (defaults to username)",
    )
    config_set_parser.add_argument(
        "--sftp-password",
        dest="sftp_password",
        help="SFTP password (defaults to password)",
    )
    config_set_parser.add_argument(
        "--sftp-key-file",
        dest="sftp_key_file",
        help="SSH private key file path for SFTP",
    )
    config_set_parser.add_argument(
        "--sftp-key-password",
        dest="sftp_key_password",
        help="SSH key passphrase for SFTP",
    )
    config_show_parser = config_subparsers.add_parser(
        "show", help="Show current configuration"
    )
    config_show_parser.add_argument("--config-file", help="Config file path")

    # Extension
    ext_parser = subparsers.add_parser("extension", help="Manage extensions")
    ext_subparsers = ext_parser.add_subparsers(
        dest="extension_command", help="Extension commands"
    )
    ext_subparsers.add_parser("list", help="List loaded extensions")
    ext_load_parser = ext_subparsers.add_parser("load", help="Load an extension")
    ext_load_parser.add_argument("file", help="Extension configuration file")

    # Endpoint
    endpoint_parser = subparsers.add_parser("endpoint", help="Manage endpoints")
    endpoint_subparsers = endpoint_parser.add_subparsers(
        dest="endpoint_command", help="Endpoint commands"
    )
    endpoint_list_parser = endpoint_subparsers.add_parser(
        "list", help="List registered endpoints"
    )
    endpoint_list_parser.add_argument("--version", help="Filter by API version")
    endpoint_call_parser = endpoint_subparsers.add_parser(
        "call", help="Call an endpoint by name"
    )
    endpoint_call_parser.add_argument("name", help="Endpoint name (e.g., jobs.list)")
    endpoint_call_parser.add_argument("--params", help="Query parameters as JSON")
    endpoint_call_parser.add_argument("--data", help="Request body as JSON")
    endpoint_call_parser.add_argument("--path-params", help="Path parameters as JSON")

    # Auth
    auth_parser = subparsers.add_parser("auth", help="Authentication operations")
    auth_subparsers = auth_parser.add_subparsers(
        dest="auth_command", help="Auth commands"
    )
    auth_login_parser = auth_subparsers.add_parser(
        "login", help="Login with username and password"
    )
    auth_login_parser.add_argument("--username", required=True, help="Username")
    auth_login_parser.add_argument("--password", required=True, help="Password")
    auth_subparsers.add_parser("ping", help="Test authentication")
    auth_subparsers.add_parser("logout", help="Logout")

    # Jobs
    jobs_parser = subparsers.add_parser("jobs", help="Job operations")
    jobs_subparsers = jobs_parser.add_subparsers(
        dest="jobs_command", help="Jobs commands"
    )

    jobs_subparsers.add_parser("apps", help="List applications from job profile config")

    jobs_params_parser = jobs_subparsers.add_parser(
        "params", help="Show parameters for an application"
    )
    jobs_params_parser.add_argument("app_id", help="Application ID")

    # Jobs submit — minimal placeholder; real args are built dynamically in handle_jobs_submit
    jobs_subparsers.add_parser(
        "submit", help="Submit a job (use -a <app> -h for app-specific help)"
    )

    # Jobs submit-raw
    jobs_raw_parser = jobs_subparsers.add_parser(
        "submit-raw", help="Submit a job with raw JSON params"
    )
    jobs_raw_parser.add_argument(
        "--app-id", required=True, dest="app_id", help="Application ID"
    )
    jobs_raw_parser.add_argument(
        "--params", required=True, help="Job parameters as JSON string"
    )

    # Jobs list/status/get/stop/suspend/resume/output/files/history
    jobs_list_parser = jobs_subparsers.add_parser("list", help="List jobs")
    jobs_list_parser.add_argument("--page", type=int, default=1, help="Page number")
    jobs_list_parser.add_argument("--page-size", type=int, default=20, help="Page size")
    jobs_list_parser.add_argument(
        "--status", help="Filter by status (RUN, PEND, DONE, EXIT)"
    )
    jobs_list_parser.add_argument("--name", help="Filter by job name")
    jobs_list_parser.add_argument(
        "--job-id",
        "--jobid",
        dest="job_id",
        help="Query by job ID (single or comma-separated)",
    )

    jobs_status_parser = jobs_subparsers.add_parser(
        "status", help="List jobs by status"
    )
    jobs_status_parser.add_argument(
        "status",
        nargs="?",
        default=None,
        help="Job status (RUN, PEND, DONE, EXIT, all)",
    )
    jobs_status_parser.add_argument("--page", type=int, default=1, help="Page number")
    jobs_status_parser.add_argument(
        "--page-size", type=int, default=20, help="Page size"
    )

    for cmd in (
        "get",
        "stop",
        "suspend",
        "resume",
        "output",
        "files",
        "history",
        "delete",
    ):
        p = jobs_subparsers.add_parser(cmd, help=f"{cmd.capitalize()} a job")
        p.add_argument("job_id", help="Job ID")

    jobs_history_page_parser = jobs_subparsers.add_parser(
        "history-page", help="List history jobs with pagination"
    )
    jobs_history_page_parser.add_argument(
        "--page", type=int, default=1, help="Page number"
    )
    jobs_history_page_parser.add_argument(
        "--page-size", type=int, default=20, help="Page size"
    )

    jobs_form_parser = jobs_subparsers.add_parser(
        "form", help="Get job submission form (6.6+)"
    )
    jobs_form_parser.add_argument("app_id", help="Application ID")

    jobs_subparsers.add_parser("tooltip", help="Get job app monitoring info (6.6+)")

    # Sessions
    sessions_parser = subparsers.add_parser("sessions", help="Session operations")
    sessions_subparsers = sessions_parser.add_subparsers(
        dest="sessions_command", help="Sessions commands"
    )

    sessions_start_parser = sessions_subparsers.add_parser(
        "start", help="Start a new session"
    )
    sessions_start_parser.add_argument(
        "--app-id",
        required=True,
        dest="app_id",
        help="Application ID (e.g., gedit, xterm)",
    )
    sessions_start_parser.add_argument(
        "--start-new",
        action="store_true",
        dest="start_new",
        help="Start a new session instance",
    )
    sessions_start_parser.add_argument(
        "--cwd", help="Working directory path (e.g., ${HOME})"
    )
    sessions_start_parser.add_argument(
        "--work-file",
        dest="work_file",
        help="File path to open when starting the application",
    )
    sessions_start_parser.add_argument(
        "--param", help="Launch parameters (URL-encoded)"
    )

    sessions_list_parser = sessions_subparsers.add_parser(
        "list", help="Query sessions (default: current user's sessions)"
    )
    sessions_list_parser.add_argument(
        "--ids", dest="session_ids", help="Session IDs (comma-separated)"
    )
    sessions_list_parser.add_argument(
        "--name", dest="session_name", help="Session name to query"
    )

    sessions_list_all_parser = sessions_subparsers.add_parser(
        "list-all", help="List all sessions"
    )
    sessions_list_all_parser.add_argument(
        "--page", type=int, default=1, help="Page number"
    )
    sessions_list_all_parser.add_argument(
        "--page-size", type=int, default=20, help="Page size"
    )

    p = sessions_subparsers.add_parser(
        "connect", help="Get connection info for a session"
    )
    p.add_argument("session_id", help="Session ID")

    p = sessions_subparsers.add_parser(
        "connect-launch", help="Get connection info and auto-launch JHApp client"
    )
    p.add_argument("session_id", help="Session ID")

    for cmd in ("disconnect", "close"):
        p = sessions_subparsers.add_parser(cmd, help=f"{cmd.capitalize()} a session")
        p.add_argument("session_id", help="Session ID")

    sessions_share_parser = sessions_subparsers.add_parser(
        "share", help="Share a session"
    )
    sessions_share_parser.add_argument("session_id", help="Session ID")
    sessions_share_parser.add_argument(
        "--usernames", required=True, help="Usernames to share with (comma separated)"
    )

    # Files — Linux-like commands
    files_parser = subparsers.add_parser(
        "files", help="File operations (Linux-like commands)"
    )
    files_parser.add_argument(
        "--method",
        dest="default_method",
        choices=["http", "sftp"],
        default=None,
        help="Default transfer method for all file operations (overridden by per-command --method)",
    )
    files_subparsers = files_parser.add_subparsers(
        dest="files_command", help="Files commands"
    )

    # ls [path]
    files_ls_parser = files_subparsers.add_parser(
        "ls", help="List remote directory contents"
    )
    files_ls_parser.add_argument(
        "path", nargs="?", default="/", help="Remote directory path (default: /)"
    )
    files_ls_parser.add_argument("--page", type=int, default=1, help="Page number")
    files_ls_parser.add_argument("--page-size", type=int, default=100, help="Page size")
    files_ls_parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        dest="list_all",
        help="List all items (auto-pagination)",
    )
    files_ls_parser.add_argument(
        "--method",
        choices=["http", "sftp"],
        default=None,
        help="Transfer method: http (default via API) or sftp",
    )

    # cp <src> <dest>
    files_cp_parser = files_subparsers.add_parser(
        "cp", help="Copy remote file or directory"
    )
    files_cp_parser.add_argument("src", help="Source remote path")
    files_cp_parser.add_argument("dest", help="Destination remote directory")
    files_cp_parser.add_argument(
        "--method",
        choices=["http", "sftp"],
        default=None,
        help="Transfer method: http (default via API) or sftp",
    )

    # mv <src> <dest>
    files_mv_parser = files_subparsers.add_parser(
        "mv", help="Move/rename remote file or directory"
    )
    files_mv_parser.add_argument("src", help="Source remote path")
    files_mv_parser.add_argument("dest", help="Destination path or new name")
    files_mv_parser.add_argument(
        "--method",
        choices=["http", "sftp"],
        default=None,
        help="Transfer method: http (default via API) or sftp",
    )

    # rm <path>
    files_rm_parser = files_subparsers.add_parser(
        "rm", help="Delete remote file or directory"
    )
    files_rm_parser.add_argument("path", help="Remote path to delete")
    files_rm_parser.add_argument(
        "--method",
        choices=["http", "sftp"],
        default=None,
        help="Transfer method: http (default via API) or sftp",
    )

    # mkdir <path>
    files_mkdir_parser = files_subparsers.add_parser(
        "mkdir", help="Create remote directory"
    )
    files_mkdir_parser.add_argument("path", help="Remote directory path to create")
    files_mkdir_parser.add_argument(
        "--no-force",
        action="store_true",
        dest="no_force",
        help="Fail if directory already exists",
    )
    files_mkdir_parser.add_argument(
        "--method",
        choices=["http", "sftp"],
        default=None,
        help="Transfer method: http (default via API) or sftp",
    )

    # put <local> [remote]  — upload
    files_put_parser = files_subparsers.add_parser(
        "put", help="Upload local file or directory to remote"
    )
    files_put_parser.add_argument("local", help="Local file or directory path")
    files_put_parser.add_argument(
        "remote",
        nargs="?",
        default=None,
        help="Remote destination path (default: default_remote_path from config)",
    )
    files_put_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite existing remote files without confirmation",
    )
    files_put_parser.add_argument(
        "--chunk-size",
        dest="chunk_size",
        help="Read chunk size (e.g. '100M', '1G', default: from config or 100M)",
    )
    files_put_parser.add_argument(
        "--method",
        choices=["http", "sftp"],
        default=None,
        help="Transfer method: http (default via API) or sftp",
    )

    # get <remote> [local]  — download
    files_get_parser = files_subparsers.add_parser(
        "get", help="Download remote file or directory to local"
    )
    files_get_parser.add_argument("remote", help="Remote file or directory path")
    files_get_parser.add_argument(
        "local",
        nargs="?",
        default=".",
        help="Local destination path (default: current directory)",
    )
    files_get_parser.add_argument(
        "--chunk-size",
        dest="chunk_size",
        help="Read chunk size (e.g. '100M', '1G', default: from config or 100M)",
    )
    files_get_parser.add_argument(
        "--method",
        choices=["http", "sftp"],
        default=None,
        help="Transfer method: http (default via API) or sftp",
    )

    # compress (kept as utility)
    files_compress_parser = files_subparsers.add_parser(
        "compress", help="Compress remote directory"
    )
    files_compress_parser.add_argument("source", help="Source remote directory path")
    files_compress_parser.add_argument("target", help="Target archive file full path")

    # uncompress (kept as utility)
    files_uncompress_parser = files_subparsers.add_parser(
        "uncompress", help="Uncompress remote archive"
    )
    files_uncompress_parser.add_argument("archive", help="Archive file full path")
    files_uncompress_parser.add_argument("dest", help="Destination remote directory")
    files_uncompress_parser.add_argument("--password", help="Archive password")

    # conf
    files_conf_parser = files_subparsers.add_parser(
        "conf", help="File confidentiality operations"
    )
    files_conf_parser.add_argument(
        "--get-levels",
        action="store_true",
        dest="get_levels",
        help="Get available confidentiality levels",
    )
    files_conf_parser.add_argument(
        "--set",
        nargs=2,
        metavar=("PATH", "LEVEL"),
        dest="set_conf",
        help="Set file confidentiality level",
    )

    # cat — view remote text file content
    files_cat_parser = files_subparsers.add_parser(
        "cat", help="View remote text file content (SFTP only)"
    )
    files_cat_parser.add_argument("path", help="Remote file path")
    files_cat_parser.add_argument(
        "--head",
        type=int,
        default=None,
        help="Number of lines from the beginning",
    )
    files_cat_parser.add_argument(
        "--tail",
        type=int,
        default=None,
        help="Number of lines from the end",
    )
    files_cat_parser.add_argument(
        "--lines",
        default=None,
        help="Line range (1-based, inclusive), e.g. '10-20' or '10-' (from 10 to EOF)",
    )
    files_cat_parser.add_argument(
        "--start",
        type=int,
        default=None,
        help="Start line number (1-based, inclusive)",
    )
    files_cat_parser.add_argument(
        "--end",
        type=int,
        default=None,
        help="End line number (1-based, inclusive)",
    )
    files_cat_parser.add_argument(
        "--all",
        action="store_true",
        dest="all_lines",
        help="Output all lines (including large files)",
    )
    files_cat_parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Text encoding (default: utf-8)",
    )

    # Apps
    apps_parser = subparsers.add_parser("apps", help="Application operations")
    apps_subparsers = apps_parser.add_subparsers(
        dest="apps_command", help="Apps commands"
    )
    apps_subparsers.add_parser("list", help="List all applications (6.0+)")
    apps_subparsers.add_parser("list-v2", help="List available apps v2 (6.6+)")

    # Departments
    departments_parser = subparsers.add_parser(
        "departments", help="Department operations"
    )
    departments_subparsers = departments_parser.add_subparsers(
        dest="departments_command", help="Departments commands"
    )
    departments_subparsers.add_parser("list", help="List departments (tree)")

    departments_create_parser = departments_subparsers.add_parser(
        "create", help="Create department"
    )
    departments_create_parser.add_argument(
        "--name", required=True, help="Department name (English, e.g. IT)"
    )
    departments_create_parser.add_argument(
        "--display-name",
        required=True,
        dest="display_name",
        help="Department Chinese name (e.g. IT部门)",
    )
    departments_create_parser.add_argument(
        "--parent", required=True, help="Parent department name"
    )
    departments_create_parser.add_argument(
        "--description", help="Department description"
    )

    departments_update_parser = departments_subparsers.add_parser(
        "update", help="Update department"
    )
    departments_update_parser.add_argument(
        "--name", required=True, help="Department name to update (English name)"
    )
    departments_update_parser.add_argument(
        "--display-name", dest="display_name", help="New Chinese name (depNameCN)"
    )
    departments_update_parser.add_argument(
        "--parent", help="New parent department name"
    )
    departments_update_parser.add_argument("--description", help="New description")

    departments_delete_parser = departments_subparsers.add_parser(
        "delete", help="Delete department"
    )
    departments_delete_parser.add_argument(
        "--name", required=True, help="Department name to delete (English name)"
    )

    # Users
    users_parser = subparsers.add_parser("users", help="User operations")
    users_subparsers = users_parser.add_subparsers(
        dest="users_command", help="Users commands"
    )
    users_list_parser = users_subparsers.add_parser("list", help="List users")
    users_list_parser.add_argument("--page", type=int, default=1, help="Page number")
    users_list_parser.add_argument(
        "--page-size", type=int, default=20, help="Page size"
    )
    users_list_parser.add_argument("--dep", help="Filter by department")
    users_list_parser.add_argument(
        "--filter-username", dest="filter_username", help="Filter by username"
    )

    users_create_parser = users_subparsers.add_parser("create", help="Create user")
    users_create_parser.add_argument(
        "--user", required=True, dest="new_username", help="Username (English)"
    )
    users_create_parser.add_argument(
        "--display-name", required=True, dest="display_name", help="Display name"
    )
    users_create_parser.add_argument(
        "--new-password", required=True, dest="new_password", help="Password"
    )
    users_create_parser.add_argument("--dep", help="Department name")
    users_create_parser.add_argument("--phone", help="Phone number")
    users_create_parser.add_argument("--mail", help="Email address")
    users_create_parser.add_argument("--card", help="ID card number")

    users_update_parser = users_subparsers.add_parser("update", help="Update user")
    users_update_parser.add_argument(
        "--user", required=True, dest="target_username", help="Username to update"
    )
    users_update_parser.add_argument(
        "--display-name", dest="display_name", help="New display name"
    )
    users_update_parser.add_argument("--dep", help="New department")
    users_update_parser.add_argument("--phone", help="New phone number")
    users_update_parser.add_argument("--mail", help="New email address")
    users_update_parser.add_argument("--card", help="New ID card number")

    users_delete_parser = users_subparsers.add_parser("delete", help="Delete user")
    users_delete_parser.add_argument(
        "--user", required=True, dest="target_username", help="Username to delete"
    )

    users_reset_parser = users_subparsers.add_parser(
        "reset-password", help="Reset user password"
    )
    users_reset_parser.add_argument(
        "--user", required=True, dest="target_username", help="Username"
    )
    users_reset_parser.add_argument(
        "--new-password", required=True, dest="new_password", help="New password"
    )

    return parser


# ---------------------------------------------------------------------------
# Job submit: dynamic parser per application
# ---------------------------------------------------------------------------


def _resolve_profile_config(args: argparse.Namespace) -> Optional[str]:
    profile_config = getattr(args, "profile_config", None)
    if not profile_config:
        cfg = Config(config_file=getattr(args, "config_file", None))
        profile_config = cfg.job_profile_config
    return profile_config


def _load_pm(args):
    from .job_profiles import JobProfileManager

    return JobProfileManager(config_file=_resolve_profile_config(args))


def _build_submit_parser(pm, app_id, profile, supported):
    """Build a full argparse parser with app-specific parameters."""
    p = argparse.ArgumentParser(
        prog=f"appform jobs submit -a {app_id}",
        description=f"Universal job submission tool for Appform SDK.",
        formatter_class=_SubmitHelpFormatter,
        epilog=_build_epilog(pm, app_id, profile, supported),
    )

    p.add_argument(
        "-a",
        "--app",
        choices=supported,
        default=app_id,
        metavar="{" + ",".join(supported) + "}",
        help="Select application type",
    )
    p.add_argument(
        "-l",
        "--list-apps",
        action="store_true",
        dest="list_apps",
        help="List all supported applications",
    )
    p.add_argument(
        "--set",
        action="append",
        dest="set_params",
        metavar="KEY=VALUE",
        help="Override any JH_* parameter (repeatable)",
    )
    p.add_argument(
        "--params", dest="json_params", help="Override parameters as JSON string"
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Only show final parameters, do not submit",
    )

    required_params = [x for x in profile.parameters if x.required]
    optional_params = [x for x in profile.parameters if not x.required]

    if required_params:
        group = p.add_argument_group(f"{profile.name} required parameters")
        _add_params_to_group(group, required_params)
    if optional_params:
        group = p.add_argument_group(f"{profile.name} optional parameters")
        _add_params_to_group(group, optional_params)

    return p


def _add_params_to_group(group, params):
    """Add ParameterDef objects as argparse arguments."""
    for pd in params:
        arg_options = []
        if pd.short_arg:
            arg_options.append(f"-{pd.short_arg}")
        arg_options.append(f"--{pd.effective_cli_name}")

        help_text = pd.description
        if pd.default:
            help_text += f" (default: {pd.default})"
        if pd.required:
            help_text += " [REQUIRED]"

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
        else:
            kwargs["metavar"] = metavar

        group.add_argument(*arg_options, **kwargs)


def _build_epilog(pm, app_id, profile, supported):
    """Build help epilog text."""
    lines = []
    lines.append(f"Supported applications: {', '.join(supported)}")
    lines.append("")
    lines.append("Usage examples:")
    lines.append(f"  appform jobs submit -a {app_id} -i /path/to/file.sim --ncpu 8")
    lines.append(
        f"  appform jobs submit -a {app_id} --set JH_CAS=/path/to/file --set JH_NCPU=8"
    )
    lines.append(f"  appform jobs submit -a {app_id} --dry-run -i /path/to/file.sim")
    lines.append(
        f"  appform jobs submit -l                                     # list apps"
    )
    lines.append(
        f"  appform jobs submit -a {app_id} --help                     # this help"
    )
    lines.append("")

    required = profile.get_required_params()
    if required:
        lines.append(f"{profile.name} required parameters:")
        for pd in required:
            if pd.cli_arg and pd.short_arg:
                arg_str = f"  -{pd.short_arg}, --{pd.cli_arg}"
            elif pd.cli_arg:
                arg_str = f"  --{pd.cli_arg}"
            elif pd.short_arg:
                arg_str = f"  -{pd.short_arg}, --{pd.effective_cli_name}"
            else:
                arg_str = f"  --{pd.effective_cli_name}"
            lines.append(f"{arg_str:<30} {pd.description}")
        lines.append("")

    return "\n".join(lines)


def _handle_jobs_submit(pm, raw_args, output_format):
    """
    Full handler for ``appform jobs submit``.

    Two-pass parsing:
      Pass 1 (quick): extract -a/-l from raw_args
      Pass 2 (full):  build per-app parser, parse everything including --help
    """
    supported = [a["app_id"] for a in pm.list_apps()]
    disk_mapping = _resolve_disk_mapping(pm)

    # --- Pass 1: quick pre-parse ---
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("-a", "--app", dest="_app", default=None)
    pre.add_argument("-l", "--list-apps", dest="_list_apps", action="store_true")
    pre_args, _ = pre.parse_known_args(raw_args)

    # -l: list apps
    if pre_args._list_apps:
        apps = pm.list_apps()
        if output_format == "json":
            print(
                json.dumps(
                    {"applications": apps, "config_file": pm.config_file},
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            _print_apps_table(apps)
            if pm.config_file:
                print(f"\nConfig: {pm.config_file}")
            if disk_mapping:
                print("\nWindows path mapping:")
                for drive, path in disk_mapping.items():
                    print(f"  {drive} -> {path}")
        return

    app_id = pre_args._app

    if not app_id:
        # No -a given: show generic submit help
        print(f"Supported applications: {', '.join(supported)}")
        print(f"\nUsage:")
        print(
            f"  appform jobs submit -a <app> [options]   # Submit with app-specific args"
        )
        print(f"  appform jobs submit -l                   # List all applications")
        print(f"  appform jobs submit -a <app> --help      # Show app-specific help")
        if disk_mapping:
            print("\nWindows path mapping:")
            for drive, path in disk_mapping.items():
                print(f"  {drive} -> {path}")
        return

    # --- Resolve profile ---
    profile = pm.get_profile(app_id)
    if not profile:
        print(
            f"Error: Unknown application '{app_id}'. Available: {', '.join(supported)}",
            file=sys.stderr,
        )
        sys.exit(1)

    # --- Pass 2: build full parser and parse ---
    full_parser = _build_submit_parser(pm, app_id, profile, supported)
    try:
        parsed = full_parser.parse_args(raw_args)
    except SystemExit:
        return  # --help triggered exit, or parse error

    if parsed.list_apps:
        apps = pm.list_apps()
        if output_format == "json":
            print(
                json.dumps(
                    {"applications": apps, "config_file": pm.config_file},
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            _print_apps_table(apps)
            if disk_mapping:
                print("\nWindows path mapping:")
                for drive, path in disk_mapping.items():
                    print(f"  {drive} -> {path}")
        return

    # --- Collect overrides ---
    overrides = {}
    for pd in profile.parameters:
        attr = f"param_{pd.effective_cli_name.replace('-', '_')}"
        val = getattr(parsed, attr, None)
        if val is not None:
            if pd.param_type == "switch":
                overrides[pd.name] = str(val)
            elif val not in (None, ""):
                overrides[pd.name] = str(val)

    if parsed.set_params:
        for item in parsed.set_params:
            if "=" not in item:
                print(
                    f"Error: Invalid format '{item}'. Expected KEY=VALUE.",
                    file=sys.stderr,
                )
                sys.exit(1)
            k, v = item.split("=", 1)
            overrides[k] = v

    if parsed.json_params:
        overrides.update(json.loads(parsed.json_params))

    # --- Windows path conversion ---
    overrides = _apply_path_conversion(overrides, disk_mapping)

    # --- Build params ---
    try:
        params = pm.build_submit_params(app_id, overrides)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Dry run ---
    if parsed.dry_run:
        print(f"Application: {app_id} ({profile.name})")
        print(f"Parameters:")
        print(json.dumps(params, indent=2, ensure_ascii=False))
        return

    # --- Submit ---
    return app_id, params


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _print_apps_table(apps):
    print(f"{'App ID':<25} {'Name':<25} Description")
    print("-" * 80)
    for app in apps:
        print(f"{app['app_id']:<25} {app['name']:<25} {app['description']}")


def _print_app_params(profile):
    print(f"Application: {profile.app_id} - {profile.name}")
    if profile.description:
        print(f"Description: {profile.description}")
    print()
    print(
        f"{'Parameter':<25} {'Type':<8} {'Required':<8} {'Default':<12} {'CLI Arg':<12} {'Short':<6} Description"
    )
    print("-" * 110)
    for p in profile.parameters:
        req = "Yes" if p.required else ""
        default = p.default or ""
        cli = p.cli_arg or p.effective_cli_name
        short = f"-{p.short_arg}" if p.short_arg else ""
        print(
            f"{p.name:<25} {p.param_type:<8} {req:<8} {default:<12} {cli:<12} {short:<6} {p.description}"
        )

    required = profile.get_required_params()
    if required:
        example_parts = []
        for p in required:
            if p.cli_arg:
                example_parts.append(f"--{p.cli_arg} VALUE")
            elif p.short_arg:
                example_parts.append(f"-{p.short_arg} VALUE")
            else:
                name = p.name.lower().replace("jh_", "").replace("_", "-")
                example_parts.append(f"--{name} VALUE")
        print(f"\nUsage example:")
        print(f"  appform jobs submit -a {profile.app_id} {' '.join(example_parts)}")
        print(
            f"  appform jobs submit -a {profile.app_id} --set JH_CAS=/path/to/file --set JH_NCPU=8"
        )


def _remote_file_exists(client, remote_dir: str, filename: str) -> bool:
    """Check if a file already exists in the remote directory."""
    try:
        result = client.files.list(path=remote_dir, page=1, page_size=1000)
        data = result.get("data", [])
        if isinstance(data, dict):
            items = data.get("files", data.get("records", []))
        elif isinstance(data, list):
            items = data
        else:
            items = []
        for item in items:
            if item.get("fileName") == filename:
                return True
    except Exception:
        pass
    return False


def _confirm_overwrite(filename: str) -> bool:
    """Ask user to confirm file overwrite."""
    try:
        answer = input(f"Remote file '{filename}' already exists. Overwrite? [y/N] ")
        return answer.strip().lower() in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def _resolve_output_format(args: argparse.Namespace) -> str:
    """Resolve output format: CLI arg > env var / config file > default (table)."""
    output = getattr(args, "output", None)
    if output:
        return output
    cfg = Config(config_file=getattr(args, "config_file", None))
    return cfg.output_format or "table"


def create_client(args: argparse.Namespace) -> AppformClient:
    config = Config(
        base_url=args.base_url,
        access_key=args.access_key,
        access_key_secret=args.access_key_secret,
        username=getattr(args, "auth_username", None),
        password=getattr(args, "auth_password", None),
        token=args.token,
        api_version=args.api_version,
        extensions_dir=args.extensions_dir,
        config_file=args.config_file,
    )

    if not config.base_url:
        print(
            "Error: base_url is required. Set --base-url or APPFORM_BASE_URL environment variable.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Auto-authenticate: AccessKey > token > password login
    if config.access_key and config.access_key_secret:
        client = AppformClient(
            base_url=config.base_url,
            access_key=config.access_key,
            access_key_secret=config.access_key_secret,
            username=config.username,
            api_version=config.api_version,
            extensions_dir=config.extensions_dir,
            timeout=config.timeout,
            verify_ssl=config.verify_ssl,
            config=config,
        )
    elif config.token:
        client = AppformClient(
            base_url=config.base_url,
            token=config.token,
            api_version=config.api_version,
            extensions_dir=config.extensions_dir,
            timeout=config.timeout,
            verify_ssl=config.verify_ssl,
            config=config,
        )
    else:
        client = AppformClient(
            base_url=config.base_url,
            api_version=config.api_version,
            extensions_dir=config.extensions_dir,
            timeout=config.timeout,
            verify_ssl=config.verify_ssl,
            config=config,
        )
        # Password login if credentials available
        if config.username and config.password:
            result = client.auth.login(config.username, config.password)
            if result.get("result") != "success":
                msg = result.get("message", "Unknown error")
                print(
                    f"Error: Login failed for '{config.username}': {msg}",
                    file=sys.stderr,
                )
                client.close()
                sys.exit(1)

    return client


def output_result(result: dict, output_format: str, command: str = ""):
    """Output result using formatters."""
    print(format_output(command, result, output_format))


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def handle_config_command(args: argparse.Namespace):
    if args.config_command == "set":
        config_file = getattr(args, "config_file", None)
        cs = getattr(args, "chunk_size", None)
        if cs and not isinstance(cs, int):
            from .files import parse_size

            cs = parse_size(cs)
        Config.save_config_file(
            base_url=args.base_url,
            access_key=args.access_key,
            access_key_secret=args.access_key_secret,
            username=args.username,
            password=getattr(args, "password", None),
            token=args.token,
            timeout=args.timeout,
            verify_ssl=args.verify_ssl,
            api_version=args.api_version,
            extensions_dir=args.extensions_dir,
            job_profile_config=getattr(args, "job_profile_config", None),
            output_format=getattr(args, "output_format", None),
            output_template=getattr(args, "output_template", None),
            default_remote_path=getattr(args, "default_remote_path", None),
            chunk_size=cs,
            default_method=getattr(args, "default_method", None),
            config_file=config_file,
            sftp_host=getattr(args, "sftp_host", None),
            sftp_port=getattr(args, "sftp_port", None),
            sftp_username=getattr(args, "sftp_username", None),
            sftp_password=getattr(args, "sftp_password", None),
            sftp_key_file=getattr(args, "sftp_key_file", None),
            sftp_key_password=getattr(args, "sftp_key_password", None),
        )
        config_path = config_file or Config.get_default_config_path()
        print(f"Configuration saved to {config_path}")
    elif args.config_command == "show":
        config = Config(config_file=getattr(args, "config_file", None))
        output_result(config.to_dict(), args.output)


def handle_extension_command(args: argparse.Namespace):
    if args.extension_command == "list":
        client = create_client(args)
        extensions = client.extension_manager.list_extensions()
        output_result({"extensions": extensions}, args.output)
        client.close()
    elif args.extension_command == "load":
        client = create_client(args)
        client.load_extension_file(args.file)
        print(f"Extension loaded from {args.file}")
        client.close()


def handle_endpoint_command(args: argparse.Namespace):
    client = create_client(args)
    if args.endpoint_command == "list":
        version = getattr(args, "version", None)
        if version:
            endpoints = client.registry.get_for_version(version)
        else:
            endpoints = client.registry.get_all()
        output_result(
            {
                "endpoints": {
                    k: {"path": v.path, "method": v.method}
                    for k, v in endpoints.items()
                }
            },
            args.output,
        )
    elif args.endpoint_command == "call":
        params = json.loads(args.params) if args.params else None
        data = json.loads(args.data) if args.data else None
        path_params = json.loads(args.path_params) if args.path_params else None
        result = client.call_endpoint(
            args.name, path_params=path_params, params=params, json_data=data
        )
        output_result(result, args.output)
    client.close()


def handle_auth_command(args: argparse.Namespace):
    client = create_client(args)
    if args.auth_command == "login":
        result = client.auth.login(username=args.username, password=args.password)
        output_result(result, args.output)
    elif args.auth_command == "ping":
        result = client.auth.ping()
        output_result(result, args.output)
    elif args.auth_command == "logout":
        result = client.auth.logout()
        output_result(result, args.output)
    client.close()


def handle_jobs_command(args: argparse.Namespace, submit_extra_args=None):
    # --- Commands that don't need API client ---
    if args.jobs_command in ("apps", "params", "submit"):
        pm = _load_pm(args)

        if args.jobs_command == "apps":
            apps = pm.list_apps()
            if args.output == "json":
                output_result(
                    {"applications": apps, "config_file": pm.config_file}, args.output
                )
            else:
                _print_apps_table(apps)
                if pm.config_file:
                    print(f"\nConfig: {pm.config_file}")
            return

        elif args.jobs_command == "params":
            profile = pm.get_profile(args.app_id)
            if not profile:
                available = [a["app_id"] for a in pm.list_apps()]
                print(
                    f"Error: Unknown application '{args.app_id}'. Available: {', '.join(available)}",
                    file=sys.stderr,
                )
                sys.exit(1)
            if args.output == "json":
                output_result(profile.to_dict(), args.output)
            else:
                _print_app_params(profile)
            return

        elif args.jobs_command == "submit":
            result = _handle_jobs_submit(pm, submit_extra_args or [], args.output)
            if result is None:
                return  # dry-run, list-apps, or help was shown
            app_id, params = result
            client = create_client(args)
            resp = client.jobs.submit(app_id=app_id, params=params)
            output_result(resp, args.output)
            client.close()
            return

    # --- Commands that need API client ---
    client = create_client(args)

    if args.jobs_command == "submit-raw":
        params = json.loads(args.params)
        result = client.jobs.submit(app_id=args.app_id, params=params)
        output_result(result, args.output, "jobs.submit")
    elif args.jobs_command == "list":
        status_filter = [args.status] if args.status else None
        result = client.jobs.list_jobs(
            page=args.page,
            page_size=args.page_size,
            name_filter=args.name,
            status_filter=status_filter,
        )
        output_result(result, args.output, "jobs.list")
    elif args.jobs_command == "status":
        if args.status and args.status.lower() != "all":
            status_filter = [args.status.upper()]
        else:
            status_filter = None
        result = client.jobs.list_jobs(
            page=args.page,
            page_size=args.page_size,
            status_filter=status_filter,
        )
        output_result(result, args.output, "jobs.list")
    elif args.jobs_command == "get":
        result = client.jobs.get_job(args.job_id)
        output_result(result, args.output, "jobs.get")
    elif args.jobs_command == "stop":
        result = client.jobs.stop(args.job_id)
        output_result(result, args.output, "jobs.action")
    elif args.jobs_command == "suspend":
        result = client.jobs.suspend(args.job_id)
        output_result(result, args.output, "jobs.action")
    elif args.jobs_command == "resume":
        result = client.jobs.resume(args.job_id)
        output_result(result, args.output, "jobs.action")
    elif args.jobs_command == "output":
        result = client.jobs.get_output(args.job_id)
        output_result(result, args.output, "jobs.output")
    elif args.jobs_command == "files":
        result = client.jobs.get_files(args.job_id)
        output_result(result, args.output, "jobs.files")
    elif args.jobs_command == "history":
        result = client.jobs.get_history(args.job_id)
        output_result(result, args.output, "jobs.history")
    elif args.jobs_command == "history-page":
        result = client.jobs.list_history(page=args.page, page_size=args.page_size)
        output_result(result, args.output, "jobs.list")
    elif args.jobs_command == "delete":
        result = client.jobs.delete_job(args.job_id)
        output_result(result, args.output, "jobs.delete")
    elif args.jobs_command == "form":
        result = client.jobs.get_form(args.app_id)
        output_result(result, args.output, "jobs.form")
    elif args.jobs_command == "tooltip":
        result = client.jobs.get_tooltip()
        output_result(result, args.output, "jobs.tooltip")

    client.close()


def handle_sessions_command(args: argparse.Namespace):
    client = create_client(args)
    if args.sessions_command == "start":
        result = client.sessions.start(
            app_id=args.app_id,
            start_new=getattr(args, "start_new", None),
            cwd=getattr(args, "cwd", None),
            work_file=getattr(args, "work_file", None),
            param=getattr(args, "param", None),
        )
        output_result(result, args.output, "sessions.start")
    elif args.sessions_command == "list":
        session_ids = getattr(args, "session_ids", None)
        session_name = getattr(args, "session_name", None)
        if session_ids:
            session_ids = session_ids.split(",")
        result = client.sessions.list(
            session_ids=session_ids, session_name=session_name
        )
        output_result(result, args.output, "sessions.list")
    elif args.sessions_command == "list-all":
        result = client.sessions.list_all(
            page=getattr(args, "page", 1), page_size=getattr(args, "page_size", 20)
        )
        output_result(result, args.output, "sessions.list-all")
    elif args.sessions_command == "connect":
        result = client.sessions.connect(args.session_id)
        output_result(result, args.output, "sessions.connect")
    elif args.sessions_command == "connect-launch":
        result = client.sessions.connect_and_launch(args.session_id)
        output_result(result, args.output, "sessions.connect")
    elif args.sessions_command == "disconnect":
        result = client.sessions.disconnect(args.session_id)
        output_result(result, args.output, "sessions.disconnect")
    elif args.sessions_command == "close":
        result = client.sessions.close(args.session_id)
        output_result(result, args.output, "sessions.close")
    elif args.sessions_command == "share":
        usernames = args.usernames.split(",")
        result = client.sessions.share(session_id=args.session_id, usernames=usernames)
        output_result(result, args.output, "sessions.share")
    client.close()


def _is_remote_path(path: str) -> bool:
    """Check if a path is remote (starts with /)."""
    return path.startswith("/")


def _resolve_remote_path(path: str, config: Config) -> str:
    """Resolve a path to a full remote path using default_remote_path if needed."""
    if _is_remote_path(path):
        return path
    default_remote = config.default_remote_path or "/"
    return f"{default_remote.rstrip('/')}/{path}"


def handle_files_command(args: argparse.Namespace):
    client = create_client(args)
    config = Config(config_file=getattr(args, "config_file", None))

    try:
        method = getattr(args, "default_method", None) or config.default_method or "http"

        try:
            if args.files_command == "ls":
                cmd_method = getattr(args, "method", None) or method
                if args.list_all:
                    items = client.files.list_all(path=args.path, transfer_method=cmd_method)
                    result = {"data": items, "path": args.path, "count": len(items)}
                else:
                    result = client.files.list(
                        path=args.path, page=args.page, page_size=args.page_size, transfer_method=cmd_method
                    )
                output_result(result, args.output, "files.list")

            elif args.files_command == "cp":
                cmd_method = getattr(args, "method", None) or method
                result = client.files.copy(src_path=args.src, dest_dir=args.dest, transfer_method=cmd_method)
                output_result(result, args.output, "files.copy")

            elif args.files_command == "mv":
                cmd_method = getattr(args, "method", None) or method
                result = client.files.move(src_path=args.src, dest_dir=args.dest, transfer_method=cmd_method)
                output_result(result, args.output, "files.rename")

            elif args.files_command == "rm":
                cmd_method = getattr(args, "method", None) or method
                result = client.files.delete(path=args.path, transfer_method=cmd_method)
                output_result(result, args.output, "files.delete")

            elif args.files_command == "mkdir":
                force = not args.no_force
                cmd_method = getattr(args, "method", None) or method
                result = client.files.mkdir(path=args.path, force=force, transfer_method=cmd_method)
                output_result(result, args.output, "files.mkdir")

            elif args.files_command == "put":
                local = args.local
                remote = args.remote
                force = getattr(args, "force", False)
                cmd_method = getattr(args, "method", None) or method
                if remote is None:
                    remote = config.default_remote_path or "/"
                remote = _resolve_remote_path(remote, config)

                local_path = Path(local)
                cs_arg = getattr(args, "chunk_size", None)
                if cs_arg:
                    from .files import parse_size

                    chunk_size = parse_size(cs_arg)
                else:
                    chunk_size = config.chunk_size or 104857600
                if local_path.is_dir():
                    from .files import _ProgressTracker

                    progress = _ProgressTracker(label="Uploading")
                    if cmd_method == "sftp":
                        results = client.files.upload_directory(
                            local_dir=local,
                            remote_dir=remote,
                            on_progress=progress.update,
                            chunk_size=chunk_size,
                            transfer_method=cmd_method,
                        )
                    else:
                        results = client.files.upload_directory(
                            local_dir=local,
                            remote_dir=remote,
                            on_progress=progress.update,
                            check_exists=lambda fname: _remote_file_exists(
                                client, remote, fname
                            )
                            and not force,
                            confirm=_confirm_overwrite,
                            chunk_size=chunk_size,
                            transfer_method=cmd_method,
                        )
                    progress.finish()
                    uploaded = [r for r in results if r.get("result")]
                    print(f"Uploaded {len(uploaded)} file(s) to {remote}")
                    if args.output == "json":
                        output_result(
                            {
                                "uploaded": results,
                                "count": len(uploaded),
                                "remote_dir": remote,
                            },
                            args.output,
                            "files.upload",
                        )
                elif local_path.is_file():
                    fname = local_path.name
                    saved = f"{remote.rstrip('/')}/{fname}"
                    if cmd_method == "http" and not force and _remote_file_exists(client, remote, fname):
                        if not _confirm_overwrite(fname):
                            print("Upload cancelled.")
                            client.close()
                            return
                    from .files import _ProgressTracker

                    progress = _ProgressTracker(label="Uploading")
                    result = client.files.upload(
                        file_path=local,
                        remote_path=remote,
                        on_progress=progress.update,
                        chunk_size=chunk_size,
                        transfer_method=cmd_method,
                    )
                    progress.finish()
                    print(f"Uploaded to {saved}")
                    if args.output == "json":
                        output_result(result, args.output, "files.upload")
                else:
                    print(f"Error: Local path not found: {local}", file=sys.stderr)
                    client.close()
                    sys.exit(1)

            elif args.files_command == "get":
                remote = args.remote
                local = args.local
                cmd_method = getattr(args, "method", None) or method
                cs_arg = getattr(args, "chunk_size", None)
                if cs_arg:
                    from .files import parse_size

                    chunk_size = parse_size(cs_arg)
                else:
                    chunk_size = config.chunk_size or 104857600

                # Check if remote path is a directory by listing it
                is_dir = False
                if cmd_method == "http":
                    try:
                        items = client.files.list(path=remote, page=1, page_size=1)
                        data = items.get("data", [])
                        if isinstance(data, dict):
                            file_list = data.get("files", data.get("records", []))
                        elif isinstance(data, list):
                            file_list = data
                        else:
                            file_list = []

                        is_dir = len(file_list) > 0
                    except Exception:
                        is_dir = False
                else:
                    is_dir = remote.endswith("/")

                if is_dir:
                    from .files import _ProgressTracker

                    local_path = Path(local)
                    save_dir = local_path if local_path.is_dir() else Path(local)
                    progress = _ProgressTracker(label="Downloading")
                    results = client.files.download_directory(
                        remote_dir=remote,
                        local_dir=str(save_dir),
                        on_progress=progress.update,
                        chunk_size=chunk_size,
                        transfer_method=cmd_method,
                    )
                    progress.finish()
                    downloaded = [r for r in results if r.get("status") == "ok"]
                    print(f"Downloaded {len(downloaded)} file(s) to {save_dir}")
                    if args.output == "json":
                        output_result(
                            {
                                "downloaded": results,
                                "count": len(downloaded),
                                "local_dir": str(save_dir),
                            },
                            args.output,
                            "files.download",
                        )
                else:
                    local_path = Path(local)
                    if local_path.is_dir() or local == ".":
                        save_path = str(local_path / Path(remote).name)
                    else:
                        save_path = local
                    from .files import _ProgressTracker

                    progress = _ProgressTracker(label="Downloading")
                    client.files.download(
                        remote_path=remote,
                        local_path=save_path,
                        on_progress=progress.update,
                        chunk_size=chunk_size,
                        transfer_method=cmd_method,
                    )
                    progress.finish()
                    print(f"Downloaded to {save_path}")

            elif args.files_command == "compress":
                result = client.files.compress(
                    source_dir=args.source, target_path=args.target
                )
                output_result(result, args.output, "files.compress")

            elif args.files_command == "uncompress":
                result = client.files.uncompress(
                    archive_path=args.archive, dest_dir=args.dest, password=args.password
                )
                output_result(result, args.output, "files.uncompress")

            elif args.files_command == "conf":
                if args.get_levels:
                    result = client.files.get_confidentiality_levels()
                    output_result(result, args.output, "files.conf")
                elif args.set_conf:
                    result = client.files.set_confidentiality(
                        path=args.set_conf[0], level=args.set_conf[1]
                    )
                    output_result(result, args.output, "files.conf")

            elif args.files_command == "cat":
                # Resolve line range from --lines if provided
                head = args.head
                tail = args.tail
                start = args.start
                end = args.end
                all_lines = getattr(args, "all_lines", False)

                if args.lines:
                    parts = args.lines.split("-", 1)
                    if len(parts) == 2:
                        if parts[0]:
                            start = int(parts[0])
                        if parts[1]:
                            end = int(parts[1])
                        else:
                            end = None  # to EOF
                    elif len(parts) == 1:
                        start = int(parts[0])

                lines = client.files.cat(
                    remote_path=args.path,
                    head=head,
                    tail=tail,
                    start=start,
                    end=end,
                    encoding=args.encoding,
                    all_lines=all_lines,
                )
                for line in lines:
                    print(line)

        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            client.close()
            sys.exit(1)
        except Exception as e:
            msg = str(e)
            print(f"Error: {msg}", file=sys.stderr)
            client.close()
            sys.exit(1)
    finally:
        client.close()


def handle_apps_command(args: argparse.Namespace):
    client = create_client(args)
    if args.apps_command == "list":
        result = client.apps.list_all()
        output_result(result, args.output, "apps.list")
    elif args.apps_command == "list-v2":
        result = client.apps.list_v2()
        output_result(result, args.output, "apps.list")
    client.close()


def handle_departments_command(args: argparse.Namespace):
    client = create_client(args)
    try:
        if args.departments_command == "list":
            result = client.organization.get_departments()
            output_result(result, args.output, "departments.list")
        elif args.departments_command == "create":
            result = client.organization.create_department(
                dep_name=args.name,
                dep_chname=args.display_name,
                parent_dep=args.parent,
                description=args.description,
            )
            output_result(result, args.output)
        elif args.departments_command == "update":
            result = client.organization.update_department(
                dep_name=args.name,
                dep_chname=args.display_name,
                parent_dep=args.parent,
                description=args.description,
            )
            output_result(result, args.output)
        elif args.departments_command == "delete":
            result = client.organization.delete_department(dep_name=args.name)
            output_result(result, args.output)
    finally:
        client.close()


def handle_users_command(args: argparse.Namespace):
    client = create_client(args)
    try:
        if args.users_command == "list":
            result = client.organization.get_users(
                page=args.page,
                page_size=args.page_size,
                dep=getattr(args, "dep", None),
                username=getattr(args, "filter_username", None),
            )
            output_result(result, args.output, "users.list")
        elif args.users_command == "create":
            result = client.organization.create_user(
                username=args.new_username,
                chusername=args.display_name,
                password=args.new_password,
                dep=getattr(args, "dep", None),
                phone=getattr(args, "phone", None),
                mail=getattr(args, "mail", None),
                card=getattr(args, "card", None),
            )
            output_result(result, args.output)
        elif args.users_command == "update":
            result = client.organization.update_user(
                username=args.target_username,
                chusername=getattr(args, "display_name", None),
                dep=getattr(args, "dep", None),
                phone=getattr(args, "phone", None),
                mail=getattr(args, "mail", None),
                card=getattr(args, "card", None),
            )
            output_result(result, args.output)
        elif args.users_command == "delete":
            result = client.organization.delete_user(username=args.target_username)
            output_result(result, args.output)
        elif args.users_command == "reset-password":
            result = client.organization.reset_password(
                username=args.target_username,
                new_password=args.new_password,
            )
            output_result(result, args.output)
    finally:
        client.close()


def main(args: Optional[list] = None):
    """Main entry point."""
    # Strip --help/-h early so the top-level parse_known_args doesn't consume it
    show_help = False
    raw = list(args) if args else list(sys.argv[1:])
    filtered = []
    for a in raw:
        if a in ("--help", "-h"):
            show_help = True
        else:
            filtered.append(a)

    parser = create_parser()

    if show_help:
        parser.parse_args(raw)
        return

    parsed_args, remaining = parser.parse_known_args(filtered)

    # Generate shell completion
    if parsed_args.generate_completion:
        script = _get_completion_script(parsed_args.generate_completion)
        if script:
            print(script)
        else:
            print(
                f"Error: No completion script available for '{parsed_args.generate_completion}'",
                file=sys.stderr,
            )
            sys.exit(1)
        return

    if not parsed_args.command:
        parser.print_help()
        sys.exit(0)

    # Resolve output format: CLI arg > env var / config > default
    parsed_args.output = _resolve_output_format(parsed_args)

    # Load output template if specified
    from .formatters import load_templates, resolve_template_file

    cfg_for_template = Config(config_file=getattr(parsed_args, "config_file", None))
    template_file = resolve_template_file(
        cli_arg=getattr(parsed_args, "output_template", None),
        config=cfg_for_template,
    )
    if template_file:
        try:
            load_templates(template_file)
        except Exception as e:
            print(
                f"Warning: Failed to load template '{template_file}': {e}",
                file=sys.stderr,
            )

    # For jobs submit, forward remaining args + --help if requested
    if parsed_args.command == "jobs" and parsed_args.jobs_command == "submit":
        if show_help:
            remaining.append("--help")
        handle_jobs_command(parsed_args, submit_extra_args=remaining)
        return

    if show_help:
        # Re-parse with --help for other commands
        parser.parse_args(raw)

    if parsed_args.command == "config":
        handle_config_command(parsed_args)
    elif parsed_args.command == "extension":
        handle_extension_command(parsed_args)
    elif parsed_args.command == "endpoint":
        handle_endpoint_command(parsed_args)
    elif parsed_args.command == "auth":
        handle_auth_command(parsed_args)
    elif parsed_args.command == "jobs":
        handle_jobs_command(parsed_args)
    elif parsed_args.command == "sessions":
        handle_sessions_command(parsed_args)
    elif parsed_args.command == "files":
        handle_files_command(parsed_args)
    elif parsed_args.command == "apps":
        handle_apps_command(parsed_args)
    elif parsed_args.command == "departments":
        handle_departments_command(parsed_args)
    elif parsed_args.command == "users":
        handle_users_command(parsed_args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
