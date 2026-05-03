"""
Appform SDK Exceptions
"""

from typing import Optional


class AppformError(Exception):
    """Base exception for Appform SDK."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class AuthenticationError(AppformError):
    """Raised when authentication fails."""

    pass


class APIError(AppformError):
    """Raised when API returns an error."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[dict] = None,
    ):
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class ValidationError(AppformError):
    """Raised when validation fails."""

    pass


class FileError(AppformError):
    """Raised when file operations fail."""

    pass


class JobError(AppformError):
    """Raised when job operations fail."""

    pass


class SessionError(AppformError):
    """Raised when session operations fail."""

    pass


class SFTPError(AppformError):
    """Raised when SFTP operations fail."""

    pass


class ComputeError(AppformError):
    """Raised when compute node SSH operations fail."""

    pass
