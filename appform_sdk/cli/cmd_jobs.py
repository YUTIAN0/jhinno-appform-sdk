"""Jobs command handler."""

import sys

from appform_sdk.cli.common import (
    check_is_directory,
    confirm_overwrite,
    create_client,
    output_result,
    remote_file_exists,
)
from appform_sdk.cli.job_submit import (
    handle_jobs_submit,
    load_pm,
    print_app_params,
    print_apps_table,
)
from appform_sdk.compute import (
    execute_on_compute_node,
    get_head_node,
    load_compute_config,
    resolve_app_config,
)
from appform_sdk.config import Config
from appform_sdk.files import parse_size


def handle_jobs_command(args, submit_extra_args=None):
    # --- Commands that don't need API client ---
    if args.jobs_command in ("apps", "params", "submit"):
        pm = load_pm(args)

        if args.jobs_command == "apps":
            apps = pm.list_apps()
            if args.output == "json":
                output_result(
                    {"applications": apps, "config_file": pm.config_file},
                    args.output,
                    "jobs.apps",
                )
            else:
                print_apps_table(apps)
                if pm.config_file:
                    print(f"\nConfig: {pm.config_file}")
            return

        elif args.jobs_command == "params":
            profile = pm.get_profile(args.app_id)
            if not profile:
                available = [a["app_id"] for a in pm.list_apps()]
                print(
                    f"Error: Unknown application '{args.app_id}'. Available: {', '.join(available)}",
                    file=sys.stderr,
                )
                sys.exit(1)
            if args.output == "json":
                output_result(profile.to_dict(), args.output, "jobs.params")
            else:
                print_app_params(profile)
            return

        elif args.jobs_command == "submit":
            result = handle_jobs_submit(pm, submit_extra_args or [], args.output)
            if result is None:
                return  # dry-run, list-apps, or help was shown
            app_id, params = result
            client = create_client(args)
            try:
                resp = client.jobs.submit(app_id=app_id, params=params)
                output_result(resp, args.output, "jobs.submit")
            finally:
                client.close()
            return

    # --- Commands that need API client ---
    client = create_client(args)

    try:
        if args.jobs_command == "submit-raw":
            import json

            params = json.loads(args.params)
            result = client.jobs.submit(app_id=args.app_id, params=params)
            output_result(result, args.output, "jobs.submit")
        elif args.jobs_command == "list":
            status_filter = [args.status] if args.status else None
            result = client.jobs.list_jobs(
                page=args.page,
                page_size=args.page_size,
                name_filter=args.name,
                status_filter=status_filter,
            )
            output_result(result, args.output, "jobs.list")
        elif args.jobs_command == "status":
            if args.status and args.status.lower() != "all":
                status_filter = [args.status.upper()]
            else:
                status_filter = None
            result = client.jobs.list_jobs(
                page=args.page,
                page_size=args.page_size,
                status_filter=status_filter,
            )
            output_result(result, args.output, "jobs.list")
        elif args.jobs_command == "get":
            result = client.jobs.get_job(args.job_id)
            output_result(result, args.output, "jobs.get")
        elif args.jobs_command == "stop":
            result = client.jobs.stop(args.job_id)
            output_result(result, args.output, "jobs.stop")
        elif args.jobs_command == "suspend":
            result = client.jobs.suspend(args.job_id)
            output_result(result, args.output, "jobs.suspend")
        elif args.jobs_command == "resume":
            result = client.jobs.resume(args.job_id)
            output_result(result, args.output, "jobs.resume")
        elif args.jobs_command == "output":
            result = client.jobs.get_output(args.job_id)
            output_result(result, args.output, "jobs.output")
        elif args.jobs_command == "files":
            jobs_files_cmd = getattr(args, "jobs_files_command", None)
            if jobs_files_cmd:
                handle_jobs_files_command(args, client=client)
            else:
                result = client.jobs.get_files(args.job_id)
                output_result(result, args.output, "jobs.files")
        elif args.jobs_command == "history":
            result = client.jobs.get_history(args.job_id)
            output_result(result, args.output, "jobs.history")
        elif args.jobs_command == "history-page":
            result = client.jobs.list_history(page=args.page, page_size=args.page_size)
            output_result(result, args.output, "jobs.list")
        elif args.jobs_command == "delete":
            result = client.jobs.delete_job(args.job_id)
            output_result(result, args.output, "jobs.delete")
        elif args.jobs_command == "form":
            result = client.jobs.get_form(args.app_id)
            output_result(result, args.output, "jobs.form")
        elif args.jobs_command == "tooltip":
            result = client.jobs.get_tooltip()
            output_result(result, args.output, "jobs.tooltip")
    finally:
        client.close()


