"""
Tests for appform_sdk.jobs — JobsAPI.
"""

import json
from unittest.mock import MagicMock

import pytest

from appform_sdk.jobs import JobsAPI


def _make_api():
    """Create JobsAPI with a mocked client."""
    mock_client = MagicMock()
    return JobsAPI(mock_client), mock_client


# ── submit ───────────────────────────────────────────────────────────────


class TestSubmit:
    def test_basic(self):
        api, client = _make_api()
        api.submit("fluent", {"JH_CAS": "/path/test.cas", "JH_NCPU": "8"})
        call_kwargs = client.post.call_args
        assert call_kwargs.args[0] == "/appform/ws/api/jobs/jsub"
        params = call_kwargs.kwargs["params"]
        assert params["appId"] == "fluent"
        parsed = json.loads(params["params"])
        assert parsed["JH_CAS"] == "/path/test.cas"
        assert parsed["JH_NCPU"] == "8"


# ── get_job ──────────────────────────────────────────────────────────────


class TestGetJob:
    def test_basic(self):
        api, client = _make_api()
        client.get.return_value = {"data": {"jobId": "j-001"}}
        result = api.get_job("j-001")
        client.get.assert_called_once_with("/appform/ws/api/jobs/j-001")
        assert result["data"]["jobId"] == "j-001"


# ── list_jobs ────────────────────────────────────────────────────────────


class TestListJobs:
    def test_defaults(self):
        api, client = _make_api()
        api.list_jobs()
        params = client.get.call_args.kwargs["params"]
        assert params["page"] == 1
        assert params["pageSize"] == 20
        assert "condition" not in params

    def test_name_filter(self):
        api, client = _make_api()
        api.list_jobs(name_filter="test")
        params = client.get.call_args.kwargs["params"]
        condition = json.loads(params["condition"])
        assert len(condition["filters"]) == 1
        assert condition["filters"][0]["field"] == "name"
        assert condition["filters"][0]["value"] == "test"

    def test_status_filter_single(self):
        api, client = _make_api()
        api.list_jobs(status_filter=["RUN"])
        condition = json.loads(client.get.call_args.kwargs["params"]["condition"])
        f = condition["filters"][0]
        assert f["field"] == "status"
        assert f["value"] == "RUN"

    def test_status_filter_multiple(self):
        api, client = _make_api()
        api.list_jobs(status_filter=["RUN", "PEND"])
        condition = json.loads(client.get.call_args.kwargs["params"]["condition"])
        group = condition["filters"][0]
        assert group["logic"] == "or"
        assert len(group["filters"]) == 2

    def test_app_name_filter(self):
        api, client = _make_api()
        api.list_jobs(app_name_filter="starccm")
        condition = json.loads(client.get.call_args.kwargs["params"]["condition"])
        assert condition["filters"][0]["field"] == "appName"

    def test_queue_filter(self):
        api, client = _make_api()
        api.list_jobs(queue_filter="gpu")
        condition = json.loads(client.get.call_args.kwargs["params"]["condition"])
        assert condition["filters"][0]["field"] == "queue"

    def test_combined_filters(self):
        api, client = _make_api()
        api.list_jobs(name_filter="sim", status_filter=["RUN"], queue_filter="gpu")
        condition = json.loads(client.get.call_args.kwargs["params"]["condition"])
        assert len(condition["filters"]) == 3
        assert condition["logic"] == "and"

    def test_custom_condition_overrides(self):
        api, client = _make_api()
        custom = {"filters": [{"field": "x", "value": "1"}], "logic": "and"}
        api.list_jobs(name_filter="ignored", condition=custom)
        params = client.get.call_args.kwargs["params"]
        parsed = json.loads(params["condition"])
        assert parsed["filters"][0]["field"] == "x"


# ── list_jobs_by_ids ─────────────────────────────────────────────────────


class TestListJobsByIds:
    def test_basic(self):
        api, client = _make_api()
        api.list_jobs_by_ids(["j-001", "j-002"])
        client.get.assert_called_once_with(
            "/appform/ws/api/jobs/list",
            params={"jobIds": "j-001,j-002"},
        )


# ── list_history ─────────────────────────────────────────────────────────


class TestListHistory:
    def test_defaults(self):
        api, client = _make_api()
        api.list_history()
        params = client.get.call_args.kwargs["params"]
        assert params["page"] == 1
        assert "condition" not in params

    def test_with_condition(self):
        api, client = _make_api()
        cond = {"filters": [], "logic": "and"}
        api.list_history(condition=cond)
        params = client.get.call_args.kwargs["params"]
        assert json.loads(params["condition"]) == cond


# ── perform_action / stop / suspend / resume / requeue ───────────────────


