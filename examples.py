#!/usr/bin/env python3
"""
Example usage of Appform SDK
"""

from appform_sdk import AppformClient, Config, FileInfo, Job, PaginatedResult, Session


def config_example():
    """Example using configuration."""
    print("\n" + "=" * 50)
    print("Configuration Example")
    print("=" * 50)

    # Method 1: Load from environment variables
    # Set these env vars: APPFORM_BASE_URL, APPFORM_ACCESS_KEY, etc.
    config = Config.from_env()
    print(f"Config from env: {config}")

    # Method 2: Load from config file
    # Create ~/.appform/config.json first
    config = Config.from_file("~/.appform/config.json")
    print(f"Config from file: {config}")

    # Method 3: Auto-load (env vars + config file)
    config = Config()
    print(f"Auto-loaded config: {config}")

    # Save configuration to file
    Config.save_config_file(
        base_url="https://your-server.com",
        access_key="your_access_key",
        access_key_secret="your_access_key_secret",
        username="your_username",
    )
    print("Configuration saved to ~/.appform/config.json")

    # Create client from config
    if config.base_url:
        client = AppformClient(
            base_url=config.base_url,
            access_key=config.access_key,
            access_key_secret=config.access_key_secret,
            username=config.username,
        )
        print("Client created from config")
        client.close()


def main():
    # Initialize client
    client = AppformClient(base_url="https://your-appform-server.com")

    # ==================== Authentication ====================
    print("=" * 50)
    print("Authentication Examples")
    print("=" * 50)

    # Method 1: Login with username and password
    result = client.auth.login(username="your_username", password="your_password")
    print(f"Login result: {result['result']}")
    print(f"Token: {client.token}")

    # Method 2: Login with encrypted token (cluster environment only)
    # result = client.auth.login_with_token(timeout=60)

    # Method 3: AccessKey authentication
    # client.auth.login_with_access_key(
    #     access_key="your_access_key",
    #     access_key_secret="your_access_key_secret",
    #     username="your_username"
    # )

    # Test connection
    ping_result = client.auth.ping()
    print(f"Ping result: {ping_result['message']}")

    # Check permissions
    if client.auth.has_upload_permission():
        print("User has upload permission")
    if client.auth.has_download_permission():
        print("User has download permission")

    # ==================== Jobs ====================
    print("\n" + "=" * 50)
    print("Jobs Examples")
    print("=" * 50)

    # Submit a job
    job_result = client.jobs.submit(
        app_id="fluent",
        params={
            "JH_JOB_NAME": "my_simulation",
            "JH_CAS": "/data/input.cas",
            "JH_NCPU": "4",
        },
    )
    print(f"Job submitted: {job_result}")

    # List jobs with pagination
    jobs_result = client.jobs.list_jobs(
        page=1,
        page_size=10,
        status_filter=["RUN", "PEND"],
    )

    # Parse jobs using model
    paginated = PaginatedResult.from_dict(jobs_result.get("data", {}), Job.from_dict)
    print(f"Total jobs: {paginated.total_elements}")

    for job in paginated.content:
        print(f"  - Job {job.job_id}: {job.name} ({job.status})")

    # Get job details
    if paginated.content:
        job_id = paginated.content[0].job_id
        job_detail = client.jobs.get_job(job_id)
        job = Job.from_dict(job_detail.get("data", {}))
        print(f"Job details: {job.name}, Status: {job.status}, Owner: {job.owner}")

    # Job operations
    # client.jobs.stop(job_id="12345")
    # client.jobs.suspend(job_id="12345")
    # client.jobs.resume(job_id="12345")

    # Get job output
    # output = client.jobs.get_output(job_id="12345")
    # print(f"Job output: {output}")

    # ==================== Sessions ====================
    print("\n" + "=" * 50)
    print("Sessions Examples")
    print("=" * 50)

    # Start a session
    session_result = client.sessions.start(
        app_id="ansys",
        start_new=True,
        cwd="${HOME}",
    )
    print(f"Session started: {session_result}")

    # List all sessions
    sessions_result = client.sessions.list_all()
    print(f"Sessions: {sessions_result}")

    # Session operations
    # client.sessions.connect(session_id="session_123")
    # client.sessions.disconnect(session_id="session_123")
    # client.sessions.close(session_id="session_123")

    # Share session
    # client.sessions.share(
    #     session_id="session_123",
    #     usernames=["user1", "user2"],
    # )

    # ==================== Files ====================
    print("\n" + "=" * 50)
    print("Files Examples")
    print("=" * 50)

    # List files
    files_result = client.files.list(path="/home/user")
    print(f"Files: {files_result}")

    # Create directory
    # mkdir_result = client.files.mkdir(path="/home/user", name="new_folder")
    # print(f"Create directory: {mkdir_result}")

    # Upload file
    # upload_result = client.files.upload(
    #     file_path="/local/path/file.txt",
    #     remote_path="/home/user/data/",
    # )
    # print(f"Upload result: {upload_result}")

    # Download file
    # content = client.files.download(remote_path="/home/user/data/file.txt")
    # print(f"Downloaded {len(content)} bytes")

    # Copy files
    # copy_result = client.files.copy(
    #     src_paths=["/home/user/file1.txt"],
    #     dest_path="/home/user/backup/",
    # )

    # Compress files
    # compress_result = client.files.compress(
    #     paths=["/home/user/data/"],
    #     output_name="backup.zip",
    # )

    # ==================== Organization ====================
    print("\n" + "=" * 50)
    print("Organization Examples")
    print("=" * 50)

    # Get department tree
    deps_result = client.organization.get_departments()
    print(f"Departments: {deps_result}")

    # Get users
    users_result = client.organization.get_users(page=1, page_size=10)
    print(f"Users: {users_result}")

    # Create user
    # create_user_result = client.organization.create_user(
    #     username="newuser",
    #     chusername="新用户",
    #     password="your_password",
    #     dep="engineering",
    # )

    # ==================== Applications ====================
    print("\n" + "=" * 50)
    print("Applications Examples")
    print("=" * 50)

    # Get all applications
    apps_result = client.apps.list_all()
    print(f"Applications: {apps_result}")

    # Get application URL
    # url_result = client.apps.get_url(app_name="fluent")
    # print(f"Application URL: {url_result}")

    # ==================== Logout ====================
    print("\n" + "=" * 50)
    print("Logout")
    print("=" * 50)

    logout_result = client.auth.logout()
    print(f"Logout result: {logout_result['message']}")

    # Close client
    client.close()


