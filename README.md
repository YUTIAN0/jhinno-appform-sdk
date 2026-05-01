# Appform SDK

Python SDK for Appform 6.0-6.6 API.

## Features

- Support for Appform 6.0, 6.3, 6.5, and 6.6 API versions
- Multiple authentication methods (Password, Token, AccessKey)
- Command-line interface (CLI)
- Extensible endpoint registry
- Version-specific endpoint support
- Configuration via environment variables or config file

## Supported Versions

| Version | Description |
|---------|-------------|
| 6.0 | Base version with core APIs |
| 6.3 | Same as 6.0 (no new endpoints) |
| 6.5 | Adds file confidentiality APIs |
| 6.6 | Adds V2 APIs, storage quota, CPU count APIs |

## Installation

### Standard installation (recommended)

```bash
pip install jhinno-appform-sdk
```

### Offline installation

Download the appropriate release package from [GitHub Releases](https://github.com/YUTIAN0/jhinno-appform-sdk/releases), then install without network access.

**Linux:**

```bash
tar xzf jhinno-appform-sdk-0.0.1-linux-x86_64-cp312.tar.gz
pip install --no-index --find-links=./bundle/ jhinno-appform-sdk
```

**Windows:**

```powershell
Expand-Archive jhinno-appform-sdk-0.0.1-windows-x86_64-cp312.zip
pip install --no-index --find-links=./bundle/ jhinno-appform-sdk
```

> Replace the version number and `cp312` with your Python version (e.g., `cp310` for Python 3.10).

Or install from source:

```bash
git clone https://github.com/YUTIAN0/jhinno-appform-sdk.git
cd appform-sdk
pip install -e .
```

### Requirements

- Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, or 3.14
- requests >= 2.28.0
- pycryptodome >= 3.15.0

## Quick Start

```python
from appform_sdk import AppformClient

# Method 1: Token authentication (login with password)
client = AppformClient(
    base_url="https://your-appform-server.com",
    verify_ssl=False,  # Set False if server uses a self-signed or weak certificate
)
result = client.auth.login(username="your_username", password="your_password")
print(f"Token: {client.token}")

# Method 2: AccessKey authentication
client = AppformClient(
    base_url="https://your-appform-server.com",
    access_key="your_access_key",
    access_key_secret="your_access_key_secret",
    username="your_username",
    verify_ssl=False,
)

# Method 3: Load from environment variables or config file
from appform_sdk import Config
config = Config(config_file="~/.appform/config.json")  # Specify config file path
print(f"Config file: {config.config_file}")
client = AppformClient(config=config)
# Automatically reads APPFORM_BASE_URL, APPFORM_ACCESS_KEY, APPFORM_ACCESS_KEY_SECRET,
# APPFORM_USERNAME, APPFORM_VERIFY_SSL, etc. from environment or config file

# Test connection
client.auth.ping()
```

## Configuration

The SDK supports configuration from multiple sources (in order of priority):

1. **Direct parameters** - Passed directly to `AppformClient` or `Config`
2. **Environment variables** - Set in shell environment
3. **Configuration file** - JSON file at `~/.appform/config.json`

### Environment Variables

```bash
export APPFORM_BASE_URL="https://your-appform-server.com"
export APPFORM_ACCESS_KEY="your_access_key"
export APPFORM_ACCESS_KEY_SECRET="your_access_key_secret"
export APPFORM_USERNAME="your_username"
export APPFORM_TOKEN="your_token"  # Optional
export APPFORM_API_VERSION="6.6"  # Optional, default: 6.5
export APPFORM_TIMEOUT="30"  # Optional, default 30
export APPFORM_VERIFY_SSL="false"  # Optional, default true
export APPFORM_EXTENSIONS_DIR="/path/to/extensions"  # Optional
```

### Configuration File

Create `~/.appform/config.json`:

```json
{
  "base_url": "https://your-appform-server.com",
  "access_key": "your_access_key",
  "access_key_secret": "your_access_key_secret",
  "username": "your_username",
  "api_version": "6.6",
  "timeout": 30,
  "verify_ssl": false
}
```

### Using Config Class

```python
from appform_sdk import Config, AppformClient

# Load from environment variables and config file
config = Config()

# Load from specific config file
config = Config(config_file="/path/to/config.json")

# Save configuration to file
Config.save_config_file(
    base_url="https://your-server.com",
    access_key="your_access_key",
    access_key_secret="your_access_key_secret",
    username="your_username",
    api_version="6.6",
    verify_ssl=False,
)

# Create client from config
client = AppformClient(
    base_url=config.base_url,
    access_key=config.access_key,
    access_key_secret=config.access_key_secret,
    username=config.username,
    api_version=config.api_version,
    verify_ssl=config.verify_ssl,
)
```

## Command Line Interface

The SDK provides a command-line tool `appform`:

```bash
# Show help
appform --help

# Show version
appform --version

# Configure (save to ~/.appform/config.json)
appform config set \
    --base-url "https://your-server.com" \
    --access-key "your_access_key" \
    --access-key-secret "your_access_key_secret" \
    --username "your_username" \
    --api-version "6.6" \
    --verify-ssl false

# Show current configuration
appform config show

# Authentication
appform auth login --username "user" --password "pass"
appform auth ping
appform auth logout

# Jobs
appform jobs list
appform jobs list --status RUN --page 1 --page-size 20
appform jobs status RUN
appform jobs status all
appform jobs get <job_id>
appform jobs stop <job_id>
appform jobs suspend <job_id>
appform jobs resume <job_id>
appform jobs output <job_id>
appform jobs files <job_id>
appform jobs history <job_id>
appform jobs submit --app-name fluent --job-name my_job --cores 4 --memory 8000

# Sessions
appform sessions start --app-id ansys --cores 2
appform sessions list
appform sessions list-all
appform sessions connect <session_id>
appform sessions disconnect <session_id>
appform sessions close <session_id>
appform sessions share <session_id> --usernames "user1,user2"

# Files
appform files list --path "/home/user"
appform files mkdir --path "/home/user" --name "new_folder"
appform files delete /path/to/file1 /path/to/file2

# Applications
appform apps list

# Users
appform users list --page 1 --page-size 20

# Extensions
appform extension list
appform extension load /path/to/extension.json

# Endpoints
appform endpoint list
appform endpoint list --version 6.6
appform endpoint call jobs.list --params '{"page": 1}'

# Use with command-line options (overrides config)
appform --base-url "https://other-server.com" jobs list

# Output format
appform -o text jobs list
appform -o json jobs list
```

## API Versioning

The SDK supports multiple API versions (6.0, 6.3, 6.5, and 6.6). Set the version via:

```bash
# Environment variable
export APPFORM_API_VERSION="6.6"
```

Or in code:

```python
from appform_sdk import AppformClient, VERSION_6_0, VERSION_6_3, VERSION_6_5, VERSION_6_6

# Use version 6.0 (base version)
client = AppformClient(base_url="https://your-server.com", api_version="6.0")

# Use version 6.3 (same as 6.0)
client = AppformClient(base_url="https://your-server.com", api_version="6.3")

# Use version 6.5 (adds file confidentiality)
client = AppformClient(base_url="https://your-server.com", api_version="6.5")

# Use version 6.6 (includes v2 endpoints)
client = AppformClient(base_url="https://your-server.com", api_version="6.6")

# Or use version constants
client = AppformClient(base_url="https://your-server.com", api_version=VERSION_6_6)
```

### Version Differences

| Feature | 6.0 | 6.3 | 6.5 | 6.6 |
|---------|-----|-----|-----|-----|
| Authentication APIs | ✓ | ✓ | ✓ | ✓ |
| Jobs APIs | ✓ | ✓ | ✓ | ✓ |
| Sessions APIs | ✓ | ✓ | ✓ | ✓ |
| Files APIs | ✓ | ✓ | ✓ | ✓ |
| Organization APIs | ✓ | ✓ | ✓ | ✓ |
| System APIs | ✓ | ✓ | ✓ | ✓ |
| File Confidentiality | - | - | ✓ | ✓ |
| V2 Jobs API | - | - | - | ✓ |
| V2 Sessions API | - | - | - | ✓ |
| V2 Apps API | - | - | - | ✓ |
| Storage Quota | - | - | - | ✓ |
| CPU Count APIs | - | - | - | ✓ |

### 6.5 New Endpoints

```python
# Get file confidentiality levels
levels = client.call_endpoint("files.getConfidentiality")

# Set file confidentiality level
result = client.call_endpoint("files.setConfidentiality", json_data={
    "path": "/home/user/file.txt",
    "level": "secret"
})
```

### 6.6 New Endpoints

```python
# Get job submission form
form = client.call_endpoint("jobs.getForm", path_params={"appId": "fluent"})

# Submit job v2 (with form params)
result = client.call_endpoint("jobs.submitV2", json_data={
    "appId": "fluent",
    "params": {
        "JH_CAS": "/home/user/jh.cas",
        "JH_NCPU": "4",
        "JH_ITERATION": "100"
    }
})

# List jobs v2
jobs = client.call_endpoint("jobs.listV2", params={"page": 1, "pageSize": 20})

# Delete job
client.call_endpoint("jobs.deleteV2", path_params={"jobId": "12345"})

# Get job monitoring info
info = client.call_endpoint("jobs.tooltip")

# Get total history job count
count = client.call_endpoint("jobs.totalHistory")

# Start session v2 (returns client and web connection)
session = client.call_endpoint("sessions.startV2", json_data={
    "appId": "ansys",
    "startNew": True,
    "cwd": "${HOME}"
})

# Get available apps v2
apps = client.call_endpoint("apps.listV2")

# Get storage quota
quota = client.call_endpoint("quota.storage")

# Get app CPU info
cpu_info = client.call_endpoint("count.appsCpu", params={"appId": "fluent"})

# Get all apps CPU info
all_cpu = client.call_endpoint("count.allAppsCpu")
```

## Extensions

Extensions allow you to add custom endpoints or override existing ones.

### Extension Configuration File

Create an extension file (e.g., `~/.appform/extensions/custom.json`):

```json
{
  "name": "custom-endpoints",
  "version": "1.0.0",
  "description": "Custom endpoints for specific environment",
  "endpoints": {
    "custom.report": {
      "path": "/appform/ws/api/custom/report",
      "method": "GET",
      "description": "Custom report endpoint"
    }
  },
  "overrides": {
    "jobs.list": {
      "path": "/appform/ws/api/v2/jobs/page",
      "method": "GET",
      "description": "Override jobs list with v2 endpoint"
    }
  }
}
```

### Loading Extensions

```python
from appform_sdk import AppformClient

# Load extensions from directory
client = AppformClient(
    base_url="https://your-server.com",
    extensions_dir="/path/to/extensions"
)

# Or load extension from file
client.load_extension_file("/path/to/extension.json")

# Or load extension from dict
client.load_extension({
    "name": "my-extension",
    "version": "1.0.0",
    "endpoints": {
        "custom.endpoint": {
            "path": "/custom/endpoint",
            "method": "GET"
        }
    }
})
```

### Registering Endpoints Directly

```python
from appform_sdk import AppformClient

client = AppformClient(base_url="https://your-server.com")

# Register a new endpoint
client.register_endpoint(
    name="custom.myEndpoint",
    path="/appform/ws/api/custom/endpoint",
    method="POST",
    description="My custom endpoint"
)

# Override an existing endpoint
client.register_endpoint(
    name="jobs.list",
    path="/appform/ws/api/v2/jobs/page",
    method="GET",
    override=True
)
```

### Using Dynamic API

Call registered endpoints by name:

```python
from appform_sdk import AppformClient

client = AppformClient(base_url="https://your-server.com")

# Call endpoint by name
result = client.call_endpoint("jobs.list", params={"page": 1})

# Or use the dynamic API
result = client.api.call("jobs.get", path_params={"jobId": "12345"})

# Call custom endpoint
result = client.api.call("custom.report", params={"type": "monthly"})
```

## Authentication

### Login with Password

```python
from appform_sdk import AppformClient

client = AppformClient(base_url="https://your-server.com")

# Login
result = client.auth.login(username="jhadmin", password="Letmein123")

if result["result"] == "success":
    print("Login successful!")
    print(f"Token: {client.token}")
```

### Login with Encrypted Token

```python
from appform_sdk import AppformClient

client = AppformClient(base_url="https://your-server.com")

# Login with token-based authentication
result = client.auth.login_with_token(username="jhadmin", timeout=60)
```

### AccessKey Authentication

AccessKey authentication uses HMAC-SHA256 signature. For each request, the SDK automatically generates:
- `signature`: HMAC-SHA256 hash of `#accessKey#username#currentTimeMillis#`
- `currentTimeMillis`: Current timestamp in milliseconds

The following headers are sent with each request:
- `accessKey`: Your access key
- `username`: User account name
- `signature`: Generated signature
- `currentTimeMillis`: Current timestamp

**Note**: `accessKeySecret` is used to generate the signature but is **NOT** sent in request headers.

```python
from appform_sdk import AppformClient

# Method 1: Initialize with AccessKey
client = AppformClient(
    base_url="https://your-server.com",
    access_key="your_access_key",
    access_key_secret="your_access_key_secret",
    username="your_username"
)

# Method 2: Set AccessKey after initialization
client = AppformClient(base_url="https://your-server.com")
client.auth.login_with_access_key(
    access_key="your_access_key",
    access_key_secret="your_access_key_secret",
    username="your_username"
)

# Check authentication status
if client.auth.is_authenticated():
    print("Client is authenticated")

if client.auth.is_access_key_authenticated():
    print("Using AccessKey authentication")

if client.auth.is_token_authenticated():
    print("Using token authentication")

# Clear AccessKey credentials
client.auth.clear_access_key()
```

### Signature Generation

```python
from appform_sdk import SignatureGenerator

signature, timestamp = SignatureGenerator.generate_signature(
    access_key="your_access_key",
    access_key_secret="your_access_key_secret",
    username="your_username"
)

# Or get complete auth headers
headers = SignatureGenerator.generate_auth_headers(
    access_key="your_access_key",
    access_key_secret="your_access_key_secret",
    username="your_username"
)
# Returns: {"accessKey": ..., "signature": ..., "currentTimeMillis": ..., "username": ...}
```

## Jobs

### Submit a Job (6.5)

```python
result = client.jobs.submit(
    app_name="fluent",
    job_name="my_simulation",
    queue="normal",
    cores=4,
    memory=8000,
    walltime="2:00:00",
    input_files=["/data/input.cas"],
    output_files=["/data/output.dat"],
)
print(f"Job ID: {result['data']['jobId']}")
```

### Submit a Job v2 (6.6)

```python
# First get the form
form = client.call_endpoint("jobs.getForm", path_params={"appId": "fluent"})

# Then submit with form params
result = client.call_endpoint("jobs.submitV2", json_data={
    "appId": "fluent",
    "params": {
        "JH_CAS": "/home/user/jh.cas",
        "JH_NCPU": "4",
        "JH_ITERATION": "100",
        "JH_PROJECT": "default"
    }
})
```

### List Jobs

```python
# List all jobs
result = client.jobs.list_jobs(page=1, page_size=20)

# Filter by status
result = client.jobs.list_jobs(
    page=1,
    page_size=20,
    status_filter=["RUN", "PEND"],
    name_filter="fluent_",
)

for job in result["data"]["content"]:
    print(f"Job: {job['name']}, Status: {job['status']}")
```

### Job Operations

```python
# Get job details
job = client.jobs.get_job(job_id="12345")

# Stop a job
client.jobs.stop(job_id="12345")

# Suspend a job
client.jobs.suspend(job_id="12345")

# Resume a job
client.jobs.resume(job_id="12345")

# Get job output
output = client.jobs.get_output(job_id="12345")

# Get job files
files = client.jobs.get_files(job_id="12345")

# Delete a job (6.6)
client.call_endpoint("jobs.deleteV2", path_params={"jobId": "12345"})
```

### Batch Operations

```python
# Stop multiple jobs
client.jobs.batch_stop(["job1", "job2", "job3"])

# Get history for multiple jobs
history = client.jobs.get_batch_history(["job1", "job2"])
```

## Sessions

### Start a Session (6.5)

```python
result = client.sessions.start(
    app_id="ansys",
    session_name="my_session",
    cores=2,
    memory=4000,
)
print(f"Session ID: {result['data']['sessionId']}")
```

### Start a Session v2 (6.6)

```python
result = client.call_endpoint("sessions.startV2", json_data={
    "appId": "ansys",
    "startNew": True,
    "cwd": "${HOME}",
    "workFile": "${HOME}/work"
})
# Returns both client connection and web connection
```

### Manage Sessions

```python
# List all sessions
sessions = client.sessions.list_all()

# Connect to a session
client.sessions.connect(session_id="session_123")

# Disconnect from a session
client.sessions.disconnect(session_id="session_123")

# Close a session
client.sessions.close(session_id="session_123")
```

### Share Sessions

```python
# Share session with other users
client.sessions.share(
    session_id="session_123",
    usernames=["user1", "user2"],
)

# Cancel sharing
client.sessions.cancel_share(session_id="session_123")

# Transfer operation to another user
client.sessions.transfer_operation(
    session_id="session_123",
    username="other_user",
)
```

## Files

### File Operations

```python
# List files
files = client.files.list(path="/home/user/data")

# Create directory
client.files.mkdir(path="/home/user", name="new_folder")

# Rename file
client.files.rename(old_path="/home/user/old_name.txt", new_name="new_name.txt")

# Copy files
client.files.copy(
    src_paths=["/home/user/file1.txt", "/home/user/file2.txt"],
    dest_path="/home/user/backup/",
)

# Delete files
client.files.delete(paths=["/home/user/old_file.txt"])

# Compress files
client.files.compress(
    paths=["/home/user/data/"],
    output_name="backup.zip",
    output_path="/home/user/",
)

# Uncompress archive
client.files.uncompress(
    archive_path="/home/user/backup.zip",
    dest_path="/home/user/extracted/",
)
```

### Upload and Download

```python
# Upload file
client.files.upload(
    file_path="/local/path/file.txt",
    remote_path="/home/user/data/",
)

# Download file
content = client.files.download(remote_path="/home/user/data/file.txt")

# Download to local file
client.files.download(
    remote_path="/home/user/data/file.txt",
    local_path="/local/path/downloaded.txt",
)
```

## Organization

### Department Management

```python
# Get department tree
deps = client.organization.get_departments()

# Create department
client.organization.create_department(
    dep_name="engineering",
    dep_chname="工程部",
    parent_dep="company",
)

# Update department
client.organization.update_department(
    dep_name="engineering",
    dep_chname="工程部门",
)

# Delete department
client.organization.delete_department(dep_name="engineering")
```

### User Management

```python
# List users
users = client.organization.get_users(page=1, page_size=20)

# Create user
client.organization.create_user(
    username="newuser",
    chusername="新用户",
    password="SecurePass123",
    dep="engineering",
    mail="user@example.com",
)

# Update user
client.organization.update_user(
    username="newuser",
    phone="1234567890",
)

# Reset password
client.organization.reset_password(
    username="newuser",
    new_password="NewSecurePass456",
)

# Delete user
client.organization.delete_user(username="newuser")
```

## Error Handling

```python
from appform_sdk import AppformClient
from appform_sdk.exceptions import AuthenticationError, APIError, AppformError

client = AppformClient(base_url="https://your-server.com")

try:
    client.auth.login(username="user", password="wrong_password")
except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
except APIError as e:
    print(f"API error (status {e.status_code}): {e.message}")
except AppformError as e:
    print(f"General error: {e.message}")
```

## Context Manager

```python
from appform_sdk import AppformClient

with AppformClient(base_url="https://your-server.com") as client:
    client.auth.login(username="user", password="pass")
    jobs = client.jobs.list_jobs()
    # Session automatically closed on exit
```

## API Reference

### AppformClient

| Property | Description |
|----------|-------------|
| `auth` | Authentication API |
| `jobs` | Jobs API |
| `sessions` | Sessions API |
| `apps` | Applications API |
| `files` | Files API |
| `organization` | Organization API |
| `api` | Dynamic API for calling registered endpoints |
| `registry` | API endpoint registry |
| `extension_manager` | Extension manager |

### AuthAPI

| Method | Description |
|--------|-------------|
| `login(username, password)` | Login with credentials |
| `login_with_token(username, timeout)` | Login with encrypted token |
| `login_with_access_key(access_key, access_key_secret, username)` | Configure AccessKey auth |
| `logout()` | Logout current session |
| `ping()` | Test service connection |
| `register(...)` | Register new user |
| `check_upload_permission()` | Check upload permission |
| `check_download_permission()` | Check download permission |
| `is_authenticated()` | Check if authenticated |
| `is_access_key_authenticated()` | Check if using AccessKey |
| `is_token_authenticated()` | Check if using token |

### JobsAPI

| Method | Description |
|--------|-------------|
| `submit(...)` | Submit a new job |
| `get_job(job_id)` | Get job details |
| `list_jobs(...)` | List jobs with pagination |
| `stop(job_id)` | Stop a job |
| `suspend(job_id)` | Suspend a job |
| `resume(job_id)` | Resume a job |
| `get_output(job_id)` | Get job output |
| `get_files(job_id)` | Get job files |

### SessionsAPI

| Method | Description |
|--------|-------------|
| `start(app_id, ...)` | Start a session |
| `list_all()` | List all sessions |
| `connect(session_id)` | Connect to session |
| `disconnect(session_id)` | Disconnect from session |
| `close(session_id)` | Close session |
| `share(session_id, usernames)` | Share session |

### FilesAPI

| Method | Description |
|--------|-------------|
| `list(path)` | List files |
| `mkdir(path, name)` | Create directory |
| `rename(old_path, new_name)` | Rename file |
| `copy(src_paths, dest_path)` | Copy files |
| `delete(paths)` | Delete files |
| `upload(file_path, remote_path)` | Upload file |
| `download(remote_path, local_path)` | Download file |
| `compress(paths, output_name)` | Compress files |
| `uncompress(archive_path, dest_path)` | Uncompress archive |

### Dynamic API Endpoints (6.6)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `jobs.getForm` | GET | Get job submission form |
| `jobs.submitV2` | POST | Submit job v2 |
| `jobs.listV2` | GET | List jobs v2 |
| `jobs.deleteV2` | DELETE | Delete a job |
| `jobs.tooltip` | GET | Get job monitoring info |
| `jobs.totalHistory` | GET | Get total history count |
| `sessions.startV2` | POST | Start session v2 |
| `apps.listV2` | GET | Get available apps v2 |
| `quota.storage` | GET | Get storage quota |
| `count.appsCpu` | GET | Get app CPU info |
| `count.allAppsCpu` | GET | Get all apps CPU info |

## License

MIT License
