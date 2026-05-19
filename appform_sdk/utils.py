"""
Utility functions for Appform SDK
"""

import base64
import hashlib
import hmac
import os
import re
import subprocess
import time
from typing import Any, Dict, Optional
from urllib.parse import quote, unquote

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


# ---------------------------------------------------------------------------
# Path validation
# ---------------------------------------------------------------------------

_DANGEROUS_PATH_CHARS = re.compile(r"""[;&|`(){}$\\><'" ]""")


def validate_path(path: str, exception_class: type = ValueError) -> str:
    """Validate a file/directory path for use in shell commands.

    Allows glob patterns (* ? [...]) but rejects characters that could
    be used for command injection (semicolons, pipes, redirects,
    subshells, variable expansion, backslashes, quotes, spaces).

    Args:
        path: The path to validate
        exception_class: Exception class to raise on validation failure.
                       Defaults to ValueError.

    Returns the unchanged path if safe. Raises exception_class if dangerous.
    """
    if ".." in path:
        raise exception_class(f"Directory traversal not allowed in path: {path!r}")
    if _DANGEROUS_PATH_CHARS.search(path):
        raise exception_class(
            f"Invalid characters in path: {path!r}. "
            "Paths must not contain shell metacharacters or spaces "
            "(; & | ( ) `{ } $ \\ ' \" space)."
        )
    if "\n" in path:
        raise exception_class(f"Newline not allowed in path: {path!r}")
    return path


class SignatureGenerator:
    """
    Signature generator for AccessKey authentication.

    Generates HMAC-SHA256 signature for API requests.
    """

    @staticmethod
    def generate_signature(
        access_key: str,
        access_key_secret: str,
        username: str,
        current_time: Optional[int] = None,
    ) -> tuple:
        """
        Generate signature for AccessKey authentication.

        Args:
            access_key: Access key
            access_key_secret: Access key secret (used as HMAC key)
            username: User account name
            current_time: Current timestamp in milliseconds (defaults to now)

        Returns:
            Tuple of (signature, current_time_millis)
        """
        if current_time is None:
            current_time = int(time.time() * 1000)

        # Build signature string: #accessKey#username#currentTime#
        before_signature = f"#{access_key}#{username}#{current_time}#"

        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            access_key_secret.encode("utf-8"),
            before_signature.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return signature, current_time

    @staticmethod
    def generate_auth_headers(
        access_key: str,
        access_key_secret: str,
        username: str,
    ) -> dict:
        """
        Generate authentication headers for AccessKey authentication.

        Args:
            access_key: Access key
            access_key_secret: Access key secret
            username: User account name

        Returns:
            Dictionary containing accessKey, signature, currentTimeMillis, username headers
        """
        signature, current_time = SignatureGenerator.generate_signature(
            access_key, access_key_secret, username
        )

        return {
            "accessKey": access_key,
            "signature": signature,
            "currentTimeMillis": str(current_time),
            "username": username,
        }


class AESEncryptor:
    """
    AES encryption utility for Appform token-based authentication.

    Uses AES/ECB/PKCS7 padding.
    AES key must be provided via environment variable APPFORM_AES_KEY
    or config file field 'aes_key'. No default key.
    """

    ENV_AES_KEY = "APPFORM_AES_KEY"

    def __init__(self, key: Optional[str] = None):
        """
        Initialize the AES encryptor.

        Args:
            key: Encryption key. If None, reads from APPFORM_AES_KEY env var.

        Raises:
            ValueError: If no key is provided and APPFORM_AES_KEY is not set
        """
        if key is None:
            key = os.environ.get(self.ENV_AES_KEY)

        if not key:
            raise ValueError(
                "AES key is required. Set APPFORM_AES_KEY environment variable "
                "or configure 'aes_key' in ~/.appform/config.json"
            )

        self.key = key.encode("utf-8")
        if len(self.key) not in (16, 24, 32):
            raise ValueError(
                f"AES key must be 16, 24, or 32 bytes, got {len(self.key)}. "
                "Check APPFORM_AES_KEY or config 'aes_key'."
            )

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string using AES/ECB/PKCS7.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64 encoded and URL encoded ciphertext
        """
        cipher = AES.new(self.key, AES.MODE_ECB)
        padded_data = pad(plaintext.encode("utf-8"), AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        encoded = base64.b64encode(encrypted).decode("utf-8")
        return quote(encoded, safe="")

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a string using AES/ECB/PKCS7.

        Args:
            ciphertext: Base64 encoded ciphertext

        Returns:
            Decrypted plaintext
        """
        cipher = AES.new(self.key, AES.MODE_ECB)
        encrypted = base64.b64decode(unquote(ciphertext))
        decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
        return decrypted.decode("utf-8")

    def encrypt_username(self, username: str, timestamp: Optional[int] = None) -> str:
        """
        Encrypt username with timestamp for token-based login.

        Args:
            username: Username to encrypt
            timestamp: Optional timestamp (defaults to current time in milliseconds)

        Returns:
            Encrypted and URL-encoded string
        """
        if timestamp is None:
            timestamp = int(time.time() * 1000)
        plaintext = f"{username},{timestamp}"
        return self.encrypt(plaintext)

    def decrypt_username(self, ciphertext: str) -> str:
        """
        Decrypt and extract username from encrypted token.

        Args:
            ciphertext: Encrypted token string

        Returns:
            Username extracted from the decrypted string
        """
        decrypted = self.decrypt(ciphertext)
        return decrypted.split(",")[0]