# ---------------------------------------------------------------------------
# Jobs files handler (file operations within a job's working directory)
# ---------------------------------------------------------------------------


def handle_jobs_files_command(args, client=None):
    """Handle file operations within a job's working directory."""
    own_client = client is None
    if client is None:
        client = create_client(args)
    config = Config(
        config_file=getattr(args, "config_file", None),
        env=getattr(args, "env", None),
    )

    # Get job's working directory
    job_info = client.jobs.get_job(args.job_id)
    job_cwd = job_info.get("data", {}).get("cwd", "/")

    def resolve_jobs_path(path):
        """Resolve a path relative to job cwd if not absolute."""
        if path and path.startswith("/"):
            return path
        if not path:
            return job_cwd
        return f"{job_cwd.rstrip('/')}/{path}"

    try:
        method = (
            getattr(args, "default_method", None) or config.default_method or "http"
        )
        cmd = args.jobs_files_command

        try:
            if cmd == "ls":
                cmd_method = getattr(args, "method", None) or method
                remote = resolve_jobs_path(args.path)
                hidden = getattr(args, "hidden", False)
                list_template = (
                    "files.list.sftp" if cmd_method == "sftp" else "files.list"
                )
                if args.list_all:
                    items = client.files.list_all(
                        path=remote, transfer_method=cmd_method, hidden=hidden
                    )
                    result = {"data": items, "path": remote, "count": len(items)}
                else:
                    result = client.files.list(
                        path=remote,
                        page=args.page,
                        page_size=args.page_size,
                        transfer_method=cmd_method,
                        hidden=hidden,
                    )
                output_result(result, args.output, list_template)

            elif cmd == "cp":
                cmd_method = getattr(args, "method", None) or method
                result = client.files.copy(
                    src_path=resolve_jobs_path(args.src),
                    dest_dir=resolve_jobs_path(args.dest),
                    transfer_method=cmd_method,
                )
                output_result(result, args.output, "files.copy")

            elif cmd == "mv":
                cmd_method = getattr(args, "method", None) or method
                result = client.files.move(
                    src_path=resolve_jobs_path(args.src),
                    dest_dir=resolve_jobs_path(args.dest),
                    transfer_method=cmd_method,
                )
                output_result(result, args.output, "files.rename")

            elif cmd == "rm":
                cmd_method = getattr(args, "method", None) or method
                result = client.files.delete(
                    path=resolve_jobs_path(args.path), transfer_method=cmd_method
                )
                output_result(result, args.output, "files.delete")

            elif cmd == "mkdir":
                force = not args.no_force
                cmd_method = getattr(args, "method", None) or method
                result = client.files.mkdir(
                    path=resolve_jobs_path(args.path),
                    force=force,
                    transfer_method=cmd_method,
                )
                output_result(result, args.output, "files.mkdir")

            elif cmd == "put":
                _handle_jobs_files_put(client, config, args, resolve_jobs_path)
                return  # put handles its own client.close()

            elif cmd == "get":
                remote = resolve_jobs_path(args.remote)
                local = args.local
                cmd_method = getattr(args, "method", None) or method
                cs_arg = getattr(args, "chunk_size", None)
                chunk_size = _get_chunk_size(cs_arg, config)

                # Check if remote path is a directory
                is_dir = check_is_directory(client, cmd_method, remote)

                if is_dir:
                    from pathlib import Path

                    from appform_sdk.files import _ProgressTracker

                    local_path = Path(local)
                    save_dir = local_path if local_path.is_dir() else Path(local)
                    progress = _ProgressTracker(label="Downloading")
                    results = client.files.download_directory(
                        remote_dir=remote,
                        local_dir=str(save_dir),
                        on_progress=progress.update,
                        chunk_size=chunk_size,
                        transfer_method=cmd_method,
                    )
                    progress.finish()
                    downloaded = [r for r in results if r.get("status") == "ok"]
                    print(f"Downloaded {len(downloaded)} file(s) to {save_dir}")
                    if args.output == "json":
                        output_result(
                            {
                                "downloaded": results,
                                "count": len(downloaded),
                                "local_dir": str(save_dir),
                            },
                            args.output,
                            "files.download",
                        )
                else:
                    from pathlib import Path

                    from appform_sdk.files import _ProgressTracker

                    local_path = Path(local)
                    if local_path.is_dir() or local == ".":
                        save_path = str(local_path / Path(remote).name)
                    else:
                        save_path = local
                    progress = _ProgressTracker(label="Downloading")
                    client.files.download(
                        remote_path=remote,
                        local_path=save_path,
                        on_progress=progress.update,
                        chunk_size=chunk_size,
                        transfer_method=cmd_method,
                    )
                    progress.finish()
                    print(f"Downloaded to {save_path}")

            elif cmd == "cat":
                cmd_method = getattr(args, "method", None) or method
                head = args.head
                tail = args.tail
                start = args.start
                end = args.end
                all_lines = getattr(args, "all_lines", False)

                if args.lines:
                    start, end = _parse_lines_range(args.lines, client)

                lines = client.files.cat(
                    remote_path=resolve_jobs_path(args.path),
                    head=head,
                    tail=tail,
                    start=start,
                    end=end,
                    encoding=args.encoding,
                    all_lines=all_lines,
                )
                for line in lines:
                    print(line)

            elif cmd == "tailf":
                tail_pid, channel = client.sftp.tailf(
                    remote_path=resolve_jobs_path(args.path),
                    encoding=args.encoding,
                )
                try:
                    client.sftp.kill_tail(tail_pid)
                except Exception:
                    pass

            elif cmd == "custom":
                handle_jobs_files_custom(args, job_info, client)
            else:
                print(f"Error: Unknown files command: {cmd}", file=sys.stderr)
                sys.exit(1)

        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            msg = str(e)
            print(f"Error: {msg}", file=sys.stderr)
            sys.exit(1)
    finally:
        if own_client:
            client.close()


