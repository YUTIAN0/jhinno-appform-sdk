"""
SFTP file transfer module for Appform SDK.

Provides SFTP-based upload/download as an alternative to HTTP API file transfer.
Requires paramiko: pip install jhinno-appform-sdk[sftp]
"""

import io
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse


def _require_paramiko():
    """Lazy-import paramiko with a helpful error message if missing."""
    try:
        import paramiko
    except ImportError:
        raise ImportError(
            "paramiko is required for SFTP operations. "
            "Install it with: pip install jhinno-appform-sdk[sftp]"
        )
    return paramiko


from .exceptions import SFTPError  # noqa: E402

# Characters/patterns that would allow command injection in shell commands
_DANGEROUS_PATH_CHARS = re.compile(r"""[;&|`(){}$\\><'" ]""")


def _open_proxy_socket(proxy_url: str, target_host: str, target_port: int):
    """Create a socket through a proxy to a target host.

    Supports:
    - SOCKS  (socks5://, socks4://)  — requires PySocks
    - HTTP CONNECT tunnel (http://, https://) — stdlib only

    Returns a connected socket.
    """
    from urllib.parse import urlparse

    parsed = urlparse(proxy_url)

    if parsed.scheme in ("socks5", "socks4"):
        try:
            import socks
        except ImportError:
            raise ImportError(
                "PySocks is required for SOCKS proxy support. "
                "Install with: pip install jhinno-appform-sdk[proxy]"
            )
        sock = socks.socksocket()
        proxy_type = socks.SOCKS5 if parsed.scheme == "socks5" else socks.SOCKS4
        sock.set_proxy(
            proxy_type,
            parsed.hostname,
            parsed.port,
            username=parsed.username,
            password=parsed.password,
        )
        sock.connect((target_host, target_port))
        return sock

    if parsed.scheme in ("http", "https"):
        proxy_auth = None
        if parsed.username:
            import base64

            proxy_auth = base64.b64encode(
                f"{parsed.username}:{parsed.password or ''}".encode()
            ).decode()

        conn_cls = (
            __import__("http.client", fromlist=["HTTPSConnection"]).HTTPSConnection
            if parsed.scheme == "https"
            else __import__("http.client", fromlist=["HTTPConnection"]).HTTPConnection
        )
        conn = conn_cls(parsed.hostname, parsed.port, timeout=30)
        headers = {}
        if proxy_auth:
            headers["Proxy-Authorization"] = f"Basic {proxy_auth}"
        conn.set_tunnel(target_host, target_port, headers=headers)
        conn.connect()
        return conn.sock

    raise ValueError(
        f"Unsupported proxy scheme: '{parsed.scheme}'. "
        "Use http://, https://, socks5://, or socks4://"
    )


def _validate_path(path: str) -> str:
    """Validate a file/directory path for use in shell commands.

    Allows glob patterns (* ? [...]) but rejects characters that could
    be used for command injection (semicolons, pipes, redirects,
    subshells, variable expansion, backslashes, quotes, spaces).

    Returns the unchanged path if safe. Raises SFTPError if dangerous.
    """
    if ".." in path:
        raise SFTPError(f"Directory traversal not allowed in path: {path!r}")
    if _DANGEROUS_PATH_CHARS.search(path):
        raise SFTPError(
            f"Invalid characters in path: {path!r}. "
            "Paths must not contain shell metacharacters or spaces "
            "(; & | ( ) `{ } $ \\ ' \" space)."
        )
    if "\n" in path:
        raise SFTPError(f"Newline not allowed in path: {path!r}")
    return path


