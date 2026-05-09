"""Tests for CLI argument parsing."""

from unittest.mock import MagicMock

import pytest


class TestCreateParser:
    """Tests for parser creation and subcommand routing."""

    def setup_method(self):
        from appform_sdk.cli.builders import create_parser

        self.parser = create_parser()

    def test_parser_exists(self):
        """Test parser is created successfully."""
        assert self.parser is not None
        assert self.parser.prog == "appform"

    def test_version_flag(self):
        """Test --version flag."""
        with pytest.raises(SystemExit) as exc:
            self.parser.parse_args(["--version"])
        assert exc.value.code == 0

    def test_jobs_subcommand(self):
        """Test 'jobs' subcommand parses correctly."""
        args = self.parser.parse_args(["jobs", "list"])
        assert args.command == "jobs"
        assert args.jobs_command == "list"

    def test_jobs_get(self):
        """Test 'jobs get' with job ID."""
        args = self.parser.parse_args(["jobs", "get", "12345"])
        assert args.command == "jobs"
        assert args.jobs_command == "get"
        assert args.job_id == "12345"

    def test_jobs_delete(self):
        """Test 'jobs delete' with job ID."""
        args = self.parser.parse_args(["jobs", "delete", "12345"])
        assert args.jobs_command == "delete"

    def test_jobs_files_ls(self):
        """Test 'jobs files <id> ls' subcommand."""
        args = self.parser.parse_args(["jobs", "files", "12345", "ls"])
        assert args.command == "jobs"
        assert args.jobs_command == "files"
        assert args.job_id == "12345"
        assert args.jobs_files_command == "ls"

    def test_jobs_files_get(self):
        """Test 'jobs files <id> get' with remote and local paths."""
        args = self.parser.parse_args(
            ["jobs", "files", "12345", "get", "/remote/f.txt", "/local/f.txt"]
        )
        assert args.jobs_files_command == "get"
        assert args.remote == "/remote/f.txt"
        assert args.local == "/local/f.txt"

    def test_jobs_files_cat(self):
        """Test 'jobs files <id> cat' with head/tail."""
        args = self.parser.parse_args(
            ["jobs", "files", "12345", "cat", "/f.txt", "--head", "10"]
        )
        assert args.jobs_files_command == "cat"
        assert args.head == 10

    def test_jobs_files_custom_ls(self):
        """Test 'jobs files <id> custom ls' subcommand."""
        args = self.parser.parse_args(["jobs", "files", "12345", "custom", "ls"])
        assert args.jobs_files_command == "custom"
        assert args.custom_command == "ls"

    def test_jobs_files_custom_get(self):
        """Test 'jobs files <id> custom get' subcommand."""
        args = self.parser.parse_args(
            ["jobs", "files", "12345", "custom", "get", "out.log", "./out.log"]
        )
        assert args.custom_command == "get"
        assert args.remote == "out.log"
        assert args.local == "./out.log"

    def test_jobs_files_custom_cat(self):
        """Test 'jobs files <id> custom cat' with head/tail."""
        args = self.parser.parse_args(
            ["jobs", "files", "12345", "custom", "cat", "log.txt", "--tail", "50"]
        )
        assert args.custom_command == "cat"
        assert args.path == "log.txt"
        assert args.tail == 50

    def test_jobs_files_custom_tailf(self):
        """Test 'jobs files <id> custom tailf' subcommand."""
        args = self.parser.parse_args(
            ["jobs", "files", "12345", "custom", "tailf", "output.log"]
        )
        assert args.custom_command == "tailf"
        assert args.path == "output.log"

    def test_files_subcommand(self):
        """Test 'files' top-level subcommand."""
        args = self.parser.parse_args(["files", "ls", "/path"])
        assert args.command == "files"
        assert args.files_command == "ls"

    def test_files_put(self):
        """Test 'files put' subcommand."""
        args = self.parser.parse_args(["files", "put", "./local.txt", "/remote/"])
        assert args.files_command == "put"
        assert args.local == "./local.txt"
        assert args.remote == "/remote/"

    def test_files_get(self):
        """Test 'files get' subcommand."""
        args = self.parser.parse_args(["files", "get", "/remote/f.txt", "./f.txt"])
        assert args.files_command == "get"

    def test_sessions_subcommand(self):
        """Test 'sessions' subcommand."""
        args = self.parser.parse_args(["sessions", "list"])
        assert args.command == "sessions"
        assert args.sessions_command == "list"

    def test_sessions_start(self):
        """Test 'sessions start' with --app-id."""
        args = self.parser.parse_args(["sessions", "start", "--app-id", "gedit"])
        assert args.sessions_command == "start"
        assert args.app_id == "gedit"

    def test_sessions_connect(self):
        """Test 'sessions connect' with session ID."""
        args = self.parser.parse_args(["sessions", "connect", "sess-123"])
        assert args.sessions_command == "connect"
        assert args.session_id == "sess-123"

    def test_apps_subcommand(self):
        """Test 'apps' subcommand."""
        args = self.parser.parse_args(["apps", "list"])
        assert args.command == "apps"
        assert args.apps_command == "list"

    def test_auth_subcommand(self):
        """Test 'auth' subcommand with login."""
        args = self.parser.parse_args(
            ["auth", "login", "--username", "user", "--password", "pass"]
        )
        assert args.command == "auth"
        assert args.auth_command == "login"

    def test_config_subcommand(self):
        """Test 'config' subcommand."""
        args = self.parser.parse_args(["config", "show"])
        assert args.command == "config"

    def test_global_options(self):
        """Test global options parsing."""
        args = self.parser.parse_args(
            ["--base-url", "https://test.com", "--username", "u", "jobs", "list"]
        )
        assert args.base_url == "https://test.com"
        assert args.auth_username == "u"

    def test_output_format(self):
        """Test output format option."""
        args = self.parser.parse_args(["--output", "json", "jobs", "list"])
        assert args.output == "json"

    def test_generate_completion(self):
        """Test shell completion generation."""
        args = self.parser.parse_args(["--generate-completion", "bash"])
        assert args.generate_completion == "bash"

    def test_jobs_submit_subcommand(self):
        """Test 'jobs submit' parses."""
        args = self.parser.parse_args(["jobs", "submit"])
        assert args.command == "jobs"
        assert args.jobs_command == "submit"

    def test_departments_subcommand(self):
        """Test 'departments' subcommand."""
        args = self.parser.parse_args(["departments", "list"])
        assert args.command == "departments"

    def test_users_subcommand(self):
        """Test 'users' subcommand."""
        args = self.parser.parse_args(["users", "list"])
        assert args.command == "users"

    def test_jobs_status(self):
        """Test 'jobs status' subcommand."""
        args = self.parser.parse_args(["jobs", "status", "RUN"])
        assert args.jobs_command == "status"

    def test_jobs_params(self):
        """Test 'jobs params' subcommand."""
        args = self.parser.parse_args(["jobs", "params", "myapp"])
        assert args.jobs_command == "params"
        assert args.app_id == "myapp"

    def test_jobs_submit_raw(self):
        """Test 'jobs submit-raw' subcommand."""
        args = self.parser.parse_args(
            ["jobs", "submit-raw", "--app-id", "app1", "--params", "{}"]
        )
        assert args.jobs_command == "submit-raw"

    def test_jobs_form(self):
        """Test 'jobs form' subcommand."""
        args = self.parser.parse_args(["jobs", "form", "app1"])
        assert args.jobs_command == "form"
        assert args.app_id == "app1"

    def test_extension_subcommand(self):
        """Test 'extension' subcommand."""
        args = self.parser.parse_args(["extension", "list"])
        assert args.command == "extension"

    def test_endpoint_subcommand(self):
        """Test 'endpoint' subcommand."""
        args = self.parser.parse_args(["endpoint", "list"])
        assert args.command == "endpoint"


