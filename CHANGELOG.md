# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **`files tailf` command** — real-time remote file output tracking via SSH exec channel
  - `appform files tailf /path/to/file` — follows file output like `tail -f`
  - `appform jobs files <id> tailf /path/to/file` — track job output files
  - `--encoding` option to specify text encoding (default: utf-8)
  - `client.sftp.tailf()` returns (tail_pid, channel) for programmatic control
  - `client.sftp.kill_tail(tail_pid)` to stop a remote tail process via SSH
  - Requires `pip install jhinno-appform-sdk[sftp]`

### Added
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
