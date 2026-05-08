"""
Tests for appform_sdk.sessions — SessionsAPI and helper functions.
"""

from unittest.mock import MagicMock, patch

import pytest

from appform_sdk.sessions import (
    SessionsAPI,
    _check_port,
    check_jhapp_client,
    try_launch_jhapp_client,
)


def _make_api():
    """Create SessionsAPI with a mocked client."""
    mock_client = MagicMock()
    mock_client._username = "alice"
    return SessionsAPI(mock_client), mock_client


# ── _check_port ──────────────────────────────────────────────────────────


class TestCheckPort:
    def test_open_port(self):
        mock_socket = MagicMock()
        mock_socket.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket.__exit__ = MagicMock(return_value=False)
        mock_socket.connect_ex.return_value = 0
        with patch("appform_sdk.sessions.socket.socket", return_value=mock_socket):
            assert _check_port("127.0.0.1", 8080) is True

    def test_closed_port(self):
        mock_socket = MagicMock()
        mock_socket.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket.__exit__ = MagicMock(return_value=False)
        mock_socket.connect_ex.return_value = 1
        with patch("appform_sdk.sessions.socket.socket", return_value=mock_socket):
            assert _check_port("127.0.0.1", 8080) is False

    def test_os_error(self):
        with patch(
            "appform_sdk.sessions.socket.socket",
            side_effect=OSError("fail"),
        ):
            assert _check_port("127.0.0.1", 8080) is False


# ── check_jhapp_client ───────────────────────────────────────────────────


class TestCheckJhappClient:
    def test_delegates_to_check_port(self):
        with patch("appform_sdk.sessions._check_port", return_value=True) as mock:
            result = check_jhapp_client()
        assert result is True
        mock.assert_called_once_with("127.0.0.1", 60540, 1.0)

    def test_custom_port(self):
        with patch("appform_sdk.sessions._check_port", return_value=False) as mock:
            check_jhapp_client(port=9999, timeout=2.0)
        mock.assert_called_once_with("127.0.0.1", 9999, 2.0)


# ── try_launch_jhapp_client ──────────────────────────────────────────────


class TestTryLaunchJhappClient:
    def test_client_not_running(self):
        with patch("appform_sdk.sessions.check_jhapp_client", return_value=False):
            assert try_launch_jhapp_client("jhclient://server/app", "d-001") is False

    def test_success(self):
        with patch("appform_sdk.sessions.check_jhapp_client", return_value=True), patch(
            "appform_sdk.sessions._requests"
        ) as mock_req:
            mock_req.get.return_value = MagicMock()
            result = try_launch_jhapp_client("jhclient://server/app", "d-001")
        assert result is True

    def test_request_fails(self):
        with patch("appform_sdk.sessions.check_jhapp_client", return_value=True), patch(
            "appform_sdk.sessions._requests"
        ) as mock_req:
            mock_req.get.side_effect = Exception("timeout")
            result = try_launch_jhapp_client("jhclient://server/app", "d-001")
        assert result is False

    def test_no_requests_module(self):
        with patch("appform_sdk.sessions._HAS_REQUESTS", False):
            assert try_launch_jhapp_client("jhclient://server/app", "d-001") is False


# ── SessionsAPI.start ────────────────────────────────────────────────────


class TestStart:
    def test_basic(self):
        api, client = _make_api()
        api.start("gedit")
        client.post.assert_called_once_with("/appform/ws/api/apps/gedit/start", json={})

    def test_with_options(self):
        api, client = _make_api()
        api.start("gedit", start_new=True, cwd="/home", work_file="a.txt", param="-v")
        body = client.post.call_args.kwargs["json"]
        assert body["startNew"] is True
        assert body["cwd"] == "/home"
        assert body["workFile"] == "a.txt"
        assert body["param"] == "-v"

    def test_none_options_excluded(self):
        api, client = _make_api()
        api.start("app")
        body = client.post.call_args.kwargs["json"]
        assert body == {}


# ── SessionsAPI.list_all ─────────────────────────────────────────────────


