"""
Files API module for Appform SDK
"""

import os
import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


def parse_size(size_str) -> int:
    """Parse human-readable size string to bytes.

    Supported formats:
        "256K", "256KB", "256k", "256kb"
        "30M", "30MB", "30m", "30mb"
        "1G", "1GB", "1g", "1gb"
        "1048576" (raw bytes)

    Returns:
        Size in bytes
    """
    if isinstance(size_str, int):
        return size_str
    if isinstance(size_str, float):
        return int(size_str)
    size_str = str(size_str).strip()
    match = re.match(
        r"^(\d+(?:\.\d+)?)\s*(B|KB|MB|GB|TB|K|M|G|T)?$", size_str, re.IGNORECASE
    )
    if not match:
        try:
            return int(size_str)
        except ValueError:
            raise ValueError(
                f"Invalid size format: '{size_str}'. Use e.g. '256K', '30M', '1G'"
            )
    num = float(match.group(1))
    unit = (match.group(2) or "B").upper()
    multipliers = {
        "B": 1,
        "K": 1024,
        "KB": 1024,
        "M": 1024**2,
        "MB": 1024**2,
        "G": 1024**3,
        "GB": 1024**3,
        "T": 1024**4,
        "TB": 1024**4,
    }
    return int(num * multipliers[unit])


def _is_remote_path(path: str) -> bool:
    """Check if a path is a remote (server) path."""
    return path.startswith("/")


def _resolve_remote_path(path: str, default_remote: str = "/") -> str:
    """Resolve a path to a full remote path."""
    if _is_remote_path(path):
        return path
    return f"{default_remote.rstrip('/')}/{path}"


class _ProgressTracker:
    """Simple progress bar for CLI output."""

    def __init__(self, label: str = "", total: int = 0):
        self.label = label
        self.total = total
        self.current = 0
        self._last_len = 0

    def update(self, *args):
        if len(args) == 3:
            _, current, total = args
        elif len(args) == 2:
            current, total = args
        else:
            current, total = args[0], None
        if total is not None:
            self.total = total
        self.current = current
        if self.total > 0:
            pct = int(self.current * 100 / self.total)
            bar_len = 30
            filled = int(bar_len * self.current / self.total)
            bar = "█" * filled + "░" * (bar_len - filled)
            line = f"\r  {self.label} [{bar}] {pct}% ({self.current}/{self.total})"
        else:
            line = f"\r  {self.label} {self.current} items"
        sys.stderr.write(line)
        sys.stderr.flush()
        self._last_len = len(line)

    def finish(self):
        sys.stderr.write("\n")
        sys.stderr.flush()


