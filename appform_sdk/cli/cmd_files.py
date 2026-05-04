"""Files command handler."""

import sys

from appform_sdk.cli.common import (
    confirm_overwrite,
    create_client,
    output_result,
    remote_file_exists,
    resolve_home_in_path,
    resolve_remote_path,
)
from appform_sdk.config import Config
from appform_sdk.files import _ProgressTracker, parse_size


def handle_files_command(args):
    client = create_client(args)
    config = Config(config_file=getattr(args, "config_file", None))

    try:
        method = (
            getattr(args, "default_method", None) or config.default_method or "http"
        )

        try:
            if args.files_command == "ls":
                cmd_method = getattr(args, "method", None) or method
                path = resolve_home_in_path(client, args.path, cmd_method)
                hidden = getattr(args, "hidden", False)
                list_template = (
                    "files.list.sftp" if cmd_method == "sftp" else "files.list"
                )
                if args.list_all:
                    items = client.files.list_all(
                        path=path, transfer_method=cmd_method, hidden=hidden
                    )
                    result = {"data": items, "path": path, "count": len(items)}
                else:
                    result = client.files.list(
                        path=path,
                        page=args.page,
                        page_size=args.page_size,
                        transfer_method=cmd_method,
                        hidden=hidden,
                    )
                output_result(result, args.output, list_template)

            elif args.files_command == "cp":
                cmd_method = getattr(args, "method", None) or method
                src = resolve_home_in_path(client, args.src, cmd_method)
                dest = resolve_home_in_path(client, args.dest, cmd_method)
                result = client.files.copy(
                    src_path=src, dest_dir=dest, transfer_method=cmd_method
                )
                output_result(result, args.output, "files.copy")

            elif args.files_command == "mv":
                cmd_method = getattr(args, "method", None) or method
                src = resolve_home_in_path(client, args.src, cmd_method)
                dest = resolve_home_in_path(client, args.dest, cmd_method)
                result = client.files.move(
                    src_path=src, dest_dir=dest, transfer_method=cmd_method
                )
                output_result(result, args.output, "files.rename")

            elif args.files_command == "rm":
                cmd_method = getattr(args, "method", None) or method
                path = resolve_home_in_path(client, args.path, cmd_method)
                result = client.files.delete(path=path, transfer_method=cmd_method)
                output_result(result, args.output, "files.delete")

            elif args.files_command == "mkdir":
                force = not args.no_force
                cmd_method = getattr(args, "method", None) or method
                path = resolve_home_in_path(client, args.path, cmd_method)
                result = client.files.mkdir(
                    path=path, force=force, transfer_method=cmd_method
                )
                output_result(result, args.output, "files.mkdir")

            elif args.files_command == "put":
                _handle_put(client, config, args, method)
                return  # put handles its own client.close()

            elif args.files_command == "get":
                _handle_get(client, config, args, method)

            elif args.files_command == "compress":
                cmd_method = getattr(args, "method", None) or method
                path = resolve_home_in_path(client, args.source, cmd_method)
                target = resolve_home_in_path(client, args.target, cmd_method)
                result = client.files.compress(source_dir=path, target_path=target)
                output_result(result, args.output, "files.compress")

            elif args.files_command == "uncompress":
                cmd_method = getattr(args, "method", None) or method
                archive = resolve_home_in_path(client, args.archive, cmd_method)
                dest = resolve_home_in_path(client, args.dest, cmd_method)
                result = client.files.uncompress(
                    archive_path=archive,
                    dest_dir=dest,
                    password=args.password,
                )
                output_result(result, args.output, "files.uncompress")

            elif args.files_command == "conf":
                if args.get_levels:
                    result = client.files.get_confidentiality_levels()
                    output_result(result, args.output, "files.conf")
                elif args.set_conf:
                    path = resolve_home_in_path(client, args.set_conf[0], "http")
                    result = client.files.set_confidentiality(
                        path=path, level=args.set_conf[1]
                    )
                    output_result(result, args.output, "files.conf")

            elif args.files_command == "cat":
                _handle_cat(client, args, method)

            elif args.files_command == "tailf":
                path = resolve_home_in_path(client, args.path, "sftp")
                tail_pid, channel = client.sftp.tailf(
                    remote_path=path, encoding=args.encoding
                )
                try:
                    client.sftp.kill_tail(tail_pid)
                except Exception:
                    pass

        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            msg = str(e)
            print(f"Error: {msg}", file=sys.stderr)
            sys.exit(1)
    finally:
        client.close()


# ---------------------------------------------------------------------------
# Sub-handlers
# ---------------------------------------------------------------------------


def _handle_put(client, config, args, method):
    """Handle the 'files put' subcommand. Handles its own client.close()."""
    from pathlib import Path

    local = args.local
    remote = args.remote
    force = getattr(args, "force", False)
    cmd_method = getattr(args, "method", None) or method
    if remote is None:
        remote = config.default_remote_path or "/"
    remote = resolve_remote_path(remote, config)
    remote = resolve_home_in_path(client, remote, cmd_method)

    local_path = Path(local)
    cs_arg = getattr(args, "chunk_size", None)
    if cs_arg:
        chunk_size = parse_size(cs_arg)
    else:
        chunk_size = config.chunk_size or 104857600

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
                client.close()
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
        client.close()
        sys.exit(1)

    client.close()


def _handle_get(client, config, args, method):
    """Handle the 'files get' subcommand."""
    from pathlib import Path

    remote = args.remote
    local = args.local
    cmd_method = getattr(args, "method", None) or method
    remote = resolve_home_in_path(client, remote, cmd_method)
    cs_arg = getattr(args, "chunk_size", None)
    if cs_arg:
        chunk_size = parse_size(cs_arg)
    else:
        chunk_size = config.chunk_size or 104857600

    is_dir = _check_is_directory(client, cmd_method, remote)

    if is_dir:
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


def _handle_cat(client, args, method):
    """Handle the 'files cat' subcommand."""
    head = args.head
    tail = args.tail
    start = args.start
    end = args.end
    all_lines = getattr(args, "all_lines", False)

    if args.lines:
        parts = args.lines.split("-", 1)
        if len(parts) == 2:
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
            else:
                end = None
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

    path = resolve_home_in_path(client, args.path, "sftp")
    lines = client.files.cat(
        remote_path=path,
        head=head,
        tail=tail,
        start=start,
        end=end,
        encoding=args.encoding,
        all_lines=all_lines,
    )
    for line in lines:
        print(line)


def _check_is_directory(client, cmd_method, remote):
    """Check if a remote path is a directory."""
    if cmd_method == "http":
        try:
            items = client.files.list(path=remote, page=1, page_size=1)
            data = items.get("data", [])
            if isinstance(data, dict):
                file_list = data.get("files", data.get("records", []))
            elif isinstance(data, list):
                file_list = data
            else:
                file_list = []
            return len(file_list) > 0 and file_list[0].get("fileType") == "directory"
        except Exception:
            return False
    else:
        return remote.endswith("/")