# ---------------------------------------------------------------------------
# Cluster environment detection
# ---------------------------------------------------------------------------


def check_cluster_environment() -> Dict[str, Any]:
    """
    Check if the current node is in an HPC cluster environment.

    Checks:
    1. 'jversion' command exists and prints scheduler version
    2. 'jhosts -w' command exists and current hostname appears in host list

    Returns:
        Dict with keys:
        - in_cluster (bool): True if in cluster
        - jversion (str): Scheduler version string, or None
        - hostname (str): Current hostname, or None
        - host_status (str): Status of current host from jhosts, or None
        - error (str): Error message if detection failed, or None
    """
    result = {
        "in_cluster": False,
        "jversion": None,
        "hostname": None,
        "host_status": None,
        "error": None,
    }

    # 1. Check jversion
    try:
        proc = subprocess.run(
            ["jversion"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
        if proc.returncode != 0:
            result["error"] = "jversion command failed"
            return result
        result["jversion"] = proc.stdout.decode("utf-8", errors="replace").strip()
    except FileNotFoundError:
        result["error"] = "jversion command not found"
        return result
    except Exception as e:
        result["error"] = f"jversion error: {e}"
        return result

    # 2. Get current hostname
    try:
        import socket

        hostname = socket.gethostname()
        result["hostname"] = hostname
    except Exception as e:
        result["error"] = f"Cannot get hostname: {e}"
        return result

    # 3. Check jhosts -w for current host
    try:
        proc = subprocess.run(
            ["jhosts", "-w"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
        if proc.returncode != 0:
            result["error"] = "jhosts -w command failed"
            return result

        output = proc.stdout.decode("utf-8", errors="replace")
        # Parse jhosts output: first line is header, each subsequent line is a host
        found = False
        for line in output.strip().split("\n")[1:]:
            parts = line.split()
            if parts and parts[0] == hostname:
                found = True
                result["host_status"] = parts[1] if len(parts) > 1 else "unknown"
                result["in_cluster"] = True
                break

        if not found:
            result["error"] = f"Host '{hostname}' not found in jhosts output"

    except FileNotFoundError:
        result["error"] = "jhosts command not found"
    except Exception as e:
        result["error"] = f"jhosts error: {e}"

    return result


def build_filter_condition(
    field: str,
    operator: str,
    value: str,
    field_type: str = "string",
    ignore_case: bool = True,
) -> dict:
    """
    Build a filter condition for job queries.

    Args:
        field: Field name to filter on
        operator: Comparison operator (eq, contains, gt, lt, etc.)
        value: Value to compare against
        field_type: Data type (string, number, etc.)
        ignore_case: Whether to ignore case for string comparisons

    Returns:
        Filter condition dictionary
    """
    return {
        "type": field_type,
        "operator": operator,
        "ignoreCase": ignore_case,
        "field": field,
        "value": value,
    }


def build_filter_group(filters: list, logic: str = "and") -> dict:
    """
    Build a filter group for complex queries.

    Args:
        filters: List of filter conditions or filter groups
        logic: Logical operator (and, or)

    Returns:
        Filter group dictionary
    """
    return {
        "filters": filters,
        "logic": logic,
    }


def compare_versions(v1: str, v2: str) -> int:
    """Compare version strings. Returns -1, 0, 1."""
    parts1 = [int(x) for x in v1.split(".")]
    parts2 = [int(x) for x in v2.split(".")]
    for p1, p2 in zip(parts1, parts2):
        if p1 < p2:
            return -1
        if p1 > p2:
            return 1
    if len(parts1) < len(parts2):
        return -1
    if len(parts1) > len(parts2):
        return 1
    return 0


def human_size(n: int) -> str:
    """Convert bytes to human-readable size string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"
