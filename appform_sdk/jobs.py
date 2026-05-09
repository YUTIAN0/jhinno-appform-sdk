"""
Jobs API module for Appform SDK
"""

import json
from typing import Any, Dict, List, Optional


class JobsAPI:
    """
    Jobs API for Appform.

    Provides methods for submitting, querying, and managing jobs.
    """

    # Job status constants
    STATUS_RUNNING = "RUN"  # 运行
    STATUS_PENDING = "PEND"  # 等待
    STATUS_UNKNOWN = "UNKNOWN"  # 状态不明
    STATUS_PSUSP = "PSUSP"  # 等待中挂起
    STATUS_USUSP = "USUSP"  # 用户挂起
    STATUS_SSUSP = "SSUSP"  # 系统挂起
    STATUS_ZOMBI = "ZOMBI"  # 僵尸
    STATUS_DONE = "DONE"  # 完成
    STATUS_EXIT = "EXIT"  # 退出

    # Job action constants
    ACTION_STOP = "stop"
    ACTION_SUSPEND = "suspend"
    ACTION_RESUME = "resume"
    ACTION_REQUEUE = "requeue"

    def __init__(self, client):
        """
        Initialize the Jobs API.

        Args:
            client: AppformClient instance
        """
        self._client = client

    def submit(
        self,
        app_id: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Submit a new job (6.0+).

        Uses multipart/form-data with appId and params JSON string.

        Args:
            app_id: Application ID (e.g., "fluent", "starccm")
            params: Job parameters dict, keys depend on the application.
                Common keys include:
                - JH_JOB_NAME: Job name
                - JH_CAS: CAS file path (required for most apps)
                - JH_NCPU: Number of CPU cores (default: 2)
                - JH_ITERATION: Iteration count
                - JH_PROJECT: Project name (default: "default")
                - JH_RELEASE: Application version
                - JH_GUI_ENABLED: GUI support ("on"/"off")
                - JH_JOB_CONF: Job confidentiality level
                - JOB_PRIORITY: Priority ("normal"/"high")

        Returns:
            Response with job ID

        Example:
            result = client.jobs.submit(
                app_id="fluent",
                params={
                    "JH_JOB_NAME": "test_job",
                    "JH_CAS": "/home/user/cases/test.cas",
                    "JH_NCPU": "8",
                    "JH_ITERATION": "100",
                    "JH_GUI_ENABLED": "off",
                },
            )
        """
        return self._client.post(
            "/appform/ws/api/jobs/jsub",
            params={
                "appId": app_id,
                "params": json.dumps(params, ensure_ascii=False),
            },
        )

    def get_job(self, job_id: str) -> Dict[str, Any]:
        """
        Get job details by ID.

        Args:
            job_id: Job ID

        Returns:
            Job details
        """
        return self._client.get(f"/appform/ws/api/jobs/{job_id}")

    def list_jobs(
        self,
        page: int = 1,
        page_size: int = 20,
        name_filter: Optional[str] = None,
        status_filter: Optional[List[str]] = None,
        app_name_filter: Optional[str] = None,
        queue_filter: Optional[str] = None,
        condition: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        List jobs with pagination and filtering.

        Args:
            page: Page number (starting from 1)
            page_size: Number of items per page
            name_filter: Filter by job name (contains)
            status_filter: Filter by job status (list of statuses).
                Valid values: RUN, PEND, UNKNOWN, PSUSP, USUSP, SSUSP, ZOMBI, DONE, EXIT
            app_name_filter: Filter by application name (contains)
            queue_filter: Filter by queue name (contains)
            condition: Custom filter condition (JSON structure). Mutually exclusive
                with name_filter, status_filter, app_name_filter, queue_filter —
                if condition is provided, all other filters are ignored.

        Returns:
            Paginated job list
        """
        params = {
            "page": page,
            "pageSize": page_size,
        }

        if condition:
            params["condition"] = json.dumps(condition)
        elif any([name_filter, status_filter, app_name_filter, queue_filter]):
            filters = []

            if name_filter:
                filters.append(
                    {
                        "type": "string",
                        "operator": "contains",
                        "ignoreCase": True,
                        "field": "name",
                        "value": name_filter,
                    }
                )

            if status_filter:
                status_filters = [
                    {
                        "field": "status",
                        "operator": "eq",
                        "value": status,
                        "type": "string",
                        "ignoreCase": True,
                    }
                    for status in status_filter
                ]
                if len(status_filters) == 1:
                    filters.append(status_filters[0])
                else:
                    filters.append(
                        {
                            "logic": "or",
                            "filters": status_filters,
                        }
                    )

            if app_name_filter:
                filters.append(
                    {
                        "type": "string",
                        "operator": "contains",
                        "ignoreCase": True,
                        "field": "appName",
                        "value": app_name_filter,
                    }
                )

            if queue_filter:
                filters.append(
                    {
                        "type": "string",
                        "operator": "contains",
                        "ignoreCase": True,
                        "field": "queue",
                        "value": queue_filter,
                    }
                )

            condition = {"filters": filters, "logic": "and"}
            params["condition"] = json.dumps(condition)

        return self._client.get("/appform/ws/api/jobs/page", params=params)

    def list_jobs_by_ids(self, job_ids: List[str]) -> Dict[str, Any]:
        """
        Get multiple jobs by IDs.

        Args:
            job_ids: List of job IDs

        Returns:
            List of job details
        """
        return self._client.get(
            "/appform/ws/api/jobs/list",
            params={"jobIds": ",".join(job_ids)},
        )

    def list_history(
        self,
        page: int = 1,
        page_size: int = 20,
        condition: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        List historical jobs with pagination.

        Args:
            page: Page number
            page_size: Number of items per page
            condition: Filter condition

        Returns:
            Paginated historical job list
        """
        params = {
            "page": page,
            "pageSize": page_size,
        }

        if condition:
            params["condition"] = json.dumps(condition)

        return self._client.get("/appform/ws/api/jobs/historyPage", params=params)

    def perform_action(self, job_id: str, action: str) -> Dict[str, Any]:
        """
        Perform an action on a job.

        Args:
            job_id: Job ID
            action: Action to perform (stop, suspend, resume, requeue)

        Returns:
            Action result
        """
        return self._client.put(f"/appform/ws/api/jobs/{job_id}/{action}")

    def stop(self, job_id: str) -> Dict[str, Any]:
        """Stop a job."""
        return self.perform_action(job_id, self.ACTION_STOP)

    def suspend(self, job_id: str) -> Dict[str, Any]:
        """Suspend a job."""
        return self.perform_action(job_id, self.ACTION_SUSPEND)

    def resume(self, job_id: str) -> Dict[str, Any]:
        """Resume a suspended job."""
        return self.perform_action(job_id, self.ACTION_RESUME)

    def requeue(self, job_id: str) -> Dict[str, Any]:
        """Requeue a job."""
        return self.perform_action(job_id, self.ACTION_REQUEUE)

    def batch_action(self, job_ids: List[str], action: str) -> Dict[str, Any]:
        """
        Perform an action on multiple jobs.

        Args:
            job_ids: List of job IDs
            action: Action to perform

        Returns:
            Action result
        """
        return self._client.put(
            f"/appform/ws/api/jobs/{action}",
            params={"jobIds": ",".join(job_ids)},
        )

    def batch_stop(self, job_ids: List[str]) -> Dict[str, Any]:
        """Stop multiple jobs."""
        return self.batch_action(job_ids, self.ACTION_STOP)

    def batch_suspend(self, job_ids: List[str]) -> Dict[str, Any]:
        """Suspend multiple jobs."""
        return self.batch_action(job_ids, self.ACTION_SUSPEND)

    def batch_resume(self, job_ids: List[str]) -> Dict[str, Any]:
        """Resume multiple jobs."""
        return self.batch_action(job_ids, self.ACTION_RESUME)

    def batch_requeue(self, job_ids: List[str]) -> Dict[str, Any]:
        """Requeue multiple jobs."""
        return self.batch_action(job_ids, self.ACTION_REQUEUE)

    def get_history(self, job_id: str) -> Dict[str, Any]:
        """
        Get job history.

        Args:
            job_id: Job ID

        Returns:
            Job history
        """
        return self._client.get(f"/appform/ws/api/jobs/{job_id}/hist")

    def get_batch_history(self, job_ids: List[str]) -> Dict[str, Any]:
        """
        Get history for multiple jobs.

        Args:
            job_ids: List of job IDs

        Returns:
            Job histories
        """
        return self._client.get(
            "/appform/ws/api/jobs/hist",
            params={"jobIds": ",".join(job_ids)},
        )

    def get_output(self, job_id: str) -> Dict[str, Any]:
        """
        Get job dynamic output.

        Args:
            job_id: Job ID

        Returns:
            Job output
        """
        return self._client.get(f"/appform/ws/api/jobs/{job_id}/peek")

    def get_files(self, job_id: str) -> Dict[str, Any]:
        """
        Get job data files list.

        Args:
            job_id: Job ID

        Returns:
            List of job files
        """
        return self._client.get(f"/appform/ws/api/jobs/{job_id}/files")

    def connect(self, job_id: str) -> Dict[str, Any]:
        """
        Connect to a job's graphical session.

        Args:
            job_id: Job ID

        Returns:
            Connection information
        """
        return self._client.post(f"/appform/ws/api/jobs/{job_id}/connect")

    # ==================== V2 APIs (6.6+) ====================

    def submit_v2(
        self,
        app_id: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Submit a new job using v2 API (6.6+).

        Uses application/json with appId and params object.
        The params structure can be obtained via get_form(app_id).

        Args:
            app_id: Application ID
            params: Job parameters dict (keys depend on application form).
                Use get_form(app_id) to discover available parameters.

        Returns:
            Response with job ID

        Example:
            # First get the form to see available parameters
            form = client.jobs.get_form("fluent")

            # Then submit with the required parameters
            result = client.jobs.submit_v2(
                app_id="fluent",
                params={
                    "JH_CAS": "/home/user/cases/test.cas",
                    "JH_NCPU": "8",
                    "JH_ITERATION": "100",
                },
            )
        """
        return self._client.post(
            "/appform/ws/api/v2/jobs",
            json={
                "appId": app_id,
                "params": params,
            },
        )

    def list_jobs_v2(
        self,
        page: int = 1,
        page_size: int = 20,
        condition: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        List jobs with pagination using v2 API (6.6+).

        Args:
            page: Page number
            page_size: Number of items per page
            condition: Custom filter condition

        Returns:
            Paginated job list
        """
        params = {"page": page, "pageSize": page_size}
        if condition:
            params["condition"] = json.dumps(condition)
        return self._client.get("/appform/ws/api/v2/jobs", params=params)

    def delete_job(self, job_id: str) -> Dict[str, Any]:
        """
        Delete a job (6.6+).

        Args:
            job_id: Job ID

        Returns:
            Deletion result
        """
        return self._client.delete(f"/appform/ws/api/v2/jobs/{job_id}")

    def get_form(self, app_id: str) -> Dict[str, Any]:
        """
        Get job submission form for an app (6.6+).

        Args:
            app_id: Application ID

        Returns:
            Job form definition
        """
        return self._client.get(f"/appform/ws/api/v2/app/form/{app_id}")

    def get_tooltip(self) -> Dict[str, Any]:
        """
        Get job app monitoring info (6.6+).

        Returns:
            Job monitoring tooltip data
        """
        return self._client.get("/appform/ws/api/v2/jobs/tooltip")

    def get_total_history_count(self) -> Dict[str, Any]:
        """
        Get total history job count (6.6+).

        Returns:
            Total history job count
        """
        return self._client.get("/appform/workspace/myjob/totalHistory")
