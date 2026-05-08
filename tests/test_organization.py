"""
Tests for appform_sdk.organization — OrganizationAPI.
"""

from unittest.mock import MagicMock

import pytest

from appform_sdk.organization import OrganizationAPI


def _make_api():
    """Create OrganizationAPI with a mocked client."""
    mock_client = MagicMock()
    return OrganizationAPI(mock_client), mock_client


# ── Department APIs ──────────────────────────────────────────────────────


class TestGetDepartments:
    def test_basic(self):
        api, client = _make_api()
        client.get.return_value = {"data": [{"depName": "eng"}]}
        result = api.get_departments()
        client.get.assert_called_once_with("/appform/ws/api/deps")
        assert result["data"][0]["depName"] == "eng"


class TestCreateDepartment:
    def test_basic(self):
        api, client = _make_api()
        client.post.return_value = {"result": "success"}
        result = api.create_department("engineering", "工程部")
        client.post.assert_called_once_with(
            "/appform/ws/api/deps",
            json={"depName": "engineering", "depNameCN": "工程部"},
        )
        assert result["result"] == "success"

    def test_with_optional_fields(self):
        api, client = _make_api()
        api.create_department("team1", "团队1", parent_dep="eng", description="desc")
        call_kwargs = client.post.call_args
        data = call_kwargs.kwargs["json"]
        assert data["parentDepName"] == "eng"
        assert data["depNote"] == "desc"

    def test_without_optional_fields(self):
        api, client = _make_api()
        api.create_department("team1", "团队1")
        data = client.post.call_args.kwargs["json"]
        assert "parentDepName" not in data
        assert "depNote" not in data


class TestUpdateDepartment:
    def test_basic(self):
        api, client = _make_api()
        api.update_department("eng", dep_chname="新工程部")
        client.put.assert_called_once_with(
            "/appform/ws/api/deps/eng",
            json={"depNameCN": "新工程部"},
        )

    def test_all_fields(self):
        api, client = _make_api()
        api.update_department(
            "eng", dep_chname="新名", parent_dep="root", description="new desc"
        )
        data = client.put.call_args.kwargs["json"]
        assert data["depNameCN"] == "新名"
        assert data["parentDepName"] == "root"
        assert data["depNote"] == "new desc"

    def test_empty_fields_excluded(self):
        api, client = _make_api()
        api.update_department("eng")
        data = client.put.call_args.kwargs["json"]
        assert data == {}


class TestDeleteDepartment:
    def test_basic(self):
        api, client = _make_api()
        api.delete_department("eng")
        client.delete.assert_called_once_with("/appform/ws/api/deps/eng")


# ── User APIs ────────────────────────────────────────────────────────────


class TestGetUsers:
    def test_defaults(self):
        api, client = _make_api()
        api.get_users()
        client.get.assert_called_once_with(
            "/appform/ws/api/users",
            params={"currentPage": 1, "pageSize": 20},
        )

    def test_with_filters(self):
        api, client = _make_api()
        api.get_users(page=2, page_size=50, dep="eng", username="alice")
        params = client.get.call_args.kwargs["params"]
        assert params["currentPage"] == 2
        assert params["pageSize"] == 50
        assert params["depName"] == "eng"
        assert params["keyWord"] == "alice"

    def test_partial_filters(self):
        api, client = _make_api()
        api.get_users(dep="eng")
        params = client.get.call_args.kwargs["params"]
        assert "depName" in params
        assert "keyWord" not in params


class TestCreateUser:
    def test_basic(self):
        api, client = _make_api()
        api.create_user("alice", "爱丽丝", "pass123")
        data = client.post.call_args.kwargs["json"]
        assert data["userName"] == "alice"
        assert data["userNameCn"] == "爱丽丝"
        assert data["userPassword"] == "pass123"
        client.post.assert_called_once_with("/appform/ws/api/users", json=data)

    def test_with_optional_fields(self):
        api, client = _make_api()
        api.create_user(
            "bob", "鲍勃", "pass", dep="eng", phone="123", mail="b@c.com", card="007"
        )
        data = client.post.call_args.kwargs["json"]
        assert data["depName"] == "eng"
        assert data["userTel"] == "123"
        assert data["userMail"] == "b@c.com"
        assert data["userCard"] == "007"

    def test_without_optional_fields(self):
        api, client = _make_api()
        api.create_user("carol", "卡罗尔", "pass")
        data = client.post.call_args.kwargs["json"]
        assert "depName" not in data
        assert "userTel" not in data


class TestUpdateUser:
    def test_basic(self):
        api, client = _make_api()
        api.update_user("alice", chusername="新名")
        client.put.assert_called_once_with(
            "/appform/ws/api/users/alice",
            json={"userNameCn": "新名"},
        )

    def test_all_fields(self):
        api, client = _make_api()
        api.update_user(
            "alice",
            chusername="新名",
            dep="hr",
            phone="999",
            mail="a@b.com",
            card="001",
        )
        data = client.put.call_args.kwargs["json"]
        assert data["userNameCn"] == "新名"
        assert data["depName"] == "hr"
        assert data["userTel"] == "999"
        assert data["userMail"] == "a@b.com"
        assert data["userCard"] == "001"

    def test_empty_fields_excluded(self):
        api, client = _make_api()
        api.update_user("alice")
        data = client.put.call_args.kwargs["json"]
        assert data == {}


class TestDeleteUser:
    def test_basic(self):
        api, client = _make_api()
        api.delete_user("alice")
        client.delete.assert_called_once_with("/appform/ws/api/users/alice")


class TestResetPassword:
    def test_basic(self):
        api, client = _make_api()
        api.reset_password("alice", "newpass123")
        client.put.assert_called_once_with(
            "/appform/ws/api/users/alice/password/password_reset",
            json={"password": "newpass123"},
        )