class _MultipartBody:
    """Streaming multipart/form-data body for upload with progress tracking.

    Manually constructs multipart body so that read() is called incrementally
    by urllib3, giving us real-time progress callbacks.

    Implements __len__ so requests sets Content-Length (required by most servers).
    urllib3 calls read(8192) in a loop; we serve from a small internal buffer
    refilled from the file in 256KB reads.
    """

    READ_UNIT = 262144  # 256KB - actual disk read size

    def __init__(
        self,
        filepath: str,
        fields: dict,
        boundary: str,
        on_progress: Optional[Callable] = None,
    ):
        self._boundary = boundary
        self._on_progress = on_progress
        self._file_size = os.path.getsize(filepath)
        self._filename = Path(filepath).name
        self._file_obj = None
        self._file_read = 0
        self._filepath = filepath

        # Pre-build small parts
        self._prefix = b""
        for key, value in fields.items():
            self._prefix += (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{key}"\r\n'
                f"\r\n"
                f"{value}\r\n"
            ).encode("utf-8")
        self._prefix += (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{self._filename}"\r\n'
            f"Content-Type: application/octet-stream\r\n"
            f"\r\n"
        ).encode("utf-8")
        self._suffix = b"\r\n" + f"--{boundary}--\r\n".encode("utf-8")
        self._total_size = len(self._prefix) + self._file_size + len(self._suffix)

        self._buf = b""
        self._phase = "prefix"  # prefix -> file -> suffix -> done
        self._prefix_pos = 0

    def __len__(self) -> int:
        return self._total_size

    def _refill(self):
        """Refill internal buffer from current phase."""
        if self._buf:
            return

        if self._phase == "prefix":
            self._buf = self._prefix
            self._prefix = b""
            self._phase = "file"
            return

        if self._phase == "file":
            if self._file_obj is None:
                self._file_obj = open(self._filepath, "rb")
            chunk = self._file_obj.read(self.READ_UNIT)
            if chunk:
                self._buf = chunk
                self._file_read += len(chunk)
                if self._on_progress and self._file_size > 0:
                    self._on_progress(self._filename, self._file_read, self._file_size)
            else:
                self._file_obj.close()
                self._file_obj = None
                self._phase = "suffix"
                self._buf = self._suffix
                self._suffix = b""
            return

        # suffix or done: nothing more

    def read(self, size: int = -1) -> bytes:
        self._refill()
        if not self._buf:
            return b""
        if size == -1 or size is None:
            data = self._buf
            self._buf = b""
        else:
            data = self._buf[:size]
            self._buf = self._buf[size:]
        return data

    def seek(self, *args):
        pass

    def tell(self):
        return 0

    def close(self):
        if self._file_obj:
            self._file_obj.close()
            self._file_obj = None


