"""Shared CLI utilities used by multiple command modules."""

import argparse
import sys
from typing import Optional

from appform_sdk.client import AppformClient
from appform_sdk.config import Config
from appform_sdk.formatters import format_output


class SubmitHelpFormatter(argparse.RawDescriptionHelpFormatter):
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


def get_completion_script(shell: str) -> Optional[str]:
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


# ---------------------------------------------------------------------------
# Client creation and output
# ---------------------------------------------------------------------------


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
        env=getattr(args, "env", None),
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


def resolve_output_format(args: argparse.Namespace) -> str:
    """Resolve output format: CLI arg > env var / config file > default (table)."""
    output = getattr(args, "output", None)
    if output:
        return output
    cfg = Config(config_file=getattr(args, "config_file", None))
    return cfg.output_format or "table"


# ---------------------------------------------------------------------------
# File operation helpers (used by files and jobs-file handlers)
# ---------------------------------------------------------------------------


def is_remote_path(path: str) -> bool:
    """Check if a path is remote (starts with /)."""
    return path.startswith("/")


def resolve_remote_path(path: str, config: Config) -> str:
    """Resolve a path to a full remote path using default_remote_path if needed."""
    if is_remote_path(path):
        return path
    default_remote = config.default_remote_path or "/"
    return f"{default_remote.rstrip('/')}/{path}"


def resolve_home_in_path(client, path: str, transfer_method: str) -> str:
    """Resolve $HOME in a remote path for SFTP transfers.

    HTTP API handles $HOME server-side; SFTP resolves it via SSH ``echo ~``.
    Returns the path unchanged if HTTP or if $HOME not present.
    """
    if transfer_method == "sftp" and "$HOME" in path:
        remote_home = client.sftp.get_home_dir()
        path = path.replace("$HOME", remote_home)
        while path.startswith("//"):
            path = path[1:]
    return path


def remote_file_exists(client, remote_dir: str, filename: str) -> bool:
    """Check if a file already exists in the remote directory."""
    try:
        items = client.files.list_all(path=remote_dir)
        for item in items:
            if item.get("fileName") == filename:
                return True
    except Exception:
        pass
    return False


def confirm_overwrite(filename: str) -> bool:
    """Ask user to confirm file overwrite."""
    try:
        answer = input(f"Remote file '{filename}' already exists. Overwrite? [y/N] ")
        return answer.strip().lower() in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def check_is_directory(client, cmd_method, remote):
    """Check if a remote path is a directory."""
    if cmd_method == "http":
        try:
            items = client.files.list(path=remote, page=1, page_size=1)
            data = items.get("data", [])
            # Directory listing returns a dict with files/records key,
            # or a list of entries. A single file returns differently.
            if isinstance(data, dict) and ("files" in data or "records" in data):
                return True
            if isinstance(data, list):
                return True
            return False
        except Exception:
            return False
    else:
        # SFTP: try listing the path; if it works, it's a directory
        try:
            result = client.sftp.list(path=remote, page=1, page_size=1)
            data = result.get("data", [])
            if isinstance(data, dict) and "files" in data:
                return True
            if isinstance(data, list):
                return True
            return remote.endswith("/")
        except Exception:
            return remote.endswith("/")