class SFTPClientManager:
    """Manages a paramiko Transport + SFTP session with lazy init and reuse."""

    def __init__(
        self,
        host: str,
        port: int = 22,
        username: Optional[str] = None,
        password: Optional[str] = None,
        key_filename: Optional[str] = None,
        key_password: Optional[str] = None,
        timeout: int = 30,
        proxy_url: Optional[str] = None,
        auto_add_host_key: bool = False,
    ):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._key_filename = key_filename
        self._key_password = key_password
        self._timeout = timeout
        self._proxy_url = proxy_url
        self._auto_add_host_key = auto_add_host_key

        self._transport = None
        self._sftp = None
        self._ssh_client = None

    @property
    def sftp(self):
        """Lazy-init SFTP client, reusing if already connected."""
        if self._sftp is None or getattr(self._sftp, "closed", True):
            self._connect()
        return self._sftp

    def _connect(self):
        paramiko = _require_paramiko()

        if not self._key_filename and not self._password:
            raise SFTPError(
                "SFTP requires either password or sftp_key_file authentication."
            )

        sock = None
        if self._proxy_url:
            sock = _open_proxy_socket(self._proxy_url, self._host, self._port)

        ssh_client = paramiko.SSHClient()
        if self._auto_add_host_key:
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:
            known_hosts = os.path.expanduser("~/.ssh/known_hosts")
            try:
                ssh_client.load_host_keys(known_hosts)
            except (FileNotFoundError, paramiko.hostkeys.SSHException):
                pass

            class _PromptAndSavePolicy(paramiko.MissingHostKeyPolicy):
                def missing_host_key(self, client, hostname, key):
                    key_type = key.get_name()
                    fingerprint = ":".join(
                        f"{b:02x}" for b in key.get_fingerprint()
                    )
                    try:
                        answer = input(
                            f"The authenticity of host '{hostname}' can't be established.\n"
                            f"{key_type} key fingerprint is {fingerprint}.\n"
                            f"Are you sure you want to continue connecting (yes/no)? "
                        )
                    except (EOFError, KeyboardInterrupt):
                        answer = "no"
                    if answer.strip().lower() in ("yes", "y"):
                        client.get_host_keys().add(hostname, key.get_name(), key)
                        try:
                            os.makedirs(os.path.dirname(known_hosts), exist_ok=True)
                            client.save_host_keys(known_hosts)
                        except OSError:
                            pass
                    else:
                        raise paramiko.SSHException(
                            f"Host key verification failed for {hostname}"
                        )

            ssh_client.set_missing_host_key_policy(_PromptAndSavePolicy())

        try:
            ssh_client.connect(
                hostname=self._host,
                port=self._port,
                username=self._username,
                password=self._password,
                key_filename=self._key_filename,
                passphrase=self._key_password,
                timeout=self._timeout,
                sock=sock,
                look_for_keys=False,
                allow_agent=False,
            )
        except Exception as e:
            try:
                ssh_client.close()
            except Exception:
                pass
            raise SFTPError(f"SFTP connection failed to {self._host}:{self._port}: {e}")
        self._ssh_client = ssh_client
        self._transport = ssh_client.get_transport()
        self._sftp = paramiko.SFTPClient.from_transport(self._transport)

    def close(self):
        try:
            if self._sftp:
                self._sftp.close()
        except Exception:
            pass
        if self._transport:
            try:
                self._transport.close()
            except Exception:
                pass
        if self._ssh_client:
            try:
                self._ssh_client.close()
            except Exception:
                pass
        self._sftp = None
        self._transport = None
        self._ssh_client = None


def _mkdir_recursive(sftp_client, path: str):
    """Create remote directories recursively (manual, no recursive=True dependency)."""
    # SSH_FX_NO_SUCH_FILE = 2, SSH_FX_PERMISSION_DENIED = 4
    NO_SUCH_FILE = 2
    parts = path.strip("/").split("/")
    current = ""
    for part in parts:
        current += "/" + part
        try:
            sftp_client.stat(current)
        except IOError as e:
            # Only skip if "no such file" (status 2). Other errors (permission denied, etc.) propagate.
            status = getattr(e, "errno", None) or (
                e.args[0] if getattr(e, "args", None) else None
            )
            if status != NO_SUCH_FILE:
                raise
            try:
                sftp_client.mkdir(current)
            except IOError as e2:
                raise SFTPError(f"Failed to create directory '{current}': {e2}")


