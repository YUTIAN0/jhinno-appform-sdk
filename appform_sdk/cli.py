#!/usr/bin/env python3
"""
Compatibility shim — delegates to the refactored cli subpackage.

All public symbols are re-exported so existing imports like
  from appform_sdk.cli import main, create_parser, create_client, ...
continue to work.
"""

from appform_sdk.cli.builders import create_parser
from appform_sdk.cli.common import (
    SubmitHelpFormatter,
    confirm_overwrite,
    create_client,
    get_completion_script,
    is_remote_path,
    output_result,
    remote_file_exists,
    resolve_output_format,
    resolve_remote_path,
)
from appform_sdk.cli.cmd_auth import handle_auth_command
from appform_sdk.cli.cmd_apps import handle_apps_command
from appform_sdk.cli.cmd_config import handle_config_command
from appform_sdk.cli.cmd_departments import handle_departments_command
from appform_sdk.cli.cmd_endpoint import handle_endpoint_command
from appform_sdk.cli.cmd_extension import handle_extension_command
from appform_sdk.cli.cmd_files import handle_files_command
from appform_sdk.cli.cmd_jobs import (
    handle_jobs_command,
    handle_jobs_files_command,
    handle_jobs_files_custom,
)
from appform_sdk.cli.cmd_sessions import handle_sessions_command
from appform_sdk.cli.cmd_users import handle_users_command
from appform_sdk.cli.job_submit import (
    build_submit_parser,
    handle_jobs_submit,
    load_pm,
    print_app_params,
    print_apps_table,
)
from appform_sdk.cli.main import main

__all__ = [
    "main",
    "create_parser",
    "create_client",
    "output_result",
    "resolve_output_format",
    "get_completion_script",
    "SubmitHelpFormatter",
    "confirm_overwrite",
    "remote_file_exists",
    "is_remote_path",
    "resolve_remote_path",
    "handle_config_command",
    "handle_extension_command",
    "handle_endpoint_command",
    "handle_auth_command",
    "handle_jobs_command",
    "handle_sessions_command",
    "handle_files_command",
    "handle_jobs_files_command",
    "handle_jobs_files_custom",
    "handle_apps_command",
    "handle_departments_command",
    "handle_users_command",
    "handle_jobs_submit",
    "build_submit_parser",
    "load_pm",
    "print_apps_table",
    "print_app_params",
]
