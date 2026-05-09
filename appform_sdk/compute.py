"""Compute node SSH/SFTP operations for jobs files custom command.

Provides ls, get, cat, tailf operations on compute node local storage.
Supports direct SSH and gateway (ssh -J style) tunnel via direct-tcpip.
"""

from __future__ import annotations

import os
import re
import shlex
import sys
import time
from pathlib import Path
from typing import Dict, List

try:
    import paramiko
except ImportError:
    paramiko = None

from .exceptions import ComputeError

DEFAULT_COMPUTE_CONFIG_PATH = os.path.expanduser("~/.appform/compute.yaml")
ENV_COMPUTE_CONFIG = "APPFORM_COMPUTE_CONFIG"
ENV_AUTO_ADD_HOST_KEY = "APPFORM_AUTO_ADD_HOST_KEY"


def _get_host_key_policy(config=None):
    """Return the host key policy based on config and env var.

    Priority: config.auto_add_host_key > APPFORM_AUTO_ADD_HOST_KEY env var > prompt.
    If auto-accept is enabled, use AutoAddPolicy.
    Otherwise, prompt the user to confirm unknown host keys.
    """
    auto_add = False
    if config is not None:
        auto_add = bool(getattr(config, "auto_add_host_key", False))
    if not auto_add:
        auto_add = bool(os.environ.get(ENV_AUTO_ADD_HOST_KEY))

    if auto_add:
        return paramiko.AutoAddPolicy()

    class _PromptPolicy(paramiko.MissingHostKeyPolicy):
        def missing_host_key(self, client, hostname, key):
            key_type = key.get_name()
            fingerprint = ":".join(f"{b:02x}" for b in key.get_fingerprint())
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
            else:
                raise paramiko.SSHException(
                    f"Host key verification failed for {hostname}"
                )

    return _PromptPolicy()


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


def load_compute_config(config_file: str = None) -> Dict:
    """Load compute.yaml configuration.

    Priority: explicit path > APPFORM_COMPUTE_CONFIG env > default path.
    """
    if not config_file:
        config_file = os.environ.get(ENV_COMPUTE_CONFIG, DEFAULT_COMPUTE_CONFIG_PATH)

    import yaml

    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve_app_config(compute_data: Dict, app_name: str) -> Dict:
    """Resolve config for a specific app, merging defaults.

    Returns dict with: mode, source_script, env_cmd, work_path_var.
    """
    default = compute_data.get("compute_config", {}).get("default", {})
    apps = compute_data.get("compute_config", {}).get("applications", {})
    app = apps.get(app_name, {})

    return {
        "mode": default.get("mode", "direct"),
        "source_script": default.get("source_script", ""),
        "env_cmd": default.get("env_cmd", "jjobs"),
        "work_path_var": app.get(
            "work_path_var", default.get("work_path_var", "work_path")
        ),
    }


# ---------------------------------------------------------------------------
# Node parsing
# ---------------------------------------------------------------------------


def get_head_node(exec_host_list: List[str]) -> str:
    """Extract head node from the executionHost array.

    The API returns executionHost as a list of node hostnames,
    one per slot. Head node = first element.

    ['ev-hpc-compute226', 'ev-hpc-compute226'] → 'ev-hpc-compute226'

    Also handles legacy string formats:
    '64*ev-hpc-compute033:64*ev-hpc-compute026' → 'ev-hpc-compute033'
    '8*ev-hpc-fat14' → 'ev-hpc-fat14'
    """
    if isinstance(exec_host_list, list) and len(exec_host_list) > 0:
        first = exec_host_list[0]
        if isinstance(first, str):
            return first.strip()
        return str(first)
    if isinstance(exec_host_list, str):
        raw = exec_host_list.strip()
        first = raw.split(":")[0]
        match = re.match(r"^\d+\*(.+)$", first)
        if match:
            return match.group(1)
        return first
    raise ComputeError("No execution host information available")


# ---------------------------------------------------------------------------
# SSH connection helpers
# ---------------------------------------------------------------------------