# ---------------------------------------------------------------------------
# Jobs files custom (compute node SSH operations)
# ---------------------------------------------------------------------------


def handle_jobs_files_custom(args, job_info, client):
    """Compute node file operations via SSH (ls/get/cat/tailf)."""
    # 1. Get subcommand
    subcommand = getattr(args, "custom_command", None)
    if not subcommand:
        print(
            "Error: Missing subcommand. Use: ls, get, cat, or tailf.",
            file=sys.stderr,
        )
        print(
            "Usage: appform jobs files <job_id> custom <ls|get|cat|tailf> [args]",
            file=sys.stderr,
        )
        client.close()
        sys.exit(1)

    # 2. Load compute config
    try:
        compute_data = load_compute_config()
    except Exception as e:
        print(f"Error: Failed to load compute config: {e}", file=sys.stderr)
        print(
            "Create ~/.appform/compute.yaml or set APPFORM_COMPUTE_CONFIG.",
            file=sys.stderr,
        )
        client.close()
        sys.exit(1)

    # 3. Get job info from API
    data = job_info.get("data", {})
    app_name = data.get("appName", "")
    job_status = data.get("status", "")

    # 4. Check app is configured
    apps_cfg = compute_data.get("compute_config", {}).get("applications", {})
    if app_name and app_name not in apps_cfg:
        configured = ", ".join(apps_cfg.keys()) if apps_cfg else "(none)"
        print(
            f"Error: Application '{app_name}' is not configured in compute.yaml.",
            file=sys.stderr,
        )
        print(f"Configured applications: {configured}", file=sys.stderr)
        print(
            f"Add '{app_name}' to ~/.appform/compute.yaml applications section.",
            file=sys.stderr,
        )
        client.close()
        sys.exit(1)

    app_cfg = resolve_app_config(compute_data, app_name)

    # 5. Check job status
    if job_status != "RUN":
        print(
            f"Error: Job is '{job_status}'. Only running jobs are supported.",
            file=sys.stderr,
        )
        client.close()
        sys.exit(1)

    exec_host_raw = data.get("executionHost", []) or data.get("host", "")
    if not exec_host_raw:
        print("Error: No execution host found for this job.", file=sys.stderr)
        client.close()
        sys.exit(1)
    head_node = get_head_node(exec_host_raw)

    # Build subcommand args
    subcommand_args = []
    if subcommand == "ls":
        subcommand_args = [args.path] if args.path else []
    elif subcommand == "get":
        subcommand_args = [args.remote]
        if args.local and args.local != ".":
            subcommand_args.append(args.local)
    elif subcommand in ("cat", "tailf"):
        subcommand_args = [args.path]

    # Get SSH credentials
    config = Config(
        config_file=getattr(args, "config_file", None),
        env=getattr(args, "env", None),
    )
    ssh_user = config.sftp_username or config.username
    ssh_pass = config.sftp_password or config.password
    ssh_key = config.sftp_key_file
    ssh_key_pass = config.sftp_key_password

    connect_kwargs = {
        "username": ssh_user,
        "password": ssh_pass,
        "key_filename": ssh_key,
        "key_password": ssh_key_pass,
        "config": config,
    }

    ssh_kwargs = {"connect_kwargs": connect_kwargs}
    if app_cfg["mode"] == "via_gateway":
        ssh_kwargs["gateway_host"] = config.sftp_host
        ssh_kwargs["gateway_port"] = config.sftp_port

    if subcommand == "cat":
        ssh_kwargs["head"] = getattr(args, "head", None)
        ssh_kwargs["tail"] = getattr(args, "tail", None)

    encoding = getattr(args, "encoding", "utf-8")
    exit_code = execute_on_compute_node(
        app_cfg=app_cfg,
        head_node=head_node,
        job_id=args.job_id,
        subcommand=subcommand,
        subcommand_args=subcommand_args,
        ssh_kwargs=ssh_kwargs,
        encoding=encoding,
    )
    if exit_code:
        sys.exit(exit_code)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _get_chunk_size(cs_arg, config):
    if cs_arg:
        return parse_size(cs_arg)
    return config.chunk_size or 104857600