class TestCLICommon:
    """Tests for CLI common utilities."""

    def test_resolve_output_format_from_args(self):
        """Test resolving json output format from args."""
        from appform_sdk.cli.common import resolve_output_format

        args = MagicMock()
        args.output = "json"
        args.config_file = None
        assert resolve_output_format(args) == "json"

    def test_resolve_output_format_from_config(self):
        """Test resolving output format from config when args has none."""
        from appform_sdk.cli.common import resolve_output_format

        args = MagicMock()
        args.output = None
        args.config_file = None
        # Falls back to config default "table"
        result = resolve_output_format(args)
        assert result in ("table", "pprint")

    def test_resolve_remote_path_absolute(self):
        """Test absolute remote path returns as-is."""
        from appform_sdk.cli.common import resolve_remote_path

        config = MagicMock()
        config.default_remote_path = "/default"
        result = resolve_remote_path("/absolute/path", config)
        assert result == "/absolute/path"

    def test_is_remote_path(self):
        """Test remote path detection."""
        from appform_sdk.cli.common import is_remote_path

        assert is_remote_path("/remote/path") is True
        assert is_remote_path("./local/path") is False
        assert is_remote_path("relative") is False


class TestCLIMain:
    """Tests for CLI main dispatch (without external calls)."""

    def test_main_help_exits(self):
        """Test main --help exits cleanly."""
        from appform_sdk.cli.main import main

        with pytest.raises(SystemExit) as exc:
            main(["--help"])
        assert exc.value.code == 0

    def test_jobs_help_exits(self):
        """Test 'jobs --help' exits cleanly."""
        from appform_sdk.cli.main import main

        with pytest.raises(SystemExit) as exc:
            main(["jobs", "--help"])
        assert exc.value.code == 0

    def test_no_command_shows_help(self):
        """Test no command shows help."""
        from appform_sdk.cli.main import main

        with pytest.raises(SystemExit):
            main([])