def connect_direct(
    node: str,
    username: str,
    password: str = None,
    key_filename: str = None,
    key_password: str = None,
    timeout: int = 30,
    config=None,
) -> paramiko.SSHClient:
    """SSH directly to a compute node."""
    if not paramiko:
        raise ComputeError(
            "paramiko is required. Install: pip install jhinno-appform-sdk[sftp]"
        )

    proxy_url = getattr(config, "sftp_proxy", None) if config else None
    sock = None
    if proxy_url:
        from .sftp import _open_proxy_socket

        sock = _open_proxy_socket(proxy_url, node, 22)

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(_get_host_key_policy(config))
    client.connect(
        hostname=node,
        port=22,
        username=username,
        password=password,
        key_filename=key_filename,
        passphrase=key_password,
        timeout=timeout,
        allow_agent=False,
        look_for_keys=False,
        sock=sock,
    )
    return client


def connect_via_gateway(
    gateway_host: str,
    gateway_port: int,
    node: str,
    username: str,
    password: str = None,
    key_filename: str = None,
    key_password: str = None,
    timeout: int = 30,
    config=None,
) -> paramiko.SSHClient:
    """SSH to compute node via login node gateway (ssh -J style).

    Uses direct-tcpip channel so no local port binding is needed
    (avoids port conflicts). The tunnel is socket-to-socket.

    1. SSH to gateway (login node)
    2. Open direct-tcpip channel: gateway → compute_node:22
    3. Create new paramiko Transport on the tunnel channel
    4. Return SSHClient with full SFTP + exec support
    """
    if not paramiko:
        raise ComputeError(
            "paramiko is required. Install: pip install jhinno-appform-sdk[sftp]"
        )

    proxy_url = getattr(config, "sftp_proxy", None) if config else None
    sock = None
    if proxy_url:
        from .sftp import _open_proxy_socket

        sock = _open_proxy_socket(proxy_url, gateway_host, gateway_port)

    # Step 1: Connect to gateway (login node)
    gateway_client = paramiko.SSHClient()
    gateway_client.load_system_host_keys()
    gateway_client.set_missing_host_key_policy(_get_host_key_policy(config))
    gateway_client.connect(
        hostname=gateway_host,
        port=gateway_port,
        username=username,
        password=password,
        key_filename=key_filename,
        passphrase=key_password,
        timeout=timeout,
        allow_agent=False,
        look_for_keys=False,
        sock=sock,
    )

    # Step 2: Open TCP tunnel from gateway to compute node
    gateway_transport = gateway_client.get_transport()
    tunnel_channel = gateway_transport.open_channel(
        "direct-tcpip",
        (node, 22),
        ("127.0.0.1", 0),
    )

    # Step 3: New SSH session on the tunnel
    # Load key if specified (Transport.connect uses pkey, not key_filename)
    pkey = None
    if key_filename:
        for klass in (
            paramiko.Ed25519Key,
            paramiko.RSAKey,
            paramiko.ECDSAKey,
            paramiko.DSSKey,
        ):
            try:
                pkey = klass.from_private_key_file(key_filename, password=key_password)
                break
            except (paramiko.SSHException, ValueError):
                continue
        if not pkey:
            raise ComputeError(f"Unable to load key file: {key_filename}")

    ssh_transport = paramiko.Transport(tunnel_channel)
    try:
        ssh_transport.connect(
            username=username,
            password=password,
            pkey=pkey,
        )
    except Exception:
        ssh_transport.close()
        gateway_client.close()
        raise

    client = paramiko.SSHClient()
    client._transport = ssh_transport  # type: ignore[literal-required]

    # Store gateway reference for cleanup
    client._gateway = gateway_client  # type: ignore[attr-defined]

    return client


def close_ssh_client(client: paramiko.SSHClient):
    """Close SSH client and its gateway (if any)."""
    try:
        client.close()
    except Exception:
        pass
    gateway = getattr(client, "_gateway", None)
    if gateway:
        try:
            gateway.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Work path query
# ---------------------------------------------------------------------------


