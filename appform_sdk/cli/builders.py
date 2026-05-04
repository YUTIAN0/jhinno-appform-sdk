"""Build the argparse parser tree for all CLI commands."""

import argparse

from appform_sdk import __version__
from appform_sdk.cli.common import SubmitHelpFormatter


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

    _add_config_parser(subparsers)
    _add_extension_parser(subparsers)
    _add_endpoint_parser(subparsers)
    _add_auth_parser(subparsers)
    _add_jobs_parser(subparsers)
    _add_sessions_parser(subparsers)
    _add_files_parser(subparsers)
    _add_apps_parser(subparsers)
    _add_departments_parser(subparsers)
    _add_users_parser(subparsers)

    return parser


# ---------------------------------------------------------------------------
# Individual command group parsers
# ---------------------------------------------------------------------------


def _add_config_parser(subparsers):
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


def _add_extension_parser(subparsers):
    ext_parser = subparsers.add_parser("extension", help="Manage extensions")
    ext_subparsers = ext_parser.add_subparsers(
        dest="extension_command", help="Extension commands"
    )
    ext_subparsers.add_parser("list", help="List loaded extensions")
    ext_load_parser = ext_subparsers.add_parser("load", help="Load an extension")
    ext_load_parser.add_argument("file", help="Extension configuration file")


def _add_endpoint_parser(subparsers):
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


def _add_auth_parser(subparsers):
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


def _add_jobs_parser(subparsers):
    jobs_parser = subparsers.add_parser("jobs", help="Job operations")
    jobs_subparsers = jobs_parser.add_subparsers(
        dest="jobs_command", help="Jobs commands"
    )

    jobs_subparsers.add_parser("apps", help="List applications from job profile config")

    jobs_params_parser = jobs_subparsers.add_parser(
        "params", help="Show parameters for an application"
    )
    jobs_params_parser.add_argument("app_id", help="Application ID")

    # Jobs submit — minimal placeholder; real args are built dynamically
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

    # Jobs list/status
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

    for cmd in ("get", "stop", "suspend", "resume", "output", "history", "delete"):
        p = jobs_subparsers.add_parser(cmd, help=f"{cmd.capitalize()} a job")
        p.add_argument("job_id", help="Job ID")

    # Jobs files
    _add_jobs_files_parser(jobs_subparsers)

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


def _add_jobs_files_parser(jobs_subparsers):
    """Add jobs files subcommand with all its nested subcommands."""
    jobs_files_parser = jobs_subparsers.add_parser(
        "files", help="Browse and manage job files"
    )
    jobs_files_parser.add_argument("job_id", help="Job ID")
    jobs_files_parser.add_argument(
        "--method",
        dest="default_method",
        choices=["http", "sftp"],
        default=None,
        help="Default transfer method for all file operations",
    )
    jobs_files_subparsers = jobs_files_parser.add_subparsers(
        dest="jobs_files_command", help="Job file commands"
    )

    # ls
    jf_ls = jobs_files_subparsers.add_parser("ls", help="List directory contents")
    jf_ls.add_argument(
        "path", nargs="?", default=None, help="Directory path (relative to job cwd)"
    )
    jf_ls.add_argument("--page", type=int, default=1, help="Page number")
    jf_ls.add_argument("--page-size", type=int, default=100, help="Page size")
    jf_ls.add_argument(
        "--all", "-a", action="store_true", dest="list_all", help="List all items"
    )
    jf_ls.add_argument(
        "--all-hidden",
        "-A",
        action="store_true",
        dest="hidden",
        help="Show hidden files (starting with .)",
    )
    jf_ls.add_argument(
        "--method", choices=["http", "sftp"], default=None, help="Transfer method"
    )

    # cp
    jf_cp = jobs_files_subparsers.add_parser("cp", help="Copy file or directory")
    jf_cp.add_argument("src", help="Source path")
    jf_cp.add_argument("dest", help="Destination path")
    jf_cp.add_argument(
        "--method", choices=["http", "sftp"], default=None, help="Transfer method"
    )

    # mv
    jf_mv = jobs_files_subparsers.add_parser("mv", help="Move/rename file or directory")
    jf_mv.add_argument("src", help="Source path")
    jf_mv.add_argument("dest", help="Destination path")
    jf_mv.add_argument(
        "--method", choices=["http", "sftp"], default=None, help="Transfer method"
    )

    # rm
    jf_rm = jobs_files_subparsers.add_parser("rm", help="Delete file or directory")
    jf_rm.add_argument("path", help="Path to delete")
    jf_rm.add_argument(
        "--method", choices=["http", "sftp"], default=None, help="Transfer method"
    )

    # mkdir
    jf_mkdir = jobs_files_subparsers.add_parser("mkdir", help="Create directory")
    jf_mkdir.add_argument("path", help="Directory path to create")
    jf_mkdir.add_argument(
        "--no-force", action="store_true", dest="no_force", help="Fail if exists"
    )
    jf_mkdir.add_argument(
        "--method", choices=["http", "sftp"], default=None, help="Transfer method"
    )

    # put
    jf_put = jobs_files_subparsers.add_parser(
        "put", help="Upload local file or directory to job directory"
    )
    jf_put.add_argument("local", help="Local file or directory path")
    jf_put.add_argument(
        "remote",
        nargs="?",
        default=None,
        help="Remote path within job directory (default: job cwd)",
    )
    jf_put.add_argument(
        "-f", "--force", action="store_true", help="Overwrite without confirmation"
    )
    jf_put.add_argument("--chunk-size", dest="chunk_size", help="Read chunk size")
    jf_put.add_argument(
        "--method", choices=["http", "sftp"], default=None, help="Transfer method"
    )

    # get
    jf_get = jobs_files_subparsers.add_parser(
        "get", help="Download file or directory from job directory"
    )
    jf_get.add_argument("remote", help="Remote file or directory path")
    jf_get.add_argument(
        "local", nargs="?", default=".", help="Local destination (default: .)"
    )
    jf_get.add_argument("--chunk-size", dest="chunk_size", help="Read chunk size")
    jf_get.add_argument(
        "--method", choices=["http", "sftp"], default=None, help="Transfer method"
    )

    # cat
    jf_cat = jobs_files_subparsers.add_parser(
        "cat", help="View remote text file content"
    )
    jf_cat.add_argument("path", help="File path")
    jf_cat.add_argument("--head", type=int, default=None, help="First N lines")
    jf_cat.add_argument("--tail", type=int, default=None, help="Last N lines")
    jf_cat.add_argument(
        "--lines",
        default=None,
        help="Line range, e.g. '10-20' or '10-'",
    )
    jf_cat.add_argument("--start", type=int, default=None, help="Start line (1-based)")
    jf_cat.add_argument("--end", type=int, default=None, help="End line (1-based)")
    jf_cat.add_argument(
        "--all", action="store_true", dest="all_lines", help="Output all lines"
    )
    jf_cat.add_argument("--encoding", default="utf-8", help="Text encoding")

    # tailf
    jf_tailf = jobs_files_subparsers.add_parser(
        "tailf", help="Follow file output in real-time (SFTP only)"
    )
    jf_tailf.add_argument("path", help="File path")
    jf_tailf.add_argument("--encoding", default="utf-8", help="Text encoding")

    # custom
    _add_jobs_files_custom_parser(jobs_files_subparsers)