class TestActions:
    def test_perform_action(self):
        api, client = _make_api()
        api.perform_action("j-001", "stop")
        client.put.assert_called_once_with("/appform/ws/api/jobs/j-001/stop")

    def test_stop(self):
        api, client = _make_api()
        api.stop("j-001")
        assert "/j-001/stop" in client.put.call_args.args[0]

    def test_suspend(self):
        api, client = _make_api()
        api.suspend("j-001")
        assert "/j-001/suspend" in client.put.call_args.args[0]

    def test_resume(self):
        api, client = _make_api()
        api.resume("j-001")
        assert "/j-001/resume" in client.put.call_args.args[0]

    def test_requeue(self):
        api, client = _make_api()
        api.requeue("j-001")
        assert "/j-001/requeue" in client.put.call_args.args[0]


# ── batch actions ────────────────────────────────────────────────────────


class TestBatchActions:
    def test_batch_action(self):
        api, client = _make_api()
        api.batch_action(["j-001", "j-002"], "stop")
        client.put.assert_called_once_with(
            "/appform/ws/api/jobs/stop",
            params={"jobIds": "j-001,j-002"},
        )

    def test_batch_stop(self):
        api, client = _make_api()
        api.batch_stop(["j-001"])
        assert "/stop" in client.put.call_args.args[0]

    def test_batch_suspend(self):
        api, client = _make_api()
        api.batch_suspend(["j-001"])
        assert "/suspend" in client.put.call_args.args[0]

    def test_batch_resume(self):
        api, client = _make_api()
        api.batch_resume(["j-001"])
        assert "/resume" in client.put.call_args.args[0]

    def test_batch_requeue(self):
        api, client = _make_api()
        api.batch_requeue(["j-001"])
        assert "/requeue" in client.put.call_args.args[0]


# ── history / output / files / connect ───────────────────────────────────


class TestJobQueries:
    def test_get_history(self):
        api, client = _make_api()
        api.get_history("j-001")
        client.get.assert_called_once_with("/appform/ws/api/jobs/j-001/hist")

    def test_get_batch_history(self):
        api, client = _make_api()
        api.get_batch_history(["j-001", "j-002"])
        client.get.assert_called_once_with(
            "/appform/ws/api/jobs/hist",
            params={"jobIds": "j-001,j-002"},
        )

    def test_get_output(self):
        api, client = _make_api()
        api.get_output("j-001")
        client.get.assert_called_once_with("/appform/ws/api/jobs/j-001/peek")

    def test_get_files(self):
        api, client = _make_api()
        api.get_files("j-001")
        client.get.assert_called_once_with("/appform/ws/api/jobs/j-001/files")

    def test_connect(self):
        api, client = _make_api()
        api.connect("j-001")
        client.post.assert_called_once_with("/appform/ws/api/jobs/j-001/connect")


# ── V2 APIs ──────────────────────────────────────────────────────────────


class TestV2APIs:
    def test_submit_v2(self):
        api, client = _make_api()
        api.submit_v2("fluent", {"JH_CAS": "/path/cas"})
        call_kwargs = client.post.call_args
        assert call_kwargs.args[0] == "/appform/ws/api/v2/jobs"
        body = call_kwargs.kwargs["json"]
        assert body["appId"] == "fluent"
        assert body["params"]["JH_CAS"] == "/path/cas"

    def test_list_jobs_v2(self):
        api, client = _make_api()
        api.list_jobs_v2(page=2, page_size=50)
        params = client.get.call_args.kwargs["params"]
        assert params["page"] == 2
        assert params["pageSize"] == 50
        client.get.assert_called_once_with("/appform/ws/api/v2/jobs", params=params)

    def test_list_jobs_v2_with_condition(self):
        api, client = _make_api()
        cond = {"filters": []}
        api.list_jobs_v2(condition=cond)
        params = client.get.call_args.kwargs["params"]
        assert json.loads(params["condition"]) == cond

    def test_delete_job(self):
        api, client = _make_api()
        api.delete_job("j-001")
        client.delete.assert_called_once_with("/appform/ws/api/v2/jobs/j-001")

    def test_get_form(self):
        api, client = _make_api()
        api.get_form("fluent")
        client.get.assert_called_once_with("/appform/ws/api/v2/app/form/fluent")

    def test_get_tooltip(self):
        api, client = _make_api()
        api.get_tooltip()
        client.get.assert_called_once_with("/appform/ws/api/v2/jobs/tooltip")

    def test_get_total_history_count(self):
        api, client = _make_api()
        api.get_total_history_count()
        client.get.assert_called_once_with("/appform/workspace/myjob/totalHistory")