def query_work_path(
    client: paramiko.SSHClient,
    node: str,
    job_id: str,
    source_script: str,
    env_cmd: str,
    work_path_var: str,
) -> str:
    """SSH exec: source env script && jjobs -env <job_id>, extract work_path.

    The command output contains lines like:
        old_work_path=/apps/backup/...
        work_path=/share/v-hehaowu/abaqus/...

    We match the specific work_path_var (not old_work_path).
    """
    remote_cmd = f"source {shlex.quote(source_script)} && {shlex.quote(env_cmd)} -env {shlex.quote(job_id)}"
    print(f"Querying work_path on {node}...")

    stdin, stdout, stderr = client.exec_command(remote_cmd, timeout=120)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode("utf-8", errors="replace")
    err_output = stderr.read().decode("utf-8", errors="replace")

    if exit_status != 0:
        raise ComputeError(
            f"'{env_cmd} -env {job_id}' failed on {node}:\n"
            f"stderr: {err_output}\nstdout: {output}"
        )

    # Match 'work_path=...' (exact variable name, not 'old_work_path')
    pattern = r"(^|[\s;])" + re.escape(work_path_var) + r"=(\S+)"
    for line in output.splitlines():
        line = line.strip()
        m = re.search(pattern, line)
        if m:
            return m.group(2)

    raise ComputeError(
        f"Could not find '{work_path_var}' in output of '{env_cmd} -env {job_id}' on {node}.\n"
        f"Output:\n{output}"
    )


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def resolve_path(work_path: str, user_path: str) -> str:
    """If user_path is absolute, use as-is. Otherwise prepend work_path."""
    if user_path.startswith("/"):
        return user_path
    return f"{work_path.rstrip('/')}/{user_path}"


# ---------------------------------------------------------------------------
# ls — list directory via SFTP
# ---------------------------------------------------------------------------


def compute_ls(sftp_client, remote_path: str) -> List[Dict]:
    """List directory contents via SFTP."""
    try:
        entries = sftp_client.listdir_attr(remote_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Directory not found: {remote_path}")

    items = []
    for attr in entries:
        items.append(
            {
                "fileName": attr.filename,
                "fileType": "directory" if attr.st_mode & 0o40000 else "file",
                "size": attr.st_size,
                "ts": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(attr.st_mtime)),
            }
        )
    return items


def print_ls_table(items: List[Dict], path: str):
    """Print ls output as formatted table."""
    if not items:
        print("(empty directory)")
        return
    print(f"Directory: {path}")
    print(f"{'TYPE':<6} {'SIZE':>10} {'MODIFIED':<20}  {'NAME'}")
    print("-" * 70)
    for item in sorted(
        items, key=lambda x: (x["fileType"] != "directory", x["fileName"].lower())
    ):
        type_ch = "D" if item["fileType"] == "directory" else "F"
        size_str = human_size(item["size"]) if item["fileType"] == "file" else "-"
        print(f"{type_ch:<6} {size_str:>10} {item['ts']:<20}  {item['fileName']}")
    print(f"\n{len(items)} item(s)")


# ---------------------------------------------------------------------------
# get — download via SFTP
# ---------------------------------------------------------------------------