def context_manager_example():
    """Example using context manager."""
    print("\n" + "=" * 50)
    print("Context Manager Example")
    print("=" * 50)

    with AppformClient(base_url="https://your-appform-server.com") as client:
        client.auth.login(username="your_username", password="your_password")

        jobs = client.jobs.list_jobs(page=1, page_size=5)
        print(f"Found {jobs['data'].get('total', 0)} jobs")

        # Session automatically closed on exit


def access_key_example():
    """Example using AccessKey authentication."""
    print("\n" + "=" * 50)
    print("AccessKey Authentication Example")
    print("=" * 50)

    # Method 1: Initialize with AccessKey
    client = AppformClient(
        base_url="https://your-appform-server.com",
        access_key="your_access_key",
        access_key_secret="your_access_key_secret",
        username="your_username",
    )

    # Check authentication status
    if client.auth.is_authenticated():
        print("Client is authenticated")

    if client.auth.is_access_key_authenticated():
        print("Using AccessKey authentication")

    # Make API calls - the SDK automatically generates:
    # - signature: HmacSHA256(#accessKey#username#currentTimeMillis#, accessKeySecret)
    # - currentTimeMillis: current timestamp
    # Headers sent: accessKey, username, signature, currentTimeMillis
    # Note: accessKeySecret is NOT sent in headers (used only for signature)
    jobs = client.jobs.list_jobs(page=1, page_size=5)
    print(f"Found {jobs['data'].get('total', 0)} jobs")

    client.close()

    # Method 2: Set AccessKey after initialization
    print("\n--- Method 2: Set AccessKey after initialization ---")
    client = AppformClient(base_url="https://your-appform-server.com")

    client.auth.set_access_key(
        access_key="your_access_key",
        access_key_secret="your_access_key_secret",
        username="your_username",
    )

    # Now all requests will use AccessKey authentication
    ping_result = client.auth.ping()
    print(f"Ping result: {ping_result}")

    # Clear AccessKey credentials
    client.auth.clear_access_key()
    print("AccessKey credentials cleared")

    client.close()


def signature_example():
    """Example of manual signature generation."""
    from appform_sdk import SignatureGenerator

    print("\n" + "=" * 50)
    print("Signature Generation Example")
    print("=" * 50)

    # Generate signature manually
    signature, timestamp = SignatureGenerator.generate_signature(
        access_key="your_access_key",
        access_key_secret="your_access_key_secret",
        username="your_username",
    )
    print(f"Signature: {signature}")
    print(f"Timestamp: {timestamp}")

    # Generate complete auth headers
    headers = SignatureGenerator.generate_auth_headers(
        access_key="your_access_key",
        access_key_secret="your_access_key_secret",
        username="your_username",
    )
    print(f"Auth headers: {headers}")


def error_handling_example():
    """Example of error handling."""
    from appform_sdk.exceptions import APIError, AppformError, AuthenticationError

    print("\n" + "=" * 50)
    print("Error Handling Example")
    print("=" * 50)

    client = AppformClient(base_url="https://your-appform-server.com")

    try:
        client.auth.login(username="your_username", password="wrong_password")
    except AuthenticationError as e:
        print(f"Authentication failed: {e.message}")
    except APIError as e:
        print(f"API error (status {e.status_code}): {e.message}")
    except AppformError as e:
        print(f"General error: {e.message}")


def encryption_example():
    """Example of AES encryption."""
    from appform_sdk import AESEncryptor

    print("\n" + "=" * 50)
    print("Encryption Example")
    print("=" * 50)

    encryptor = AESEncryptor()

    # Encrypt username for token login
    encrypted = encryptor.encrypt_username("myuser")
    print(f"Encrypted: {encrypted}")

    # Decrypt
    decrypted = encryptor.decrypt_username(encrypted)
    print(f"Username: {decrypted}")


if __name__ == "__main__":
    # Uncomment to run examples
    # main()
    # context_manager_example()
    # error_handling_example()
    # encryption_example()
    # access_key_example()
    # signature_example()
    # config_example()

    print("Appform SDK Examples")
    print("Edit the script to configure your server URL and credentials")
    print("Then uncomment the example functions you want to run")
    print("\nAvailable examples:")
    print("  - main(): Full API usage example")
    print("  - context_manager_example(): Using context manager")
    print("  - error_handling_example(): Error handling")
    print("  - encryption_example(): AES encryption")
    print("  - access_key_example(): AccessKey authentication")
    print("  - signature_example(): Manual signature generation")
    print("  - config_example(): Configuration management")