def _handle_jobs_files_put(client, config, args, resolve_jobs_path):
    """Handle the 'jobs files put' subcommand.

    Does NOT close client — caller is responsible for cleanup.
    Returns True if the caller should skip its finally-block close (e.g. early exit).
    """
    from pathlib import Path

    from appform_sdk.files import _ProgressTracker

    local = args.local
    remote = resolve_jobs_path(args.remote)
    force = getattr(args, "force", False)
    cmd_method = getattr(args, "method", None) or (
        getattr(args, "default_method", None) or config.default_method or "http"
    )

    local_path = Path(local)
    cs_arg = getattr(args, "chunk_size", None)
    chunk_size = _get_chunk_size(cs_arg, config)

    if local_path.is_dir():
        progress = _ProgressTracker(label="Uploading")
        if cmd_method == "sftp":
            results = client.files.upload_directory(
                local_dir=local,
                remote_dir=remote,
                on_progress=progress.update,
                check_exists=lambda fname: remote_file_exists(client, remote, fname)
                and not force,
                confirm=confirm_overwrite if not force else None,
                chunk_size=chunk_size,
                transfer_method=cmd_method,
            )
        else:
            results = client.files.upload_directory(
                local_dir=local,
                remote_dir=remote,
                on_progress=progress.update,
                check_exists=lambda fname: remote_file_exists(client, remote, fname)
                and not force,
                confirm=confirm_overwrite,
                chunk_size=chunk_size,
                transfer_method=cmd_method,
            )
        progress.finish()
        uploaded = [r for r in results if r.get("result")]
        print(f"Uploaded {len(uploaded)} file(s) to {remote}")
        if args.output == "json":
            output_result(
                {
                    "uploaded": results,
                    "count": len(uploaded),
                    "remote_dir": remote,
                },
                args.output,
                "files.upload",
            )
    elif local_path.is_file():
        fname = local_path.name
        saved = f"{remote.rstrip('/')}/{fname}"
        if (
            cmd_method == "http"
            and not force
            and remote_file_exists(client, remote, fname)
        ):
            if not confirm_overwrite(fname):
                print("Upload cancelled.")
                return
        progress = _ProgressTracker(label="Uploading")
        result = client.files.upload(
            file_path=local,
            remote_path=remote,
            on_progress=progress.update,
            chunk_size=chunk_size,
            transfer_method=cmd_method,
        )
        progress.finish()
        print(f"Uploaded to {saved}")
        if args.output == "json":
            output_result(result, args.output, "files.upload")
    else:
        print(f"Error: Local path not found: {local}", file=sys.stderr)
        sys.exit(1)


def _parse_lines_range(lines_str, client):
    """Parse --lines '10-20' or '10-' and return (start, end)."""
    parts = lines_str.split("-", 1)
    if len(parts) == 2:
        start = None
        end = None
        if parts[0]:
            try:
                start = int(parts[0])
            except ValueError:
                print(
                    f"Error: --lines start must be a number, got: {parts[0]!r}",
                    file=sys.stderr,
                )
                client.close()
                sys.exit(1)
        if parts[1]:
            try:
                end = int(parts[1])
            except ValueError:
                print(
                    f"Error: --lines end must be a number, got: {parts[1]!r}",
                    file=sys.stderr,
                )
                client.close()
                sys.exit(1)
        return start, end
    elif len(parts) == 1:
        try:
            start = int(parts[0])
        except ValueError:
            print(
                f"Error: --lines value must be a number, got: {parts[0]!r}",
                file=sys.stderr,
            )
            client.close()
            sys.exit(1)
        return start, None
    return None, None