def human_size(n: int) -> str:
    """Convert bytes to human-readable size."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def compute_get(sftp_client, remote_path: str, local_path: str):
    """Download file or directory via SFTP with progress."""
    local = Path(local_path)

    try:
        sftp_client.stat(remote_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Remote path not found: {remote_path}")

    try:
        sftp_client.listdir(remote_path)
        _download_directory(sftp_client, remote_path, local)
    except OSError:
        # It's a file
        _download_file(sftp_client, remote_path, local)


def _download_file(sftp_client, remote_path: str, local_path: Path):
    """Download a single file with progress."""
    if local_path.is_dir():
        local_path = local_path / Path(remote_path).name
    local_path.parent.mkdir(parents=True, exist_ok=True)
    label = local_path.name
    total = [0]
    start = time.time()

    def callback(_, total_bytes):
        total[0] = total_bytes

    sftp_client.get(str(remote_path), str(local_path), callback=callback)
    elapsed = max(time.time() - start, 0.001)
    speed = total[0] / elapsed / 1024 / 1024
    print(
        f"Downloaded: {label} ({human_size(total[0])} at {speed:.1f} MB/s) → {local_path}"
    )


def _download_directory(sftp_client, remote_dir: str, local_dir: Path):
    """Recursively download directory with per-file progress."""
    local_dir.mkdir(parents=True, exist_ok=True)
    entries = sftp_client.listdir_attr(remote_dir)
    downloaded = 0
    total_size = 0

    for attr in entries:
        if attr.filename in (".", ".."):
            continue
        remote_file = f"{remote_dir.rstrip('/')}/{attr.filename}"
        if attr.st_mode & 0o40000:
            _download_directory(sftp_client, remote_file, local_dir / attr.filename)
        else:
            local_file = local_dir / attr.filename
            _download_file(sftp_client, remote_file, local_file)
            downloaded += 1
            total_size += attr.st_size

    if downloaded == 1:
        print(f"Downloaded {downloaded} file ({human_size(total_size)}) to {local_dir}")
    else:
        print(
            f"Downloaded {downloaded} files ({human_size(total_size)}) to {local_dir}"
        )


# ---------------------------------------------------------------------------
# cat — view file via SSH exec
# ---------------------------------------------------------------------------


def compute_cat(
    ssh_client: paramiko.SSHClient,
    remote_path: str,
    encoding: str = "utf-8",
    head: int = None,
    tail: int = None,
) -> str:
    """View file content via SSH exec. Supports --head / --tail."""
    if head is not None:
        cmd = f"head -n {head} {shlex.quote(remote_path)}"
    elif tail is not None:
        cmd = f"tail -n {tail} {shlex.quote(remote_path)}"
    else:
        cmd = f"cat {shlex.quote(remote_path)}"

    stdin, stdout, stderr = ssh_client.exec_command(cmd, timeout=120)
    exit_status = stdout.channel.recv_exit_status()
    content = stdout.read().decode(encoding, errors="replace")
    err_text = stderr.read().decode(encoding, errors="replace")

    if exit_status != 0 and err_text:
        print(err_text, file=sys.stderr)

    return content.rstrip("\n")


# ---------------------------------------------------------------------------
# Path validation
# ---------------------------------------------------------------------------

# Characters/patterns that would allow command injection in shell commands
_DANGEROUS_PATH_CHARS = re.compile(r"""[;&|`(){}$\\><'" ]""")


def _validate_path(path: str) -> str:
    """Validate a file/directory path for use in shell commands.

    Allows glob patterns (* ? [...]) but rejects characters that could
    be used for command injection (semicolons, pipes, redirects,
    subshells, variable expansion, backslashes, quotes, spaces).

    Returns the unchanged path if safe. Raises ComputeError if dangerous.
    """
    if ".." in path:
        raise ComputeError(f"Directory traversal not allowed in path: {path!r}")
    if _DANGEROUS_PATH_CHARS.search(path):
        raise ComputeError(
            f"Invalid characters in path: {path!r}. "
            "Paths must not contain shell metacharacters or spaces "
            "(; & | ( ) `{ } $ \\ ' \" space)."
        )
    if "\n" in path:
        raise ComputeError(f"Newline not allowed in path: {path!r}")
    return path


# ---------------------------------------------------------------------------
# tailf — follow file via SSH exec
# ---------------------------------------------------------------------------