class SFTPAPI:
    """SFTP-based file transfer with the same interface as HTTP FilesAPI."""

    def __init__(self, client):
        self._client = client
        self._manager: Optional[SFTPClientManager] = None

    def _get_manager(self) -> SFTPClientManager:
        if self._manager is None:
            c = self._client
            host = getattr(c, "_sftp_host", None) or (
                urlparse(c.base_url).hostname if c.base_url else None
            )
            if not host:
                raise SFTPError(
                    "SFTP host is not configured. "
                    "Set --sftp-host or APPFORM_SFTP_HOST or derive from base_url."
                )
            self._manager = SFTPClientManager(
                host=host,
                port=getattr(c, "_sftp_port", 22) or 22,
                username=getattr(c, "_sftp_username", None) or c.username,
                password=getattr(c, "_sftp_password", None),
                key_filename=getattr(c, "_sftp_key_file", None),
                key_password=getattr(c, "_sftp_key_password", None),
                timeout=getattr(c, "timeout", 30) or 30,
                proxy_url=getattr(c, "_sftp_proxy", None),
                auto_add_host_key=getattr(c, "auto_add_host_key", False),
            )
        return self._manager

    def get_home_dir(self) -> str:
        """Get remote user's home directory via SSH exec 'echo ~'."""
        manager = self._get_manager()
        _ = manager.sftp
        if manager._transport is None:
            raise SFTPError("SFTP transport not connected")
        channel = manager._transport.open_session()
        channel.settimeout(10)
        channel.exec_command("echo ~")
        home = channel.recv(4096).decode("utf-8", errors="replace").strip()
        channel.recv_exit_status()
        channel.close()
        if not home or home == "~":
            home = "/"
        return home

    def upload(
        self,
        file_path: str,
        remote_path: str,
        on_progress: Optional[Callable] = None,
        chunk_size: int = 104857600,
    ) -> Dict[str, Any]:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        sftp = self._get_manager().sftp
        remote_dir = remote_path.rstrip("/")
        fname = file_path.name
        remote_full = f"{remote_dir}/{fname}"

        # Ensure remote directory exists
        try:
            sftp.stat(remote_dir)
        except IOError:
            _mkdir_recursive(sftp, remote_dir)

        try:
            if on_progress:

                def callback(transferred, total, _fname=fname):
                    on_progress(_fname, transferred, total)

                sftp.put(str(file_path), remote_full, callback=callback)
            else:
                sftp.put(str(file_path), remote_full)
        except IOError as e:
            raise SFTPError(f"Failed to upload '{file_path}' to '{remote_full}': {e}")

        return {"data": {"file": fname, "remote": remote_full, "result": "success"}}

    def upload_directory(
        self,
        local_dir: str,
        remote_dir: str,
        on_progress: Optional[Callable] = None,
        check_exists: Optional[Callable] = None,
        confirm: Optional[Callable] = None,
        chunk_size: int = 104857600,
    ) -> List[Dict[str, Any]]:
        local_dir_path = Path(local_dir)
        if not local_dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {local_dir_path}")

        sftp = self._get_manager().sftp
        remote_dir = remote_dir.rstrip("/")

        # Create top-level remote directory
        try:
            sftp.stat(remote_dir)
        except IOError:
            _mkdir_recursive(sftp, remote_dir)

        files = sorted(f for f in local_dir_path.rglob("*") if f.is_file())
        total = len(files)
        results = []

        for idx, file_path in enumerate(files, 1):
            rel = file_path.relative_to(local_dir_path)
            parent = str(rel.parent)
            fname = file_path.name

            if parent == ".":
                target_dir = remote_dir
            else:
                target_dir = f"{remote_dir}/{parent.replace(os.sep, '/')}"

            # Create subdirectories
            if parent != ".":
                try:
                    sftp.stat(target_dir)
                except IOError:
                    _mkdir_recursive(sftp, target_dir)

            # Check overwrite
            skip = False
            if check_exists and check_exists(fname):
                if confirm and not confirm(fname):
                    results.append({"file": str(rel), "status": "skipped"})
                    skip = True

            if not skip:
                remote_full = f"{target_dir}/{fname}"
                try:
                    if on_progress:

                        def cb(transferred, total_b, _fname=fname):
                            on_progress(_fname, transferred, total_b)

                        sftp.put(str(file_path), remote_full, callback=cb)
                    else:
                        sftp.put(str(file_path), remote_full)

                    results.append(
                        {
                            "file": str(rel),
                            "remote": remote_full,
                            "result": "success",
                        }
                    )
                except Exception as e:
                    results.append(
                        {
                            "file": str(rel),
                            "remote": remote_full,
                            "status": "error",
                            "error": str(e),
                        }
                    )

            if on_progress:
                on_progress(str(rel), idx, total)

        return results

    def download(
        self,
        remote_path: str,
        local_path: Optional[str] = None,
        on_progress: Optional[Callable] = None,
        chunk_size: int = 104857600,
    ) -> Optional[bytes]:
        sftp = self._get_manager().sftp
        fname = Path(remote_path).name

        # Get remote file size for progress
        try:
            sftp.stat(remote_path)
        except IOError:
            raise FileNotFoundError(f"Remote file not found: {remote_path}")

        if local_path:
            local = Path(local_path)
            if local.is_dir():
                local = local / fname
            local.parent.mkdir(parents=True, exist_ok=True)

            if on_progress:

                def callback(transferred, total):
                    on_progress(fname, transferred, total)

                try:
                    sftp.get(remote_path, str(local), callback=callback)
                except IOError as e:
                    raise SFTPError(
                        f"Failed to download '{remote_path}' to '{local}': {e}"
                    )
            else:
                try:
                    sftp.get(remote_path, str(local))
                except IOError as e:
                    raise SFTPError(
                        f"Failed to download '{remote_path}' to '{local}': {e}"
                    )

            return None
        else:
            # Return bytes for small files
            buf = io.BytesIO()
            if on_progress:

                def callback(transferred, total):
                    on_progress(fname, transferred, total)

                try:
                    sftp.getfo(remote_path, buf, callback=callback)
                except IOError as e:
                    raise SFTPError(f"Failed to read remote file '{remote_path}': {e}")
            else:
                try:
                    sftp.getfo(remote_path, buf)
                except IOError as e:
                    raise SFTPError(f"Failed to read remote file '{remote_path}': {e}")
            return buf.getvalue()

    def download_directory(
        self,
        remote_dir: str,
        local_dir: str,
        on_progress: Optional[Callable] = None,
        chunk_size: int = 104857600,
    ) -> List[Dict[str, Any]]:
        sftp = self._get_manager().sftp
        local_base = Path(local_dir)
        local_base.mkdir(parents=True, exist_ok=True)

        remote_dir = remote_dir.rstrip("/")

        return _download_dir_recursive(
            sftp, remote_dir, local_base, on_progress, chunk_size
        )

    def list(
        self,
        path: str = "/",
        page: int = 1,
        page_size: int = 100,
        hidden: bool = False,
    ) -> Dict[str, Any]:
        """List remote directory contents via SFTP.

        Args:
            path: Directory path
            page: Page number
            page_size: Items per page
            hidden: Whether to show hidden files (starting with .)
        """
        sftp = self._get_manager().sftp
        items = []

        try:
            attr = sftp.stat(path)
            if stat.S_ISREG(attr.st_mode):
                # Path is a file — return single item
                name = Path(path).name
                items.append(
                    {
                        "fileName": name,
                        "path": path,
                        "fileType": "file",
                        "size": attr.st_size,
                        "modifiedDate": _format_mtime(attr.st_mtime),
                        "uid": attr.st_uid,
                        "gid": attr.st_gid,
                        "mode": _format_mode(attr.st_mode),
                    }
                )
        except IOError:
            pass

        if not items:
            try:
                entries = sftp.listdir_attr(path)
            except IOError as e:
                raise FileNotFoundError(f"Remote path not found: {path}") from e

            for attr in entries:
                if attr.filename in (".", ".."):
                    continue
                if not hidden and attr.filename.startswith("."):
                    continue
                items.append(
                    {
                        "fileName": attr.filename,
                        "path": f"{path.rstrip('/')}/{attr.filename}",
                        "fileType": _file_type_from_mode(attr.st_mode),
                        "size": attr.st_size if stat.S_ISREG(attr.st_mode) else 0,
                        "modifiedDate": _format_mtime(attr.st_mtime),
                        "uid": attr.st_uid,
                        "gid": attr.st_gid,
                        "mode": _format_mode(attr.st_mode),
                    }
                )

        start = (page - 1) * page_size
        end = start + page_size
        return {
            "data": items[start:end],
            "total": len(items),
            "page": page,
            "pageSize": page_size,
        }

    def mkdir(self, path: str, force: bool = True) -> Dict[str, Any]:
        """Create a remote directory."""
        sftp = self._get_manager().sftp
        try:
            sftp.stat(path)
            if not force:
                return {"result": False, "message": f"Directory already exists: {path}"}
            return {"result": True, "message": "Directory already exists"}
        except IOError:
            pass

        try:
            _mkdir_recursive(sftp, path)
            return {"result": True, "message": "Directory created"}
        except IOError as e:
            raise SFTPError(f"Failed to create directory '{path}': {e}")

    def move(self, src_path: str, dest_dir: str) -> Dict[str, Any]:
        """Move/rename a remote file or directory."""
        sftp = self._get_manager().sftp

        # Verify source exists
        try:
            sftp.stat(src_path)
        except IOError:
            raise FileNotFoundError(f"Source not found: {src_path}")

        try:
            # Determine final destination: if dest exists and is a directory,
            # append the source name; otherwise treat dest as the target path.
            try:
                dest_stat = sftp.stat(dest_dir)
                if stat.S_ISDIR(dest_stat.st_mode):
                    dest_full = f"{dest_dir.rstrip('/')}/{Path(src_path).name}"
                else:
                    dest_full = dest_dir
            except IOError:
                dest_full = dest_dir

            try:
                sftp.rename(src_path, dest_full)
            except IOError:
                # rename may fail cross-directory: fallback to copy + delete
                _copy_recursive(sftp, src_path, dest_full)
                _remove_recursive(sftp, src_path)
            return {"result": True, "message": "Moved"}
        except (FileNotFoundError, SFTPError):
            raise
        except IOError as e:
            raise SFTPError(f"Failed to move '{src_path}' to '{dest_dir}': {e}")

    def copy(self, src_path: str, dest_dir: str) -> Dict[str, Any]:
        """Copy a remote file or directory via SFTP."""
        sftp = self._get_manager().sftp

        try:
            dest_stat = sftp.stat(dest_dir)
            if stat.S_ISDIR(dest_stat.st_mode):
                dest_full = f"{dest_dir.rstrip('/')}/{Path(src_path).name}"
            else:
                dest_full = dest_dir
        except IOError:
            dest_full = dest_dir

        try:
            _copy_recursive(sftp, src_path, dest_full)
        except (FileNotFoundError, SFTPError):
            raise
        except IOError as e:
            raise SFTPError(f"Failed to copy '{src_path}' to '{dest_full}': {e}")
        return {"result": True, "message": "Copied"}

    def delete(self, path: str) -> Dict[str, Any]:
        """Delete a remote file or directory."""
        sftp = self._get_manager().sftp
        try:
            _remove_recursive(sftp, path)
        except IOError as e:
            raise SFTPError(f"Failed to delete '{path}': {e}")
        return {"result": True, "message": "Deleted"}

    def list_all(self, path: str = "/", hidden: bool = False) -> List[Dict[str, Any]]:
        """List all files in a directory via SFTP (no pagination)."""
        sftp = self._get_manager().sftp
        items = []

        try:
            attr = sftp.stat(path)
            if stat.S_ISREG(attr.st_mode):
                name = Path(path).name
                items.append(
                    {
                        "fileName": name,
                        "path": path,
                        "fileType": "file",
                        "size": attr.st_size,
                        "modifiedDate": _format_mtime(attr.st_mtime),
                        "uid": attr.st_uid,
                        "gid": attr.st_gid,
                        "mode": _format_mode(attr.st_mode),
                    }
                )
                return items
        except IOError:
            pass

        try:
            entries = sftp.listdir_attr(path)
        except IOError as e:
            raise FileNotFoundError(f"Remote path not found: {path}") from e

        for attr in entries:
            if attr.filename in (".", ".."):
                continue
            if not hidden and attr.filename.startswith("."):
                continue
            items.append(
                {
                    "fileName": attr.filename,
                    "path": f"{path.rstrip('/')}/{attr.filename}",
                    "fileType": _file_type_from_mode(attr.st_mode),
                    "size": attr.st_size if stat.S_ISREG(attr.st_mode) else 0,
                    "modifiedDate": _format_mtime(attr.st_mtime),
                    "uid": attr.st_uid,
                    "gid": attr.st_gid,
                    "mode": _format_mode(attr.st_mode),
                }
            )
        return items

    def cat(
        self,
        remote_path: str,
        head: Optional[int] = None,
        tail: Optional[int] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        encoding: str = "utf-8",
        small_threshold: int = 1048576,
        all_lines: bool = False,
    ) -> List[str]:
        """Read selected lines from a remote text file via SFTP.

        Args:
            remote_path: Remote file full path
            head: Number of lines from the beginning
            tail: Number of lines from the end
            start: Start line number (1-based, inclusive)
            end: End line number (1-based, inclusive)
            encoding: Text encoding (default: utf-8)
            small_threshold: Byte threshold below which the file is read entirely
            all_lines: Force output all lines even for large files

        Returns:
            List of lines (with newlines stripped)
        """
        sftp = self._get_manager().sftp

        try:
            attr = sftp.stat(remote_path)
        except IOError:
            raise FileNotFoundError(f"Remote path not found: {remote_path}")

        if stat.S_ISDIR(attr.st_mode):
            raise IsADirectoryError(f"Is a directory, not a file: {remote_path}")

        file_size = attr.st_size

        # --all or small file: read all into memory
        # If all_lines is set but head/tail/start/end are also specified,
        # skip the all_lines path to avoid reading the entire file unnecessarily.
        has_slice = (
            head is not None or tail is not None or start is not None or end is not None
        )
        read_all = (all_lines and not has_slice) or file_size < small_threshold
        if read_all:
            buf = io.BytesIO()
            try:
                sftp.getfo(remote_path, buf)
            except IOError as e:
                raise SFTPError(f"Failed to read remote file '{remote_path}': {e}")
            text = buf.getvalue().decode(encoding, errors="replace")
            lines = text.splitlines()

            if head is not None:
                return lines[:head]
            if tail is not None:
                return lines[-tail:] if tail else []
            if start is not None and end is not None:
                return lines[start - 1 : end]
            if start is not None:
                return lines[start - 1 :]
            return lines

        # Large file: seek-based partial read
        if head is not None:
            return _read_head(sftp, remote_path, head, encoding)
        if tail is not None:
            return _read_tail(sftp, remote_path, tail, encoding, file_size)
        if start is not None:
            if end is not None:
                return _read_range(sftp, remote_path, start, end, encoding)
            return _read_from(sftp, remote_path, start, encoding)
        # No selector on large file: default to last 20 lines
        return _read_tail(sftp, remote_path, 20, encoding, file_size)

    def tailf(self, remote_path: str, encoding: str = "utf-8"):
        """Run ``tail -f`` on one or more remote files via SSH exec channel.

        Supports glob patterns (e.g. ``*.k``, ``*.log``) — the shell
        expands them before tail -f reads them.

        Returns the channel + tail PID so the caller can clean up.

        Blocks and prints output in real-time until interrupted with Ctrl+C.
        Requires an SFTP connection with password or key auth (Transport available).

        Args:
            remote_path: Remote file path or glob pattern to tail
            encoding: Text encoding (default: utf-8)

        Returns:
            Tuple of (tail_pid, channel) for caller to clean up.
            tail_pid may be None if command failed.
        """

        _validate_path(remote_path)

        manager = self._get_manager()
        _ = manager.sftp
        transport = manager._transport
        if transport is None:
            raise SFTPError("SFTP transport not connected")

        channel = transport.open_session()
        # Use blocking mode with a timeout instead of setblocking(False) + sleep
        # polling, which adds up to 100ms latency per data chunk.
        channel.setblocking(True)
        channel.settimeout(1.0)
        # Start tail in background, get PID on stdout.
        # Do NOT quote remote_path so shell glob patterns are expanded.
        cmd = f"tail -f {remote_path} 2>&1 & echo $!"
        channel.exec_command(cmd)

        tail_pid = None
        first_chunk = True
        # Stream output; extract PID from first line
        try:
            while not channel.closed:
                try:
                    data = channel.recv(65536)
                except (TimeoutError, OSError):
                    # socket.timeout / channel timeout — loop back to check .closed
                    continue
                if not data:
                    break
                text = data.decode(encoding, errors="replace")

                if first_chunk:
                    first_chunk = False
                    # First line is the PID, rest is tail output
                    parts = text.split("\n", 1)
                    tail_pid = parts[0].strip()
                    if len(parts) > 1:
                        sys.stdout.write(parts[1])
                        sys.stdout.flush()
                else:
                    sys.stdout.write(text)
                    sys.stdout.flush()
        except KeyboardInterrupt:
            pass

        return tail_pid, channel

    def kill_tail(self, tail_pid: str):
        """Kill a tail process started by tailf().

        Args:
            tail_pid: PID returned by tailf()
        """

        # Validate PID is numeric to prevent command injection
        if not tail_pid or not str(tail_pid).isdigit():
            raise SFTPError(f"Invalid tail PID: {tail_pid!r} (must be numeric)")

        manager = self._get_manager()
        _ = manager.sftp
        transport = manager._transport
        if transport is None:
            raise SFTPError("SFTP transport not connected")

        kill_ch = transport.open_session()
        kill_ch.setblocking(True)
        kill_ch.settimeout(2.0)
        kill_ch.exec_command(f"kill {tail_pid} 2>/dev/null")
        try:
            kill_ch.recv_exit_status()
        except Exception:
            pass
        finally:
            kill_ch.close()

    def close(self):
        if self._manager:
            self._manager.close()
            self._manager = None


