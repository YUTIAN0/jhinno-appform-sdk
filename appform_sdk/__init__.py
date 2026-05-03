"""
Appform SDK - Python client library for Appform 6.0-6.6 API
"""

from pathlib import Path

from .apps import AppsAPI
from .auth import AuthAPI
from .client import AppformClient
from .config import Config
from .exceptions import (
    APIError,
    AppformError,
    AuthenticationError,
    ComputeError,
    FileError,
    JobError,
    SessionError,
    SFTPError,
    ValidationError,
)
from .extensions import (
    SUPPORTED_VERSIONS,
    VERSION_6_0,
    VERSION_6_3,
    VERSION_6_5,
    VERSION_6_6,
    DynamicAPI,
    Extension,
    ExtensionConfig,
    ExtensionManager,
    init_default_registry,
)
from .files import FilesAPI
from .job_profiles import AppProfile, JobProfileManager, ParameterDef
from .jobs import JobsAPI
from .models import (
    ApiResponse,
    Application,
    Department,
    FileInfo,
    Job,
    JobSubmitResult,
    PaginatedResult,
    Session,
    User,
)
from .organization import OrganizationAPI
from .registry import APIRegistry, EndpointDefinition, get_registry
from .sessions import SessionsAPI
from .sftp import SFTPAPI, SFTPClientManager
from .utils import AESEncryptor, SignatureGenerator, check_cluster_environment

# Lazy-import xml2table to avoid pulling in pandas/openpyxl at package load time
# Use: from appform_sdk.xml2table import export, create_sdk_yaml, ...
# Or:  python -m appform_sdk.xml2table

__version__ = Path(__file__).resolve().parent.joinpath("VERSION").read_text().strip()
__all__ = [
    # Client
    "AppformClient",
    # Configuration
    "Config",
    # API modules
    "AuthAPI",
    "JobsAPI",
    "SessionsAPI",
    "AppsAPI",
    "FilesAPI",
    "OrganizationAPI",
    "SFTPAPI",
    # Utilities
    "AESEncryptor",
    "SignatureGenerator",
    # Job Profiles
    "JobProfileManager",
    "AppProfile",
    "ParameterDef",
    # Models
    "ApiResponse",
    "Job",
    "Session",
    "FileInfo",
    "Department",
    "User",
    "Application",
    "JobSubmitResult",
    "PaginatedResult",
    # Exceptions
    "AppformError",
    "AuthenticationError",
    "APIError",
    "ValidationError",
    "FileError",
    "JobError",
    "SessionError",
    "SFTPError",
    "ComputeError",
    # Registry and Extensions
    "APIRegistry",
    "get_registry",
    "EndpointDefinition",
    "Extension",
    "ExtensionConfig",
    "ExtensionManager",
    "DynamicAPI",
    "init_default_registry",
    # Version constants
    "VERSION_6_0",
    "VERSION_6_3",
    "VERSION_6_5",
    "VERSION_6_6",
    "SUPPORTED_VERSIONS",
    # XML Parser (lazy import, no top-level import to avoid optional deps)
]