class TestListAll:
    def test_defaults(self):
        api, client = _make_api()
        api.list_all()
        client.get.assert_called_once_with(
            "/appform/ws/api/apps/sessions/all",
            params={"page": 1, "pageSize": 20},
        )

    def test_custom_page(self):
        api, client = _make_api()
        api.list_all(page=3, page_size=50)
        params = client.get.call_args.kwargs["params"]
        assert params["page"] == 3
        assert params["pageSize"] == 50


# ── SessionsAPI.list ─────────────────────────────────────────────────────


class TestList:
    def test_with_session_ids(self):
        api, client = _make_api()
        api.list(session_ids=["s-001", "s-002"])
        client.get.assert_called_once_with(
            "/appform/ws/api/apps/sessions",
            params={"sessionIds": "s-001,s-002"},
        )

    def test_with_session_name(self):
        api, client = _make_api()
        api.list(session_name="desktop1")
        client.get.assert_called_once_with(
            "/appform/ws/api/apps/sessions",
            params={"sessionName": "desktop1"},
        )

    def test_no_args_fetches_all(self):
        api, client = _make_api()
        client.get.return_value = {
            "data": {"records": [{"session_id": "s-001", "owner": "alice"}]}
        }
        result = api.list()
        assert len(result["data"]) == 1
        assert result["data"][0]["owner"] == "alice"


# ── SessionsAPI._fetch_all_sessions ──────────────────────────────────────


class TestFetchAllSessions:
    def test_single_page(self):
        api, client = _make_api()
        client.get.return_value = {
            "data": {"records": [{"session_id": "s-001"}, {"session_id": "s-002"}]}
        }
        result = api._fetch_all_sessions()
        assert len(result) == 2

    def test_pagination_stops_on_empty(self):
        api, client = _make_api()
        client.get.side_effect = [
            {"data": {"records": [{"session_id": "s-001"}]}},
            {"data": {"records": []}},
        ]
        result = api._fetch_all_sessions()
        assert len(result) == 1

    def test_deduplication(self):
        api, client = _make_api()
        # Page size is 100, so each page must have >=100 records to continue
        page1 = [{"session_id": f"s-{i:03d}"} for i in range(100)]
        page2 = [{"session_id": f"s-{i:03d}"} for i in range(50, 150)]  # 50-99 dups
        client.get.side_effect = [
            {"data": {"records": page1}},
            {"data": {"records": page2}},
            {"data": {"records": []}},
        ]
        result = api._fetch_all_sessions()
        # 0-99 from page1 + 100-149 new from page2 = 150 unique
        assert len(result) == 150

    def test_list_data_format(self):
        api, client = _make_api()
        client.get.return_value = {"data": [{"session_id": "s-001"}]}
        result = api._fetch_all_sessions()
        assert len(result) == 1


# ── SessionsAPI share / cancel_share / transfer ──────────────────────────


class TestShare:
    def test_share(self):
        api, client = _make_api()
        api.share("s-001", ["bob", "carol"])
        client.post.assert_called_once_with(
            "/appform/ws/api/apps/sessions/s-001/share",
            json={"usernames": ["bob", "carol"]},
        )

    def test_cancel_share(self):
        api, client = _make_api()
        api.cancel_share("s-001")
        client.put.assert_called_once_with(
            "/appform/ws/api/apps/sessions/s-001/share_cancel"
        )

    def test_transfer_operation(self):
        api, client = _make_api()
        api.transfer_operation("s-001", "bob")
        client.put.assert_called_once_with(
            "/appform/ws/api/apps/sessions/s-001/operation_transfer",
            json={"username": "bob"},
        )


# ── SessionsAPI connect / disconnect / close ─────────────────────────────


