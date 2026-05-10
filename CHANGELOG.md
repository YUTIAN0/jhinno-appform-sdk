# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Multi-environment configuration support**
  - `config.json` supports `environments` and `default_environment` fields
  - Select environment via: `Config(env="prod")`, `--env ENV`, or `APPFORM_ENV`
  - `Config.save_config_file(environment="prod")` saves to named environment
  - `to_dict()` reports `current_environment` and available environments list
  - Full backward compatibility with root-level config

- **`-e/--env` flag** for `appform` and `job_submit` CLI commands

- **`--environment` option** for `appform config set` to save config per environment

### Changed
- CLI handlers now propagate `env` to all `Config()` instantiations

## [0.0.6] - 2026-05-03

### Added
- **`try_launch_jhapp_client()` public function** — check and launch local JHApp client via HTTP API
- **`check_jhapp_client()` public function** — detect if local JHApp client is running on port 60540
- **Auto-launch JHApp client after `sessions start`** — CLI automatically tries to launch the client when a jhappUrl is returned; silent fallback if client unavailable

### Changed
- `SessionsAPI.connect_and_launch()` refactored to use shared `try_launch_jhapp_client()`
- Removed `SessionsAPI._try_launch_client()` static method, replaced with module-level public functions

### Fixed
- `DOCUMENTATION.md` package name: `appform-sdk` → `jhinno-appform-sdk`
- `DOCUMENTATION.md` missing `PyYAML>=6.0` dependency
- `sessions.list()` docstring — added warning that no-argument call paginates through all sessions (heavy operation)
- `jobs.list_jobs()` docstring — clarified `condition` parameter is mutually exclusive with other filters

## [0.0.5] - 2026-05-03

### Added
- **`jobs files custom` command** — compute node file operations via SSH
  - `appform jobs files <id> custom ls [path]` — list directory on compute node
  - `appform jobs files <id> custom get <remote> [local]` — download from compute node
  - `appform jobs files <id> custom cat <path>` — view file on compute node
  - `appform jobs files <id> custom tailf <path>` — follow file on compute node
  - `cat` supports `--head N` / `--tail N` / `--encoding ENC`
  - Configuration via `~/.appform/compute.yaml` (YAML format)
  - Supports direct SSH and gateway (jump host) connection modes
  - Uses `jjobs -env` to resolve work_path on compute node
  - `APPFORM_COMPUTE_CONFIG` environment variable to override config path
  - Reuses SFTP credentials from `~/.appform/config.json`
  - `ComputeError` exception for compute node errors
- **`__main__` entry point** for `job_submit` module — supports `python -m appform_sdk.job_submit`

### Fixed
- `via_gateway` SSH tunnel uses `pkey` instead of `key_filename` for `Transport.connect()`
- `tailf` supports glob patterns in file paths
- SFTP `get_home_dir()` properly triggers lazy transport connection
- Paramiko `Channel.settimeout()` method name (was `set_blocking`)
- Windows backslashes normalized to forward slashes in config paths
- Centralized version in `appform_sdk/VERSION` file, setup.py reads from it

## [0.0.4] - 2026-05-03

### Added
- **`job_submit` file upload support** — automatic upload of local files before job submission
  - `param_type: upload` parameters detect local files not in mapped remote paths
  - `--upload-path PATH` flag to specify remote upload directory
  - Default upload path: `$HOME/<YYYYMMDD_HHMMSS>/` (server-side $HOME resolution)
  - Multiple files and directories supported via `nargs='+'`
  - Upload method follows `APPFORM_DEFAULT_METHOD` (http/sftp)
  - SFTP resolves `$HOME` via SSH exec `echo ~` through `SFTPAPI.get_home_dir()`
  - Path mapping uses `windows_disk_mapping` values (e.g. `S: -> /apps`) to detect remote files
- **`jobs tailf` command** — track real-time job output files on compute node via SSH
  - `appform jobs files <id> tailf /path/to/file` — track job output files via SFTP
  - `--encoding` option to specify text encoding (default: utf-8)
  - `client.sftp.tailf()` returns (tail_pid, channel) for programmatic control
  - `client.sftp.kill_tail(tail_pid)` to stop a remote tail process via SSH
  - Requires `pip install jhinno-appform-sdk[sftp]`