def _download_dir_recursive(sftp, remote_dir, local_base, on_progress, chunk_size):
    """Recursively download a remote directory via SFTP."""
    try:
        entries = sftp.listdir_attr(remote_dir)
    except IOError as e:
        raise SFTPError(f"Failed to list remote directory '{remote_dir}': {e}")

    results = []
    file_items = []
    dir_items = []

    for attr in entries:
        name = attr.filename
        if name in (".", ".."):
            continue
        if stat.S_ISDIR(attr.st_mode):
            dir_items.append(name)
        else:
            file_items.append(attr)

    total = len(file_items)
    for idx, attr in enumerate(file_items, 1):
        fname = attr.filename
        remote_path = f"{remote_dir}/{fname}"
        local_file = local_base / fname

        try:
            local_file.parent.mkdir(parents=True, exist_ok=True)
            if on_progress:

                def callback(transferred, total_b):
                    on_progress(fname, transferred, total_b)

                sftp.get(remote_path, str(local_file), callback=callback)
            else:
                sftp.get(remote_path, str(local_file))

            results.append(
                {
                    "file": fname,
                    "status": "ok",
                    "size": local_file.stat().st_size,
                }
            )
        except Exception as e:
            results.append({"file": fname, "status": "error", "error": str(e)})

        if on_progress:
            on_progress(fname, idx, total)

    for dirname in dir_items:
        sub_results = _download_dir_recursive(
            sftp,
            f"{remote_dir}/{dirname}",
            local_base / dirname,
            on_progress,
            chunk_size,
        )
        results.extend(sub_results)

    return results


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _format_mtime(ts) -> str:
    """Format timestamp as ISO-like date string."""
    import datetime

    try:
        dt = datetime.datetime.fromtimestamp(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (OSError, ValueError):
        return str(int(ts))


# Map group name → (special-bit, char-with-execute, char-without-execute)
_MODE_SPECIAL_BITS = {
    "USR": (stat.S_ISUID, "s", "S"),
    "GRP": (stat.S_ISGID, "s", "S"),
    "OTH": (stat.S_ISVTX, "t", "T"),
}


def _format_mode(mode) -> str:
    """Format a Unix file mode to 'l/ d/-rwxr-xr-x' string."""
    if stat.S_ISLNK(mode):
        type_char = "l"
    elif stat.S_ISDIR(mode):
        type_char = "d"
    elif stat.S_ISREG(mode):
        type_char = "-"
    elif stat.S_ISFIFO(mode):
        type_char = "p"
    elif stat.S_ISCHR(mode):
        type_char = "c"
    elif stat.S_ISBLK(mode):
        type_char = "b"
    else:
        type_char = "?"

    perms = ""
    for who in ("USR", "GRP", "OTH"):
        r = mode & getattr(stat, f"S_IR{who}")
        w = mode & getattr(stat, f"S_IW{who}")
        x = mode & getattr(stat, f"S_IX{who}")
        perms += "r" if r else "-"
        perms += "w" if w else "-"
        bit, low, up = _MODE_SPECIAL_BITS[who]
        if mode & bit:
            perms += low if x else up
        else:
            perms += "x" if x else "-"

    return f"{type_char} {perms}"


def _file_type_from_mode(mode) -> str:
    """Return a file type string from a Unix mode."""
    if stat.S_ISLNK(mode):
        return "symlink"
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISREG(mode):
        return "file"
    return "unknown"


def _copy_recursive(sftp, src: str, dest: str):
    """Copy a file or directory recursively via SFTP."""
    try:
        attr = sftp.stat(src)
    except IOError:
        raise FileNotFoundError(f"Source not found: {src}")

    if stat.S_ISDIR(attr.st_mode):
        try:
            sftp.mkdir(dest)
        except IOError:
            pass
        try:
            entries = sftp.listdir_attr(src)
        except IOError as e:
            raise SFTPError(f"Failed to list directory '{src}': {e}")
        for entry in entries:
            if entry.filename in (".", ".."):
                continue
            _copy_recursive(
                sftp,
                f"{src}/{entry.filename}",
                f"{dest}/{entry.filename}",
            )
    else:
        # Ensure parent directory of destination exists
        dest_parent = str(Path(dest).parent)
        if dest_parent:
            _mkdir_recursive(sftp, dest_parent)

        _copy_chunk_size = 65536
        try:
            with sftp.open(src, "rb") as src_f:
                with sftp.open(dest, "wb") as dest_f:
                    while True:
                        chunk = src_f.read(_copy_chunk_size)
                        if not chunk:
                            break
                        dest_f.write(chunk)
                sftp.chmod(dest, attr.st_mode)
        except IOError as e:
            raise SFTPError(f"Failed to copy '{src}' to '{dest}': {e}")


def _remove_recursive(sftp, path: str):
    """Remove a file or directory recursively via SFTP."""
    try:
        attr = sftp.stat(path)
    except IOError:
        return

    if stat.S_ISDIR(attr.st_mode):
        try:
            entries = sftp.listdir_attr(path)
        except IOError as e:
            raise SFTPError(f"Failed to list directory for removal '{path}': {e}")
        for entry in entries:
            if entry.filename in (".", ".."):
                continue
            _remove_recursive(sftp, f"{path}/{entry.filename}")
        try:
            sftp.rmdir(path)
        except IOError as e:
            raise SFTPError(f"Failed to remove directory '{path}': {e}")
    else:
        try:
            sftp.remove(path)
        except IOError as e:
            raise SFTPError(f"Failed to remove file '{path}': {e}")


# ---------------------------------------------------------------------------
# Partial read helpers for cat()
# ---------------------------------------------------------------------------


def _read_chunked_lines(sftp, remote_path: str, encoding: str, chunk_size: int = 65536):
    """Yield (line_number, line_text) from a remote file using chunked reads.

    Line numbers are 1-based. Handles partial lines across chunk boundaries.
    """
    offset = 0
    line_num = 1
    remainder = b""

    while True:
        buf = io.BytesIO()
        try:
            sftp.getfo(remote_path, buf, offset, chunk_size)
        except IOError as e:
            raise SFTPError(
                f"Failed to read remote file '{remote_path}' at offset {offset}: {e}"
            )
        chunk = buf.getvalue()
        if not chunk:
            if remainder:
                yield line_num, remainder.decode(encoding, errors="replace").rstrip(
                    "\r"
                )
            break

        data = remainder + chunk
        parts = data.split(b"\n")
        remainder = parts[-1]
        for raw_line in parts[:-1]:
            yield line_num, raw_line.decode(encoding, errors="replace").rstrip("\r")
            line_num += 1

        offset += len(chunk)


def _read_head(sftp, remote_path: str, n: int, encoding: str) -> List[str]:
    """Read first n lines from a remote file using chunked reads."""
    lines = []
    for _, text in _read_chunked_lines(sftp, remote_path, encoding):
        lines.append(text)
        if len(lines) >= n:
            break
    return lines


def _read_tail(
    sftp, remote_path: str, n: int, encoding: str, file_size: int
) -> List[str]:
    """Read last n lines from a remote file by seeking near the end."""
    chunk_size = 8192
    collected = []
    pos = file_size

    while pos > 0 and len(collected) < n + 1:
        read_start = max(0, pos - chunk_size)
        amount = pos - read_start
        buf = io.BytesIO()
        try:
            sftp.getfo(remote_path, buf, read_start, amount)
        except IOError as e:
            raise SFTPError(
                f"Failed to read remote file '{remote_path}' at offset {read_start}: {e}"
            )
        chunk = buf.getvalue()
        lines = chunk.decode(encoding, errors="replace").splitlines()
        if read_start > 0:
            # Check whether the byte immediately before this chunk is a newline.
            # If so, the first line is complete (starts at a boundary);
            # otherwise it is a continuation of the previous line and must be discarded.
            prev_buf = io.BytesIO()
            try:
                sftp.getfo(remote_path, prev_buf, read_start - 1, 1)
            except IOError:
                # If we can't peek, assume partial to be safe.
                lines.pop(0)
            else:
                prev_byte = prev_buf.getvalue()
                if prev_byte not in (b"\n", b"\r"):
                    lines.pop(0)
        collected = lines + collected
        pos = read_start

    if pos > 0 and len(collected) > n:
        collected.pop(0)

    return collected[-n:] if len(collected) > n else collected


def _read_range(
    sftp, remote_path: str, start: int, end: int, encoding: str
) -> List[str]:
    """Read lines start..end (1-based inclusive) using chunked reads."""
    lines = []
    for line_num, text in _read_chunked_lines(sftp, remote_path, encoding):
        if line_num > end:
            break
        if line_num >= start:
            lines.append(text)
    return lines


def _read_from(sftp, remote_path: str, start: int, encoding: str) -> List[str]:
    """Read from line start to EOF (1-based) using chunked reads."""
    lines = []
    for line_num, text in _read_chunked_lines(sftp, remote_path, encoding):
        if line_num >= start:
            lines.append(text)
    return lines
