"""
Tests for appform_sdk.models — all data model classes.
"""


from appform_sdk.models import (
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

# ── ApiResponse ──────────────────────────────────────────────────────────


class TestApiResponse:
    def test_success_true(self):
        r = ApiResponse(code=200, result="success", message="OK")
        assert r.success is True

    def test_success_false(self):
        r = ApiResponse(code=500, result="error", message="fail")
        assert r.success is False

    def test_defaults(self):
        r = ApiResponse(code=200, result="success")
        assert r.message is None
        assert r.data is None


# ── Job ──────────────────────────────────────────────────────────────────


class TestJob:
    SAMPLE = {
        "id": "100",
        "jobId": "j-001",
        "name": "test_job",
        "status": "RUN",
        "owner": "alice",
        "appName": "starccm",
        "queue": "normal",
        "slots": "8",
        "submitTime": "2025-01-01 10:00:00",
        "executionTime": "2025-01-01 10:05:00",
        "terminationTime": None,
        "executionHost": ["node01", "node02"],
        "cwd": "/home/alice",
        "gpuNum": 2,
        "isDocker": True,
        "exclusive": False,
        "reasons": ["queue full"],
        "userNameCn": "Alice",
        "organizationTree": "/deptA/team1",
        "cpuBinds": ["0-7"],
        "gpuBinds": ["0,1"],
    }

    def test_from_dict_basic(self):
        job = Job.from_dict(self.SAMPLE)
        assert job.id == "100"
        assert job.job_id == "j-001"
        assert job.name == "test_job"
        assert job.status == "RUN"
        assert job.owner == "alice"
        assert job.app_name == "starccm"
        assert job.queue == "normal"
        assert job.slots == "8"

    def test_from_dict_optional_fields(self):
        job = Job.from_dict(self.SAMPLE)
        assert job.submit_time == "2025-01-01 10:00:00"
        assert job.execution_time == "2025-01-01 10:05:00"
        assert job.termination_time is None
        assert job.execution_host == ["node01", "node02"]
        assert job.cwd == "/home/alice"
        assert job.gpu_num == 2
        assert job.is_docker is True
        assert job.reasons == ["queue full"]
        assert job.cpu_binds == ["0-7"]
        assert job.gpu_binds == ["0,1"]

    def test_from_dict_defaults(self):
        job = Job.from_dict({"jobId": "j-minimal"})
        assert job.job_id == "j-minimal"
        assert job.id == ""
        assert job.status == ""
        assert job.gpu_num == 0
        assert job.is_docker is False
        assert job.execution_host is None
        assert job.reasons == []

    def test_status_properties(self):
        job = Job.from_dict({"status": "RUN"})
        assert job.is_running is True
        assert job.is_pending is False
        assert job.is_done is False
        assert job.is_error is False

    def test_status_pending(self):
        job = Job.from_dict({"status": "PEND"})
        assert job.is_pending is True
        assert job.is_running is False

    def test_status_done(self):
        job = Job.from_dict({"status": "DONE"})
        assert job.is_done is True
        assert job.is_error is False

    def test_status_error_exit(self):
        job = Job.from_dict({"status": "EXIT"})
        assert job.is_error is True
        assert job.is_done is False

    def test_status_error_error(self):
        job = Job.from_dict({"status": "ERROR"})
        assert job.is_error is True

    def test_status_unknown(self):
        job = Job.from_dict({"status": "ZOMBI"})
        assert job.is_running is False
        assert job.is_pending is False
        assert job.is_done is False
        assert job.is_error is False


# ── Session ──────────────────────────────────────────────────────────────


class TestSession:
    def test_from_dict_basic(self):
        data = {
            "sessionId": "s-001",
            "sessionName": "desktop1",
            "appName": "xfce",
            "appId": "xfce_id",
            "owner": "bob",
            "status": "RUNNING",
            "createTime": "2025-01-01",
            "cores": 4,
            "memory": 8192,
            "queue": "interactive",
            "walltime": "24:00:00",
            "sharedUsers": ["alice"],
            "currentOperator": "bob",
        }
        s = Session.from_dict(data)
        assert s.session_id == "s-001"
        assert s.session_name == "desktop1"
        assert s.owner == "bob"
        assert s.cores == 4
        assert s.shared_users == ["alice"]

    def test_from_dict_fallback_id(self):
        """sessionId falls back to 'id'."""
        s = Session.from_dict({"id": "s-002"})
        assert s.session_id == "s-002"

    def test_from_dict_fallback_name(self):
        """sessionName falls back to 'name'."""
        s = Session.from_dict({"name": "my_session"})
        assert s.session_name == "my_session"

    def test_from_dict_defaults(self):
        s = Session.from_dict({"sessionId": "s-003"})
        assert s.session_name is None
        assert s.cores is None
        assert s.shared_users == []


# ── FileInfo ─────────────────────────────────────────────────────────────


class TestFileInfo:
    def test_from_dict_basic(self):
        data = {
            "name": "test.txt",
            "path": "/home/user/test.txt",
            "isDirectory": False,
            "size": 1024,
            "modifyTime": "2025-01-01",
            "permission": "rw-r--r--",
            "owner": "user",
            "confidentialLevel": "public",
        }
        fi = FileInfo.from_dict(data)
        assert fi.name == "test.txt"
        assert fi.path == "/home/user/test.txt"
        assert fi.is_directory is False
        assert fi.size == 1024
        assert fi.owner == "user"

    def test_from_dict_fallback_isdir(self):
        """isDirectory falls back to 'isDir'."""
        fi = FileInfo.from_dict({"isDir": True})
        assert fi.is_directory is True

    def test_from_dict_fallback_mtime(self):
        """modifyTime falls back to 'mtime'."""
        fi = FileInfo.from_dict({"mtime": "2025-06-01"})
        assert fi.modify_time == "2025-06-01"

    def test_from_dict_defaults(self):
        fi = FileInfo.from_dict({})
        assert fi.name == ""
        assert fi.path == ""
        assert fi.is_directory is False
        assert fi.size is None


# ── Department ───────────────────────────────────────────────────────────


class TestDepartment:
    def test_from_dict_basic(self):
        data = {
            "depName": "engineering",
            "depChname": "工程部",
            "parentDep": "root",
            "description": "Engineering dept",
            "users": ["alice", "bob"],
        }
        d = Department.from_dict(data)
        assert d.dep_name == "engineering"
        assert d.dep_chname == "工程部"
        assert d.parent_dep == "root"
        assert d.users == ["alice", "bob"]

    def test_from_dict_fallback_name(self):
        """depName falls back to 'name'."""
        d = Department.from_dict({"name": "hr"})
        assert d.dep_name == "hr"

    def test_from_dict_fallback_chname(self):
        """depChname falls back to 'chname'."""
        d = Department.from_dict({"chname": "人力"})
        assert d.dep_chname == "人力"

    def test_from_dict_fallback_parent(self):
        """parentDep falls back to 'parent'."""
        d = Department.from_dict({"parent": "root"})
        assert d.parent_dep == "root"

    def test_from_dict_nested_children(self):
        data = {
            "depName": "root",
            "children": [
                {
                    "depName": "child1",
                    "children": [
                        {"depName": "grandchild"},
                    ],
                },
                {"depName": "child2"},
            ],
        }
        d = Department.from_dict(data)
        assert len(d.children) == 2
        assert d.children[0].dep_name == "child1"
        assert len(d.children[0].children) == 1
        assert d.children[0].children[0].dep_name == "grandchild"
        assert d.children[1].dep_name == "child2"
        assert d.children[1].children is None

    def test_from_dict_defaults(self):
        d = Department.from_dict({})
        assert d.dep_name == ""
        assert d.children is None
        assert d.users == []


# ── User ─────────────────────────────────────────────────────────────────


class TestUser:
    def test_from_dict_basic(self):
        data = {
            "username": "alice",
            "chusername": "爱丽丝",
            "dep": "engineering",
            "phone": "123456",
            "mail": "alice@example.com",
            "card": "001",
            "status": "active",
            "createTime": "2025-01-01",
            "lastLoginTime": "2025-06-01",
        }
        u = User.from_dict(data)
        assert u.username == "alice"
        assert u.chusername == "爱丽丝"
        assert u.dep == "engineering"
        assert u.mail == "alice@example.com"

    def test_from_dict_fallback_chname(self):
        """chusername falls back to 'chName'."""
        u = User.from_dict({"chName": "Bob"})
        assert u.chusername == "Bob"

    def test_from_dict_fallback_department(self):
        """dep falls back to 'department'."""
        u = User.from_dict({"department": "sales"})
        assert u.dep == "sales"

    def test_from_dict_fallback_email(self):
        """mail falls back to 'email'."""
        u = User.from_dict({"email": "a@b.com"})
        assert u.mail == "a@b.com"

    def test_from_dict_defaults(self):
        u = User.from_dict({})
        assert u.username == ""
        assert u.chusername is None
        assert u.phone is None


# ── Application ──────────────────────────────────────────────────────────


class TestApplication:
    def test_from_dict_basic(self):
        data = {
            "appId": "starccm",
            "appName": "STAR-CCM+",
            "appChname": "流体仿真",
            "appType": "gui",
            "description": "CFD solver",
            "icon": "starccm.png",
            "url": "/apps/starccm",
            "version": "2024.1",
            "categories": ["CFD", "simulation"],
        }
        a = Application.from_dict(data)
        assert a.app_id == "starccm"
        assert a.app_name == "STAR-CCM+"
        assert a.categories == ["CFD", "simulation"]

    def test_from_dict_fallback_id(self):
        """appId falls back to 'id'."""
        a = Application.from_dict({"id": "lsdyna", "name": "LS-DYNA"})
        assert a.app_id == "lsdyna"

    def test_from_dict_fallback_name(self):
        """appName falls back to 'name'."""
        a = Application.from_dict({"name": "Gaussian"})
        assert a.app_name == "Gaussian"

    def test_from_dict_fallback_chname(self):
        """appChname falls back to 'chname'."""
        a = Application.from_dict({"chname": "高斯"})
        assert a.app_chname == "高斯"

    def test_from_dict_fallback_type(self):
        """appType falls back to 'type'."""
        a = Application.from_dict({"type": "cli"})
        assert a.app_type == "cli"

    def test_from_dict_defaults(self):
        a = Application.from_dict({})
        assert a.app_id == ""
        assert a.app_name == ""
        assert a.categories == []


# ── JobSubmitResult ──────────────────────────────────────────────────────


class TestJobSubmitResult:
    def test_from_dict(self):
        data = {"jobId": "j-001", "jobName": "test", "status": "PEND", "message": "ok"}
        r = JobSubmitResult.from_dict(data)
        assert r.job_id == "j-001"
        assert r.job_name == "test"
        assert r.status == "PEND"
        assert r.message == "ok"

    def test_from_dict_defaults(self):
        r = JobSubmitResult.from_dict({})
        assert r.job_id == ""
        assert r.job_name is None


# ── PaginatedResult ──────────────────────────────────────────────────────


class TestPaginatedResult:
    def test_from_dict_basic(self):
        data = {
            "content": [{"id": 1}, {"id": 2}],
            "totalElements": 10,
            "totalPages": 5,
            "page": 1,
            "pageSize": 2,
            "hasNext": True,
            "hasPrevious": False,
        }
        p = PaginatedResult.from_dict(data)
        assert len(p.content) == 2
        assert p.total_elements == 10
        assert p.total_pages == 5
        assert p.page == 1
        assert p.page_size == 2
        assert p.has_next is True
        assert p.has_previous is False

    def test_from_dict_with_item_parser(self):
        data = {
            "jobs": [{"jobId": "j-001", "name": "a"}, {"jobId": "j-002", "name": "b"}],
            "total": 2,
            "pageNumber": 1,
            "size": 20,
        }
        p = PaginatedResult.from_dict(data, item_parser=Job.from_dict)
        assert len(p.content) == 2
        assert isinstance(p.content[0], Job)
        assert p.content[0].job_id == "j-001"

    def test_from_dict_fallback_keys(self):
        """Uses 'jobs'/'list' for content, 'total' for totalElements, etc."""
        data = {"list": [{"id": 1}], "total": 100, "pageNumber": 3, "size": 10}
        p = PaginatedResult.from_dict(data)
        assert len(p.content) == 1
        assert p.total_elements == 100
        assert p.page == 3
        assert p.page_size == 10
        assert p.has_next is True  # 3*10 < 100
        assert p.has_previous is True  # page > 1

    def test_from_dict_auto_compute_totals(self):
        """totalPages auto-computed when not provided."""
        data = {"content": [], "total": 25, "page": 1, "pageSize": 10}
        p = PaginatedResult.from_dict(data)
        assert p.total_pages == 3  # ceil(25/10)

    def test_from_dict_defaults(self):
        p = PaginatedResult.from_dict({})
        assert p.content == []
        assert p.total_elements == 0
        assert p.page == 1
        assert p.page_size == 20