def _add_jobs_files_custom_parser(jobs_files_subparsers):
    """Add jobs files custom subcommand with ls/get/cat/tailf."""
    jf_custom = jobs_files_subparsers.add_parser(
        "custom", help="File operations on compute node (SSH)"
    )
    jf_custom_subparsers = jf_custom.add_subparsers(
        dest="custom_command", help="Custom subcommands"
    )

    jf_custom_ls = jf_custom_subparsers.add_parser("ls", help="List directory contents")
    jf_custom_ls.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Directory path (relative to work_path)",
    )

    jf_custom_get = jf_custom_subparsers.add_parser(
        "get", help="Download file or directory to local"
    )
    jf_custom_get.add_argument("remote", help="Remote file or directory path")
    jf_custom_get.add_argument(
        "local",
        nargs="?",
        default=".",
        help="Local destination (default: current directory)",
    )

    jf_custom_cat = jf_custom_subparsers.add_parser("cat", help="View file content")
    jf_custom_cat.add_argument("path", help="File path")
    jf_custom_cat.add_argument("--head", type=int, default=None, help="First N lines")
    jf_custom_cat.add_argument("--tail", type=int, default=None, help="Last N lines")
    jf_custom_cat.add_argument("--encoding", default="utf-8", help="Text encoding")

    jf_custom_tailf = jf_custom_subparsers.add_parser(
        "tailf", help="Follow file output in real-time"
    )
    jf_custom_tailf.add_argument("path", help="File path")
    jf_custom_tailf.add_argument("--encoding", default="utf-8", help="Text encoding")


def _add_sessions_parser(subparsers):
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


def _add_files_parser(subparsers):
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

    # ls
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
        "--all-hidden",
        "-A",
        action="store_true",
        dest="hidden",
        help="Show hidden files (starting with .)",
    )
    files_ls_parser.add_argument(
        "--method",
        choices=["http", "sftp"],
        default=None,
        help="Transfer method: http (default via API) or sftp",
    )

    # cp
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

    # mv
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

    # rm
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

    # mkdir
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

    # put
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

    # get
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

    # compress
    files_compress_parser = files_subparsers.add_parser(
        "compress", help="Compress remote directory"
    )
    files_compress_parser.add_argument("source", help="Source remote directory path")
    files_compress_parser.add_argument("target", help="Target archive file full path")

    # uncompress
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

    # cat
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

    # tailf
    files_tailf_parser = files_subparsers.add_parser(
        "tailf", help="Follow file output in real-time (SFTP only)"
    )
    files_tailf_parser.add_argument("path", help="Remote file path")
    files_tailf_parser.add_argument("--encoding", default="utf-8", help="Text encoding")


def _add_apps_parser(subparsers):
    apps_parser = subparsers.add_parser("apps", help="Application operations")
    apps_subparsers = apps_parser.add_subparsers(
        dest="apps_command", help="Apps commands"
    )
    apps_subparsers.add_parser("list", help="List all applications (6.0+)")
    apps_subparsers.add_parser("list-v2", help="List available apps v2 (6.6+)")


def _add_departments_parser(subparsers):
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


def _add_users_parser(subparsers):
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