class FilesAPI:
    """
    Files API for Appform.

    Provides methods for file and directory operations.
    All parameter names match the Appform OpenAPI specification.
    """

    def __init__(self, client):
        self._client = client

    def list(
        self,
        path: str = "/",
        page: int = 1,
        page_size: int = 100,
        transfer_method: str = "http",
    ) -> Dict[str, Any]:
        """
        List files in a directory.

        Args:
            path: Directory path
            page: Page number
            page_size: Number of items per page
            transfer_method: Transfer protocol ("http" or "sftp", default "http")
        """
        if transfer_method == "sftp":
            return self._client.sftp.list(path=path, page=page, page_size=page_size)
        return self._client.get(
            "/appform/ws/api/files",
            params={"dir": path, "page": page, "pageSize": page_size},
        )

    def list_all(
        self, path: str = "/", transfer_method: str = "http"
    ) -> List[Dict[str, Any]]:
        """
        List all files in a directory (auto-pagination).

        Args:
            path: Directory path
            transfer_method: Transfer protocol ("http" or "sftp", default "http")
        """
        if transfer_method == "sftp":
            return self._client.sftp.list_all(path=path)
        page = 1
        all_items = []
        while True:
            result = self.list(path=path, page=page, page_size=100)
            data = result.get("data", [])
            if isinstance(data, list):
                if not data:
                    break
                all_items.extend(data)
                if len(data) < 100:
                    break
                page += 1
            elif isinstance(data, dict):
                items = data.get("files", data.get("records", []))
                if not items:
                    break
                all_items.extend(items)
                total = data.get("total", 0)
                if len(all_items) >= total:
                    break
                page += 1
            else:
                break
        return all_items

    def mkdir(
        self, path: str, force: bool = True, transfer_method: str = "http"
    ) -> Dict[str, Any]:
        """
        Create a directory.

        Args:
            path: Full directory path to create
            force: Force creation even if exists (default: True)
            transfer_method: Transfer protocol ("http" or "sftp", default "http")
        """
        if transfer_method == "sftp":
            return self._client.sftp.mkdir(path=path, force=force)
        return self._client.post(
            "/appform/ws/api/files/mkdir",
            json={"dirPath": path, "isForce": str(force).lower()},
        )

    def rename(self, old_path: str, new_name: str) -> Dict[str, Any]:
        """
        Rename a file or directory.

        Args:
            old_path: Current file/directory full path
            new_name: New name (not full path, just the name)

        Returns:
            Rename result
        """
        return self._client.put(
            "/appform/ws/api/files/rename",
            json={"oldFileName": old_path, "newFileName": new_name},
        )

    def copy(
        self, src_path: str, dest_dir: str, transfer_method: str = "http"
    ) -> Dict[str, Any]:
        """
        Copy a file or directory.

        Args:
            src_path: Source file/directory full path
            dest_dir: Destination directory full path, or destination file full path
            transfer_method: Transfer protocol ("http" or "sftp", default "http")
        """
        if transfer_method == "sftp":
            return self._client.sftp.copy(src_path=src_path, dest_dir=dest_dir)
        return self._client.put(
            "/appform/ws/api/files/copy",
            json={"sourceFileName": src_path, "targetDirectory": dest_dir},
        )

    def move(
        self, src_path: str, dest_dir: str, transfer_method: str = "http"
    ) -> Dict[str, Any]:
        """
        Move/rename a file or directory.

        If dest_dir is a name without /, renames in same directory.
        If dest_dir is a full path, copies to target then deletes source.

        Args:
            src_path: Source file/directory full path
            dest_dir: Destination directory or new name
            transfer_method: Transfer protocol ("http" or "sftp", default "http")

        Returns:
            Move result
        """
        if transfer_method == "sftp":
            return self._client.sftp.move(src_path=src_path, dest_dir=dest_dir)
        if "/" not in dest_dir.rstrip("/"):
            # Simple rename in same directory
            return self.rename(src_path, dest_dir)
        else:
            # Cross-directory move: copy, rename, delete source
            dest_parts = dest_dir.rstrip("/").split("/")
            dest_name = dest_parts[-1]
            dest_parent = "/".join(dest_parts[:-1]) or "/"
            src_name = src_path.rstrip("/").split("/")[-1]

            result = self.copy(src_path, dest_parent)
            if dest_name != src_name:
                self.rename(f"{dest_parent.rstrip('/')}/{src_name}", dest_name)
            self.delete(src_path)
            return result

    def delete(self, path: str, transfer_method: str = "http") -> Dict[str, Any]:
        """
        Delete a file or directory.

        Args:
            path: File/directory full path to delete
            transfer_method: Transfer protocol ("http" or "sftp", default "http")
        """
        if transfer_method == "sftp":
            return self._client.sftp.delete(path=path)
        return self._client.delete(
            "/appform/ws/api/files/delete",
            params={"fileName": path},
        )

    def upload(
        self,
        file_path: str,
        remote_path: str,
        on_progress: Optional[Callable] = None,
        chunk_size: int = 104857600,
        transfer_method: str = "http",
    ) -> Dict[str, Any]:
        """
        Upload a file with optional progress tracking.

        Args:
            file_path: Local file path
            remote_path: Remote directory path to save the file
            on_progress: Optional callback(filename, bytes_read, total_bytes)
            chunk_size: Unused, kept for API compatibility
            transfer_method: Transfer protocol ("http" or "sftp", default "http")

        Returns:
            Upload result
        """
        if transfer_method == "sftp":
            return self._client.sftp.upload(
                file_path=file_path,
                remote_path=remote_path,
                on_progress=on_progress,
                chunk_size=chunk_size,
            )
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        boundary = f"----WebKitFormBoundary{os.urandom(16).hex()}"

        if on_progress:
            body = _MultipartBody(
                str(file_path),
                {"uploadPath": remote_path, "isCover": "true"},
                boundary,
                on_progress=on_progress,
            )
            content_type = f"multipart/form-data; boundary={boundary}"
            try:
                return self._client.request(
                    "POST",
                    "/appform/ws/api/files/upload",
                    data=body,
                    headers={"Content-Type": content_type},
                )
            finally:
                body.close()
        else:
            with open(str(file_path), "rb") as f:
                return self._client.post(
                    "/appform/ws/api/files/upload",
                    data={"uploadPath": remote_path, "isCover": "true"},
                    files={"file": (file_path.name, f)},
                )

    def upload_directory(
        self,
        local_dir: str,
        remote_dir: str,
        on_progress: Optional[Callable] = None,
        check_exists: Optional[Callable] = None,
        confirm: Optional[Callable] = None,
        chunk_size: int = 104857600,
        transfer_method: str = "http",
    ) -> List[Dict[str, Any]]:
        """
        Upload an entire directory recursively.

        Args:
            local_dir: Local directory path
            remote_dir: Remote directory path
            on_progress: Optional callback(filename, current_index, total)
            check_exists: Optional callback(filename) -> bool, returns True if remote file exists
            confirm: Optional callback(filename) -> bool, returns True if user confirms overwrite
            transfer_method: Transfer protocol ("http" or "sftp", default "http")

        Returns:
            List of upload results
        """
        if transfer_method == "sftp":
            return self._client.sftp.upload_directory(
                local_dir=local_dir,
                remote_dir=remote_dir,
                on_progress=on_progress,
                check_exists=check_exists,
                confirm=confirm,
                chunk_size=chunk_size,
            )
        local_dir = Path(local_dir)
        if not local_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {local_dir}")

        files = sorted(f for f in local_dir.rglob("*") if f.is_file())
        total = len(files)
        results = []

        for idx, file_path in enumerate(files, 1):
            rel = file_path.relative_to(local_dir)
            parent = str(rel.parent)
            fname = file_path.name
            if parent == ".":
                target_dir = remote_dir
            else:
                target_dir = f"{remote_dir.rstrip('/')}/{parent.replace(os.sep, '/')}"

            if parent != ".":
                try:
                    self.mkdir(target_dir)
                except Exception:
                    pass

            # Check overwrite
            skip = False
            if check_exists and check_exists(fname):
                if confirm and not confirm(fname):
                    results.append({"file": str(rel), "status": "skipped"})
                    skip = True

            if not skip:
                result = self.upload(
                    str(file_path),
                    target_dir,
                    on_progress=on_progress,
                    chunk_size=chunk_size,
                )
                results.append(
                    {
                        "file": str(rel),
                        "remote": f"{target_dir}/{fname}",
                        "result": result,
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
        transfer_method: str = "http",
    ) -> bytes:
        """
        Download a file.

        Uses streaming to avoid loading the entire file into memory.

        Args:
            remote_path: Remote file full path
            local_path: Local file/dir path (optional, returns bytes if not provided)
            on_progress: Optional callback(filename, bytes_downloaded, total_bytes)
            chunk_size: Read chunk size in bytes (default: 30MB)
            transfer_method: Transfer protocol ("http" or "sftp", default "http")

        Returns:
            File content as bytes if local_path not provided
        """
        if transfer_method == "sftp":
            return self._client.sftp.download(
                remote_path=remote_path,
                local_path=local_path,
                on_progress=on_progress,
                chunk_size=chunk_size,
            )
        result = self._client.get(
            "/appform/ws/api/files/download",
            params={"filePath": remote_path},
        )

        # API returns JSON with download URL
        download_url = None
        if isinstance(result, dict):
            data = result.get("data", {})
            if isinstance(data, dict):
                download_url = data.get("url")

        if not download_url:
            raise FileNotFoundError(f"Failed to get download URL for: {remote_path}")

        # Streaming download
        import requests as req

        verify = self._client.verify_ssl
        response = req.get(
            download_url, verify=verify, timeout=self._client.timeout, stream=True
        )

        total_size = int(response.headers.get("content-length", 0))
        fname = Path(remote_path).name
        downloaded = 0

        if local_path:
            local = Path(local_path)
            if local.is_dir():
                local = local / fname
            local.parent.mkdir(parents=True, exist_ok=True)
            with open(str(local), "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if on_progress:
                            on_progress(fname, downloaded, total_size)
            return None
        else:
            content = bytearray()
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    content.extend(chunk)
                    downloaded += len(chunk)
                    if on_progress:
                        on_progress(fname, downloaded, total_size)
            return bytes(content)

    def download_directory(
        self,
        remote_dir: str,
        local_dir: str,
        on_progress: Optional[Callable] = None,
        chunk_size: int = 104857600,
        transfer_method: str = "http",
    ) -> List[Dict[str, Any]]:
        """
        Download an entire remote directory.

        Args:
            remote_dir: Remote directory full path
            local_dir: Local directory path to save to
            on_progress: Optional callback(filename, current_index, total)
            chunk_size: Read chunk size in bytes (default: 30MB)
            transfer_method: Transfer protocol ("http" or "sftp", default "http")

        Returns:
            List of download results
        """
        if transfer_method == "sftp":
            return self._client.sftp.download_directory(
                remote_dir=remote_dir,
                local_dir=local_dir,
                on_progress=on_progress,
                chunk_size=chunk_size,
            )
        local_base = Path(local_dir)
        local_base.mkdir(parents=True, exist_ok=True)

        all_items = self.list_all(path=remote_dir)

        file_items = [
            i
            for i in all_items
            if i.get("fileType") != "directory" and i.get("dirs") != "1"
        ]
        dir_items = [
            i
            for i in all_items
            if i.get("fileType") == "directory" or i.get("dirs") == "1"
        ]
        total = len(file_items)

        results = []
        for idx, item in enumerate(file_items, 1):
            fname = item.get("fileName", "")
            fpath = item.get("path", f"{remote_dir}/{fname}")
            rel = fpath.replace(remote_dir, "").lstrip("/")
            local_file = local_base / rel

            try:
                self.download(fpath, str(local_file), chunk_size=chunk_size)
                results.append(
                    {"file": rel, "status": "ok", "size": local_file.stat().st_size}
                )
            except Exception as e:
                results.append({"file": rel, "status": "error", "error": str(e)})

            if on_progress:
                on_progress(rel, idx, total)

        for item in dir_items:
            fname = item.get("fileName", "")
            fpath = item.get("path", f"{remote_dir}/{fname}")
            sub_results = self.download_directory(
                fpath, str(local_base / fname), on_progress=on_progress
            )
            results.extend(sub_results)

        return results

    def cat(
        self,
        remote_path: str,
        head: Optional[int] = None,
        tail: Optional[int] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        encoding: str = "utf-8",
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
            all_lines: Output all lines (including large files, default: False)

        Returns:
            List of lines (with newlines stripped)
        """
        return self._client.sftp.cat(
            remote_path=remote_path,
            head=head,
            tail=tail,
            start=start,
            end=end,
            encoding=encoding,
            all_lines=all_lines,
        )

    def compress(
        self,
        source_dir: str,
        target_path: str,
    ) -> Dict[str, Any]:
        """
        Compress a directory.

        Args:
            source_dir: Source directory path
            target_path: Target archive file full path

        Returns:
            Compression result
        """
        return self._client.post(
            "/appform/ws/api/files/compress",
            params={"sourceDirName": source_dir, "targetFilePath": target_path},
        )

    def uncompress(
        self,
        archive_path: str,
        dest_dir: str,
        password: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Uncompress an archive.

        Args:
            archive_path: Archive file full path
            dest_dir: Destination directory full path
            password: Archive password (optional)

        Returns:
            Uncompression result
        """
        params = {"zipFile": archive_path, "targetDir": dest_dir}
        if password:
            params["password"] = password
        return self._client.post(
            "/appform/ws/api/files/uncompress",
            params=params,
        )

    def get_confidentiality_levels(self) -> Dict[str, Any]:
        """Get available file confidentiality levels."""
        return self._client.get("/appform/ws/api/file/conf")

    def set_confidentiality(self, path: str, level: str) -> Dict[str, Any]:
        """Set file confidentiality level."""
        return self._client.post(
            "/appform/ws/api/file/conf",
            json={"path": path, "conf": level},
        )

    def get_root_dir(self) -> Dict[str, Any]:
        """Get root directory information."""
        return self._client.get("/appform/fm/getRootDir")