class TestSessionsCommand:
    """Tests for sessions command argument parsing."""

    def setup_method(self):
        from appform_sdk.cli.builders import create_parser

        self.parser = create_parser()

    def test_sessions_start_with_options(self):
        """Test sessions start with --start-new and --cwd."""
        args = self.parser.parse_args(
            [
                "sessions",
                "start",
                "--app-id",
                "app1",
                "--start-new",
                "--cwd",
                "/home/user",
            ]
        )
        assert args.app_id == "app1"
        assert args.start_new is True
        assert args.cwd == "/home/user"

    def test_sessions_close(self):
        """Test sessions close subcommand."""
        args = self.parser.parse_args(["sessions", "close", "sess-abc"])
        assert args.sessions_command == "close"
        assert args.session_id == "sess-abc"

    def test_sessions_connect_launch(self):
        """Test sessions connect-launch subcommand."""
        args = self.parser.parse_args(["sessions", "connect-launch", "sess-abc"])
        assert args.sessions_command == "connect-launch"

    def test_sessions_share(self):
        """Test sessions share subcommand."""
        args = self.parser.parse_args(
            ["sessions", "share", "sess-abc", "--usernames", "user1,user2"]
        )
        assert args.sessions_command == "share"
        assert args.usernames == "user1,user2"

    def test_sessions_disconnect(self):
        """Test sessions disconnect subcommand."""
        args = self.parser.parse_args(["sessions", "disconnect", "sess-abc"])
        assert args.sessions_command == "disconnect"

    def test_sessions_list_all(self):
        """Test sessions list-all subcommand."""
        args = self.parser.parse_args(["sessions", "list-all", "--page", "2"])
        assert args.sessions_command == "list-all"
        assert args.page == 2