def compute_tailf(
    ssh_client: paramiko.SSHClient,
    remote_path: str,
    encoding: str = "utf-8",
):
    """Follow file output in real-time via SSH exec (tail -f).

    Uses the same pattern as SFTPAPI.tailf():
      tail -f PATH 2>&1 & echo $!

    Opens a raw session channel (not exec_command) so the channel
    stays open after the shell exits — same behaviour as the
    non-custom tailf.

    First line of output is the PID; all subsequent lines are tail output.
    Allows shell glob patterns (e.g. *.log) but rejects dangerous shell
    metacharacters to prevent command injection.
    """
    _validate_path(remote_path)

    transport = ssh_client.get_transport()
    if transport is None:
        raise ComputeError(
            "SSH transport not available. "
            "Use compute_tailf() with an SSHClient from connect_direct/connect_via_gateway."
        )

    channel = transport.open_session()
    # Use blocking mode with a timeout instead of setblocking(False) + sleep
    # polling, which adds up to 100ms latency per data chunk.
    channel.setblocking(True)
    channel.settimeout(1.0)

    # Do NOT quote remote_path — allow shell glob expansion (e.g. *.log)
    cmd = f"tail -f {remote_path} 2>&1 & echo $!"
    channel.exec_command(cmd)

    tail_pid = None
    first_chunk = True

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
    finally:
        # Kill the tail process on the remote node
        if tail_pid and tail_pid.isdigit():
            kill_ch = transport.open_session()
            kill_ch.setblocking(False)
            kill_ch.exec_command(f"kill {tail_pid} 2>/dev/null")
            try:
                for _ in range(20):
                    if kill_ch.recv_ready():
                        kill_ch.recv(65536)
                    if kill_ch.exit_status_ready():
                        break
                    time.sleep(0.05)
            finally:
                kill_ch.close()
        channel.close()


# ---------------------------------------------------------------------------
# High-level dispatcher
# ---------------------------------------------------------------------------


def execute_on_compute_node(
    app_cfg: Dict,
    head_node: str,
    job_id: str,
    subcommand: str,
    subcommand_args: List[str],
    ssh_kwargs: Dict,
    encoding: str = "utf-8",
) -> int:
    """Connect to compute node, resolve work_path, execute subcommand.

    Returns: 0 on success, non-zero on error.
    """
    mode = app_cfg["mode"]
    conn_kwargs = ssh_kwargs.get("connect_kwargs", {})
    client = None

    try:
        # 1. Connect to compute node
        print(f"Connecting to {head_node} (mode: {mode})...")
        if mode == "via_gateway":
            client = connect_via_gateway(
                gateway_host=ssh_kwargs["gateway_host"],
                gateway_port=ssh_kwargs.get("gateway_port", 22),
                node=head_node,
                **conn_kwargs,
            )
        else:
            client = connect_direct(head_node, **conn_kwargs)

        # 2. Query work_path
        work_path = query_work_path(
            client,
            head_node,
            job_id,
            app_cfg["source_script"],
            app_cfg["env_cmd"],
            app_cfg["work_path_var"],
        )
        print(f"Work path: {work_path}")

        # 3. Dispatch subcommand
        if subcommand == "ls":
            user_path = subcommand_args[0] if subcommand_args else "."
            remote_path = resolve_path(work_path, user_path)
            sftp = client.open_sftp()
            items = compute_ls(sftp, remote_path)
            print_ls_table(items, remote_path)
            sftp.close()

        elif subcommand == "get":
            if not subcommand_args:
                raise ComputeError("Usage: custom get <remote> [local]")
            remote_file = resolve_path(work_path, subcommand_args[0])
            local_dest = subcommand_args[1] if len(subcommand_args) > 1 else "."
            sftp = client.open_sftp()
            compute_get(sftp, remote_file, local_dest)
            sftp.close()

        elif subcommand == "cat":
            if not subcommand_args:
                raise ComputeError("Usage: custom cat <path>")
            remote_file = resolve_path(work_path, subcommand_args[0])
            head_n = ssh_kwargs.get("head")
            tail_n = ssh_kwargs.get("tail")
            output = compute_cat(
                client, remote_file, encoding=encoding, head=head_n, tail=tail_n
            )
            print(output)

        elif subcommand == "tailf":
            if not subcommand_args:
                raise ComputeError("Usage: custom tailf <path>")
            remote_file = resolve_path(work_path, subcommand_args[0])
            compute_tailf(client, remote_file, encoding=encoding)

        else:
            raise ComputeError(f"Unknown subcommand: {subcommand}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except (ComputeError, ImportError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    finally:
        if client:
            close_ssh_client(client)
