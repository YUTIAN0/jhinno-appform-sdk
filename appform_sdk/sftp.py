"""
SFTP file transfer module for Appform SDK.

Provides SFTP-based upload/download as an alternative to HTTP API file transfer.
Requires paramiko: pip install jhinno-appform-sdk[sftp]
"""

import os
import stat
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


from .exceptions import SFTPError


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
    ):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._key_filename = key_filename
        self._key_password = key_password
        self._timeout = timeout

        self._transport = None
        self._sftp = None

    @property
    def sftp(self):
        """Lazy-init SFTP client, reusing if already connected."""
        if self._sftp is None or self._sftp.closed:
            self._connect()
        return self._sftp

    def _connect(self):
        paramiko = _require_paramiko()

        self._transport = paramiko.Transport((self._host, self._port))
        try:
            if self._key_filename:
                self._transport.connect(
                    username=self._username,
                    key_filename=self._key_filename,
                    password=self._key_password,
                )
            elif self._password:
                self._transport.connect(
                    username=self._username,
                    password=self._password,
                )
            else:
                raise SFTPError(
                    "SFTP requires either password or sftp_key_file authentication."
                )
            self._transport.set_keepalive(60)
        except paramiko.SSHException as e:
            self._transport.close()
            self._transport = None
            raise SFTPError(
                f"SFTP connection failed to {self._host}:{self._port}: {e}"
            )

        self._sftp = paramiko.SFTPClient.from_transport(self._transport)

    def close(self):
        if self._sftp and not self._sftp.closed:
            self._sftp.close()
        if self._transport:
            self._transport.close()
        self._sftp = None
        self._transport = None


def _mkdir_recursive(sftp_client, path: str):
    """Create remote directories recursively (manual, no recursive=True dependency)."""
    parts = path.strip("/").split("/")
    current = ""
    for part in parts:
        current += "/" + part
        try:
            sftp_client.stat(current)
        except IOError:
            sftp_client.mkdir(current)


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
            )
        return self._manager

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

        if on_progress:
            file_size = file_path.stat().st_size

            def callback(transferred, total):
                on_progress(fname, transferred, total)

            sftp.put(str(file_path), remote_full, callback=callback)
        else:
            sftp.put(str(file_path), remote_full)

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
                        file_size = file_path.stat().st_size

                        def cb(transferred, total_b):
                            on_progress(fname, transferred, total_b)

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
    ) -> bytes:
        sftp = self._get_manager().sftp
        fname = Path(remote_path).name

        # Get remote file size for progress
        try:
            remote_size = sftp.stat(remote_path).st_size
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

                sftp.get(remote_path, str(local), callback=callback)
            else:
                sftp.get(remote_path, str(local))

            return None
        else:
            # Return bytes for small files
            import io

            buf = io.BytesIO()
            if on_progress:
                def callback(transferred, total):
                    on_progress(fname, transferred, total)

                sftp.getfo(remote_path, buf, callback=callback)
            else:
                sftp.getfo(remote_path, buf)
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

    def close(self):
        if self._manager:
            self._manager.close()
            self._manager = None


def _download_dir_recursive(sftp, remote_dir, local_base, on_progress, chunk_size):
    """Recursively download a remote directory via SFTP."""
    try:
        entries = sftp.listdir_attr(remote_dir)
    except IOError:
        return []

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
