"""
Data models for Appform SDK
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ApiResponse:
    """Base API response model."""

    code: int
    result: str
    message: Optional[str] = None
    data: Optional[Any] = None

    @property
    def success(self) -> bool:
        """Check if the response indicates success."""
        return self.result == "success"


@dataclass
class Job:
    """Job model."""

    id: str
    job_id: str
    name: str
    status: str
    owner: str
    app_name: str
    queue: str
    slots: str
    submit_time: Optional[str] = None
    execution_time: Optional[str] = None
    termination_time: Optional[str] = None
    execution_host: Optional[List[str]] = None
    cwd: Optional[str] = None
    sub_cwd: Optional[str] = None
    project: Optional[str] = None
    index_id: Optional[str] = None
    array_job: Optional[str] = None
    desktop_id: Optional[str] = None
    reasons: Optional[List[str]] = None
    user_name_cn: Optional[str] = None
    organization_tree: Optional[str] = None
    gpu_num: int = 0
    is_docker: bool = False
    exclusive: bool = False
    job_type: bool = True
    job_desktop_expires: bool = False
    job_data_not_exists: bool = False
    has_alarm_host: bool = False
    has_job_exception: bool = False
    alarm_info: Optional[str] = None
    exception_info: Optional[str] = None
    graphic_script_name: Optional[str] = None
    cpu_binds: Optional[List[str]] = None
    gpu_binds: Optional[List[str]] = None
    confidential: Optional[str] = None
    confidential_map: int = -1
    delete_time: Optional[str] = None
    queue_number: int = 0
    host: Optional[str] = None
    run_time: Optional[str] = None
    job_index_ids: Optional[List[str]] = None
    job_is_deleted: bool = False
    under_run_threshold: int = 0
    over_run_threshold: int = 0
    idle_threshold: int = 0
    transfer_progress_in: Optional[str] = None
    transfer_progress_out: Optional[str] = None
    is_local_spooler_job: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Job":
        """Create Job from dictionary."""
        return cls(
            id=data.get("id", ""),
            job_id=data.get("jobId", ""),
            name=data.get("name", ""),
            status=data.get("status", ""),
            owner=data.get("owner", ""),
            app_name=data.get("appName", ""),
            queue=data.get("queue", ""),
            slots=data.get("slots", ""),
            submit_time=data.get("submitTime"),
            execution_time=data.get("executionTime"),
            termination_time=data.get("terminationTime"),
            execution_host=data.get("executionHost"),
            cwd=data.get("cwd"),
            sub_cwd=data.get("subCwd"),
            project=data.get("project"),
            index_id=data.get("indexid"),
            array_job=data.get("arrayJob"),
            desktop_id=data.get("desktopid"),
            reasons=data.get("reasons", []),
            user_name_cn=data.get("userNameCn"),
            organization_tree=data.get("organizationTree"),
            gpu_num=data.get("gpuNum", 0),
            is_docker=data.get("isDocker", False),
            exclusive=data.get("exclusive", False),
            job_type=data.get("jobType", True),
            job_desktop_expires=data.get("jobDesktopExpires", False),
            job_data_not_exists=data.get("jobDataNotExists", False),
            has_alarm_host=data.get("hasAlarmHost", False),
            has_job_exception=data.get("hasJobException", False),
            alarm_info=data.get("alarmInfo"),
            exception_info=data.get("exceptionInfo"),
            graphic_script_name=data.get("graphicScriptName"),
            cpu_binds=data.get("cpuBinds", []),
            gpu_binds=data.get("gpuBinds", []),
            confidential=data.get("confidential"),
            confidential_map=data.get("confidential_map", -1),
            delete_time=data.get("deleteTime"),
            queue_number=data.get("queueNumber", 0),
            host=data.get("host"),
            run_time=data.get("runTime"),
            job_index_ids=data.get("jobIndexIds"),
            job_is_deleted=data.get("jobIsDeleted", False),
            under_run_threshold=data.get("underRunThreshold", 0),
            over_run_threshold=data.get("overRunThreshold", 0),
            idle_threshold=data.get("idleThreshold", 0),
            transfer_progress_in=data.get("transferProgressIn"),
            transfer_progress_out=data.get("transferProgressOut"),
            is_local_spooler_job=data.get("isLocalSpoolerJob", False),
        )

    @property
    def is_running(self) -> bool:
        """Check if job is running."""
        return self.status == "RUN"

    @property
    def is_pending(self) -> bool:
        """Check if job is pending."""
        return self.status == "PEND"

    @property
    def is_done(self) -> bool:
        """Check if job is done."""
        return self.status == "DONE"

    @property
    def is_error(self) -> bool:
        """Check if job has error."""
        return self.status in ("EXIT", "ERROR")


@dataclass
class Session:
    """Session model."""

    session_id: str
    session_name: Optional[str] = None
    app_name: Optional[str] = None
    app_id: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None
    create_time: Optional[str] = None
    cores: Optional[int] = None
    memory: Optional[int] = None
    queue: Optional[str] = None
    walltime: Optional[str] = None
    shared_users: Optional[List[str]] = None
    current_operator: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Create Session from dictionary."""
        return cls(
            session_id=data.get("sessionId", data.get("id", "")),
            session_name=data.get("sessionName", data.get("name")),
            app_name=data.get("appName"),
            app_id=data.get("appId"),
            owner=data.get("owner"),
            status=data.get("status"),
            create_time=data.get("createTime"),
            cores=data.get("cores"),
            memory=data.get("memory"),
            queue=data.get("queue"),
            walltime=data.get("walltime"),
            shared_users=data.get("sharedUsers", []),
            current_operator=data.get("currentOperator"),
        )