class TestConnectDisconnectClose:
    def test_connect(self):
        api, client = _make_api()
        api.connect("s-001")
        client.get.assert_called_once_with(
            "/appform/ws/api/apps/sessions/s-001/connect"
        )

    def test_disconnect(self):
        api, client = _make_api()
        api.disconnect("s-001")
        client.put.assert_called_once_with(
            "/appform/ws/api/apps/sessions/s-001/disconnect"
        )

    def test_batch_disconnect(self):
        api, client = _make_api()
        api.batch_disconnect(["s-001", "s-002"])
        client.put.assert_called_once_with(
            "/appform/ws/api/apps/sessions/disconnect",
            json={"sessionIds": ["s-001", "s-002"]},
        )

    def test_close(self):
        api, client = _make_api()
        api.close("s-001")
        client.put.assert_called_once_with("/appform/ws/api/apps/sessions/s-001/close")

    def test_batch_close(self):
        api, client = _make_api()
        api.batch_close(["s-001", "s-002"])
        client.put.assert_called_once_with(
            "/appform/ws/api/apps/sessions/close",
            json={"sessionIds": ["s-001", "s-002"]},
        )

    def test_webclient_connect(self):
        api, client = _make_api()
        api.webclient_connect("s-001")
        client.get.assert_called_once_with(
            "/appform/ws/api/apps/webclient/s-001/connect"
        )


# ── SessionsAPI._resolve_desktop_id ──────────────────────────────────────


class TestResolveDesktopId:
    def test_from_desktop_id(self):
        assert SessionsAPI._resolve_desktop_id({"desktopId": "d-001"}) == "d-001"

    def test_from_session_id(self):
        assert SessionsAPI._resolve_desktop_id({"session_id": "s-001"}) == "s-001"

    def test_from_id(self):
        assert SessionsAPI._resolve_desktop_id({"id": "x-001"}) == "x-001"

    def test_empty(self):
        assert SessionsAPI._resolve_desktop_id({}) == ""


# ── V2 APIs ──────────────────────────────────────────────────────────────


class TestV2APIs:
    def test_start_v2(self):
        api, client = _make_api()
        api.start_v2("common_sub", start_new=True, cwd="/home")
        body = client.post.call_args.kwargs["json"]
        assert body["appId"] == "common_sub"
        assert body["startNew"] is True
        assert body["cwd"] == "/home"
        client.post.assert_called_once_with("/appform/ws/api/v2/app_session", json=body)

    def test_start_v2_minimal(self):
        api, client = _make_api()
        api.start_v2("app1")
        body = client.post.call_args.kwargs["json"]
        assert body == {"appId": "app1"}

    def test_get_by_session_ids(self):
        api, client = _make_api()
        api.get_by_session_ids(["s-001", "s-002"])
        client.get.assert_called_once_with(
            "/appform/ws/api/apps/listBySessionIds",
            params={"sessionIds": "s-001,s-002"},
        )

    def test_get_by_session_name(self):
        api, client = _make_api()
        api.get_by_session_name("desktop1")
        client.get.assert_called_once_with(
            "/appform/ws/api/apps/listBySessionName",
            params={"sessionName": "desktop1"},
        )


# ── connect_and_launch ───────────────────────────────────────────────────


class TestConnectAndLaunch:
    def test_no_data(self):
        api, client = _make_api()
        client.get.return_value = {"data": []}
        result = api.connect_and_launch("s-001")
        assert result == {"data": []}

    def test_no_jhapp_url(self, capsys):
        api, client = _make_api()
        client.get.return_value = {"data": [{"desktopId": "d-001", "jhappUrl": ""}]}
        result = api.connect_and_launch("s-001")
        assert "Error" in capsys.readouterr().out

    def test_launch_success(self, capsys):
        api, client = _make_api()
        client.get.return_value = {
            "data": [{"desktopId": "d-001", "jhappUrl": "jhclient://server/app"}]
        }
        with patch("appform_sdk.sessions.try_launch_jhapp_client", return_value=True):
            result = api.connect_and_launch("s-001")
        assert "launched" in capsys.readouterr().out.lower()

    def test_launch_fallback(self, capsys):
        api, client = _make_api()
        client.get.return_value = {
            "data": [{"desktopId": "d-001", "jhappUrl": "jhclient://server/app"}]
        }
        with patch("appform_sdk.sessions.try_launch_jhapp_client", return_value=False):
            result = api.connect_and_launch("s-001")
        assert "falling back" in capsys.readouterr().out.lower()

    def test_list_data_format(self):
        api, client = _make_api()
        client.get.return_value = {
            "data": {"desktopId": "d-001", "jhappUrl": "jhclient://server/app"}
        }
        with patch("appform_sdk.sessions.try_launch_jhapp_client", return_value=True):
            result = api.connect_and_launch("s-001")
        assert result["data"]["desktopId"] == "d-001"