class TestFilesCommand:
    """Tests for files command argument parsing."""

    def setup_method(self):
        from appform_sdk.cli.builders import create_parser

        self.parser = create_parser()

    def test_files_rm(self):
        """Test files rm subcommand."""
        args = self.parser.parse_args(["files", "rm", "/path/to/file"])
        assert args.files_command == "rm"

    def test_files_mkdir(self):
        """Test files mkdir with --no-force."""
        args = self.parser.parse_args(["files", "mkdir", "/new/dir", "--no-force"])
        assert args.files_command == "mkdir"
        assert args.no_force is True

    def test_files_compress(self):
        """Test files compress subcommand."""
        args = self.parser.parse_args(["files", "compress", "/src", "/dst/archive.zip"])
        assert args.files_command == "compress"
        assert args.source == "/src"
        assert args.target == "/dst/archive.zip"

    def test_files_uncompress(self):
        """Test files uncompress with password."""
        args = self.parser.parse_args(
            ["files", "uncompress", "/archive.zip", "/dst/", "--password", "pwd"]
        )
        assert args.files_command == "uncompress"
        assert args.password == "pwd"

    def test_files_cat(self):
        """Test files cat with --lines."""
        args = self.parser.parse_args(["files", "cat", "/file.txt", "--lines", "10-20"])
        assert args.files_command == "cat"
        assert args.lines == "10-20"

    def test_files_tailf(self):
        """Test files tailf subcommand."""
        args = self.parser.parse_args(["files", "tailf", "/file.log"])
        assert args.files_command == "tailf"

    def test_files_ls_all_flag(self):
        """Test files ls with --all flag."""
        args = self.parser.parse_args(["files", "ls", "/path", "--all"])
        assert args.list_all is True

    def test_files_put_with_chunk_size(self):
        """Test files put with --chunk-size."""
        args = self.parser.parse_args(
            ["files", "put", "./f.txt", "/remote/", "--chunk-size", "50M"]
        )
        assert args.chunk_size == "50M"

    def test_files_method_option(self):
        """Test files command with --method sftp."""
        args = self.parser.parse_args(["files", "ls", "/path", "--method", "sftp"])
        assert args.method == "sftp"

    def test_files_mv(self):
        """Test files mv subcommand."""
        args = self.parser.parse_args(["files", "mv", "/src", "/dst"])
        assert args.files_command == "mv"

    def test_files_cp(self):
        """Test files cp subcommand."""
        args = self.parser.parse_args(["files", "cp", "/src", "/dst"])
        assert args.files_command == "cp"

    def test_files_conf_get_levels(self):
        """Test files conf --get-levels."""
        args = self.parser.parse_args(["files", "conf", "--get-levels"])
        assert args.files_command == "conf"
        assert args.get_levels is True


class TestAppsCommand:
    """Tests for apps command argument parsing."""

    def setup_method(self):
        from appform_sdk.cli.builders import create_parser

        self.parser = create_parser()

    def test_apps_list(self):
        """Test apps list subcommand."""
        args = self.parser.parse_args(["apps", "list"])
        assert args.apps_command == "list"

    def test_apps_list_v2(self):
        """Test apps list-v2 subcommand."""
        args = self.parser.parse_args(["apps", "list-v2"])
        assert args.apps_command == "list-v2"


class TestJobsFilesCommand:
    """Tests for jobs files subcommands."""

    def setup_method(self):
        from appform_sdk.cli.builders import create_parser

        self.parser = create_parser()

    def test_jobs_files_cp(self):
        """Test jobs files cp subcommand."""
        args = self.parser.parse_args(["jobs", "files", "123", "cp", "/a", "/b"])
        assert args.jobs_files_command == "cp"

    def test_jobs_files_mv(self):
        """Test jobs files mv subcommand."""
        args = self.parser.parse_args(["jobs", "files", "123", "mv", "/a", "/b"])
        assert args.jobs_files_command == "mv"

    def test_jobs_files_rm(self):
        """Test jobs files rm subcommand."""
        args = self.parser.parse_args(["jobs", "files", "123", "rm", "/a"])
        assert args.jobs_files_command == "rm"

    def test_jobs_files_mkdir(self):
        """Test jobs files mkdir subcommand."""
        args = self.parser.parse_args(["jobs", "files", "123", "mkdir", "/new"])
        assert args.jobs_files_command == "mkdir"

    def test_jobs_files_put(self):
        """Test jobs files put subcommand."""
        args = self.parser.parse_args(
            ["jobs", "files", "123", "put", "./f.txt", "/remote/"]
        )
        assert args.jobs_files_command == "put"

    def test_jobs_files_tailf(self):
        """Test jobs files tailf subcommand."""
        args = self.parser.parse_args(["jobs", "files", "123", "tailf", "/output.log"])
        assert args.jobs_files_command == "tailf"