@dataclass
class FileInfo:
    """File information model."""

    name: str
    path: str
    is_directory: bool = False
    size: Optional[int] = None
    modify_time: Optional[str] = None
    permission: Optional[str] = None
    owner: Optional[str] = None
    confidential_level: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileInfo":
        """Create FileInfo from dictionary."""
        return cls(
            name=data.get("name", ""),
            path=data.get("path", ""),
            is_directory=data.get("isDirectory", data.get("isDir", False)),
            size=data.get("size"),
            modify_time=data.get("modifyTime", data.get("mtime")),
            permission=data.get("permission"),
            owner=data.get("owner"),
            confidential_level=data.get("confidentialLevel"),
        )


@dataclass
class Department:
    """Department model."""

    dep_name: str
    dep_chname: Optional[str] = None
    parent_dep: Optional[str] = None
    description: Optional[str] = None
    children: Optional[List["Department"]] = None
    users: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Department":
        """Create Department from dictionary."""
        children = None
        if "children" in data:
            children = [Department.from_dict(c) for c in data["children"]]

        return cls(
            dep_name=data.get("depName", data.get("name", "")),
            dep_chname=data.get("depChname", data.get("chname")),
            parent_dep=data.get("parentDep", data.get("parent")),
            description=data.get("description"),
            children=children,
            users=data.get("users", []),
        )


@dataclass
class User:
    """User model."""

    username: str
    chusername: Optional[str] = None
    dep: Optional[str] = None
    phone: Optional[str] = None
    mail: Optional[str] = None
    card: Optional[str] = None
    status: Optional[str] = None
    create_time: Optional[str] = None
    last_login_time: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create User from dictionary."""
        return cls(
            username=data.get("username", ""),
            chusername=data.get("chusername", data.get("chName")),
            dep=data.get("dep", data.get("department")),
            phone=data.get("phone"),
            mail=data.get("mail", data.get("email")),
            card=data.get("card"),
            status=data.get("status"),
            create_time=data.get("createTime"),
            last_login_time=data.get("lastLoginTime"),
        )


@dataclass
class Application:
    """Application model."""

    app_id: str
    app_name: str
    app_chname: Optional[str] = None
    app_type: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    url: Optional[str] = None
    version: Optional[str] = None
    categories: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Application":
        """Create Application from dictionary."""
        return cls(
            app_id=data.get("appId", data.get("id", "")),
            app_name=data.get("appName", data.get("name", "")),
            app_chname=data.get("appChname", data.get("chname")),
            app_type=data.get("appType", data.get("type")),
            description=data.get("description"),
            icon=data.get("icon"),
            url=data.get("url"),
            version=data.get("version"),
            categories=data.get("categories", []),
        )


@dataclass
class JobSubmitResult:
    """Job submission result model."""

    job_id: str
    job_name: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobSubmitResult":
        """Create JobSubmitResult from dictionary."""
        return cls(
            job_id=data.get("jobId", ""),
            job_name=data.get("jobName"),
            status=data.get("status"),
            message=data.get("message"),
        )


@dataclass
class PaginatedResult:
    """Paginated result model."""

    content: List[Any]
    total_elements: int
    total_pages: int
    page: int
    page_size: int
    has_next: bool = False
    has_previous: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any], item_parser=None) -> "PaginatedResult":
        """Create PaginatedResult from dictionary."""
        content = data.get("content", data.get("jobs", data.get("list", [])))

        if item_parser and content:
            content = [item_parser(item) for item in content]

        total = data.get("totalElements", data.get("total", 0))
        page = data.get("page", data.get("pageNumber", 1))
        page_size = data.get("pageSize", data.get("size", 20))

        return cls(
            content=content,
            total_elements=total,
            total_pages=data.get(
                "totalPages", (total + page_size - 1) // page_size if page_size else 0
            ),
            page=page,
            page_size=page_size,
            has_next=data.get("hasNext", page * page_size < total),
            has_previous=data.get("hasPrevious", page > 1),
        )
