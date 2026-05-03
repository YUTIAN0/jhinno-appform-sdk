"""Main entry point for the CLI."""

import sys
from typing import Optional

from appform_sdk.cli.builders import create_parser
from appform_sdk.cli.cmd_apps import handle_apps_command
from appform_sdk.cli.cmd_auth import handle_auth_command
from appform_sdk.cli.cmd_config import handle_config_command
from appform_sdk.cli.cmd_departments import handle_departments_command
from appform_sdk.cli.cmd_endpoint import handle_endpoint_command
from appform_sdk.cli.cmd_extension import handle_extension_command
from appform_sdk.cli.cmd_files import handle_files_command
from appform_sdk.cli.cmd_jobs import handle_jobs_command
from appform_sdk.cli.cmd_sessions import handle_sessions_command
from appform_sdk.cli.cmd_users import handle_users_command
from appform_sdk.cli.common import (
    get_completion_script,
    resolve_output_format,
)
from appform_sdk.config import Config


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
        script = get_completion_script(parsed_args.generate_completion)
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
    parsed_args.output = resolve_output_format(parsed_args)

    # Load output template if specified
    from appform_sdk.formatters import load_templates, resolve_template_file

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
