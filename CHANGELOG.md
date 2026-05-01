# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

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