- **`jobs.history` text output format** — job history text with cleaned column spacing,
  via new `type: text` output template type

## [0.0.3] - 2026-05-02

### Added
- **SFTP file transfer** as alternative to HTTP API for all file operations
  - `pip install jhinno-appform-sdk[sftp]` installs paramiko dependency
  - Lazy SFTP connection with reuse via `SFTPClientManager`
  - All file commands support `--method {http,sftp}` parameter
  - `files --method` group-level default affects all subcommands
  - `config set --default-method {http,sftp}` persistent configuration
  - `APPFORM_DEFAULT_METHOD` environment variable support
  - SFTP config: `sftp_host`, `sftp_port`, `sftp_username`, `sftp_password`, `sftp_key_file`, `sftp_key_password`
- **`files cat` command** — view remote text file content via SFTP
  - `--head N` — first N lines
  - `--tail N` — last N lines
  - `--lines 10-20` — line range (supports `10-` for from line 10 to EOF)
  - `--start N` / `--end N` — 1-based line range
  - `--all` — force output all lines for large files
  - `--encoding ENC` — text encoding (default: utf-8)
- **`SFTPAPI`** class with full file operation coverage: `list`, `list_all`, `mkdir`, `move`, `copy`, `delete`, `upload`, `upload_directory`, `download`, `download_directory`, `cat`
- **`SFTPError`** exception for SFTP-specific errors

### Changed
- All `FilesAPI` methods (`list`, `list_all`, `mkdir`, `copy`, `move`, `delete`, `upload`, `upload_directory`, `download`, `download_directory`) accept `transfer_method` parameter
- `move` / `copy` now detect whether destination is a directory or file path, enabling rename-like usage (`mv /a/file /a/file2`)
- `handle_files_command` added unified exception handling — errors output to stderr with clean messages instead of Python tracebacks

### Fixed
- SFTP `mv`/`cp` correctly treats second argument as destination file path when it doesn't exist
- SFTP `cat` on directory raises `IsADirectoryError` with clear message
- SFTP `ls` on file returns single-item result instead of `FileNotFoundError`
- SFTP connection robust to paramiko version differences (missing `.closed` attribute)
- Config password and credentials correctly passed to `AppformClient` for SFTP auth
- `_copy_recursive` creates parent directory before writing files

## [0.0.2] - 2026-05-01

### Added
- Session `connect-launch` command — checks for JHApp client and auto-launches on connect
- `AES_KEY` environment variable and `aes_key` parameter for cluster token auth
- Default module\*.yaml files added to `.gitignore`
- `connect_and_launch()` method to `SessionsAPI`
- Session start and connect templates to output_templates.yaml

### Changed
- `sessions list` with no arguments now defaults to current user's sessions
- `Config(config_file="~/.appform/...")` now correctly expands tilde paths
- `AppformClient` `base_url` and `verify_ssl` are now optional parameters
- `AppformClient(config=Config())` fully supported with optional config values
- `verify_ssl=False` correctly applied when set via Config or parameter
- Output templates enhanced with more session fields
- Template resolver supports array indexes (e.g., `data.0`)
- README updated with `verify_ssl=False` in Quick Start
- Windows py3.8/3.9 build fix: use `python -m pip` to avoid pip upgrade conflicts
- Black CI uses `--fast` to support py313/py314 target versions
- Release now includes standard wheel and sdist alongside platform bundles

### Fixed
- `verify_ssl` default `True` no longer overrides config value
- `black` formatting for `sessions.py` and `cli.py`
- Windows bundle correctly resolves all transitive dependencies

## [0.0.1] - 2026-05-01

### Added
- Initial release of jhinno-appform-sdk
- Full Python SDK for Appform 6.0-6.6 API
- CLI tool `appform` with jobs, sessions, files, apps, departments, users commands
- `job_submit` tool with Windows path conversion support
- Dynamic API extension system with JSON configuration
- AES encryption/decryption utilities
- Output template system (YAML-based, json/table/text/raw formats)
- GitHub Actions CI/CD with Build and Test, Build and Release workflows
- Offline installation with platform-specific dependency bundles
- Support for Python 3.8 through 3.14 on Linux and Windows
