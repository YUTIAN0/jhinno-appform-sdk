"""
Sessions API module for Appform SDK
"""

from typing import Any, Dict, List, Optional


class SessionsAPI:
    """
    Sessions API for Appform.

    Provides methods for managing application sessions.
    """

    def __init__(self, client):
        """
        Initialize the Sessions API.

        Args:
            client: AppformClient instance
        """
        self._client = client

    def start(
        self,
        app_id: str,
        start_new: Optional[bool] = None,
        cwd: Optional[str] = None,
        work_file: Optional[str] = None,
        param: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Start a new session (6.0+).

        Args:
            app_id: Application ID (e.g., "gedit", "xterm")
            start_new: Whether to start a new session (default: false)
            cwd: Working directory path
            work_file: File path to open when starting the application
            param: Launch parameters (need to be URL-encoded)

        Returns:
            Session information with desktopId and jhappUrl

        Example:
            result = client.sessions.start(
                app_id="gedit",
                start_new=True,
                cwd="${HOME}",
            )
        """
        data = {}

        if start_new is not None:
            data["startNew"] = start_new
        if cwd:
            data["cwd"] = cwd
        if work_file:
            data["workFile"] = work_file
        if param:
            data["param"] = param

        return self._client.post(f"/appform/ws/api/apps/{app_id}/start", json=data)

    def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        List all sessions.

        Args:
            page: Page number
            page_size: Number of items per page

        Returns:
            List of all sessions
        """
        params = {
            "page": page,
            "pageSize": page_size,
        }
        return self._client.get("/appform/ws/api/apps/sessions/all", params=params)

    def list(
        self,
        session_ids: Optional[List[str]] = None,
        session_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Query sessions by IDs or name.

        This endpoint requires at least one of session_ids or session_name.
        Use list_all() to list all sessions.

        Args:
            session_ids: List of session IDs to query
            session_name: Session name to query

        Returns:
            Session information matching the query
        """
        params = {}

        if session_ids:
            params["sessionIds"] = ",".join(session_ids)
        if session_name:
            params["sessionName"] = session_name

        return self._client.get("/appform/ws/api/apps/sessions", params=params)

    def share(self, session_id: str, usernames: List[str]) -> Dict[str, Any]:
        """
        Share a session with other users.

        Args:
            session_id: Session ID
            usernames: List of usernames to share with

        Returns:
            Share result
        """
        return self._client.post(
            f"/appform/ws/api/apps/sessions/{session_id}/share",
            json={"usernames": usernames},
        )

    def cancel_share(self, session_id: str) -> Dict[str, Any]:
        """
        Cancel session sharing.

        Args:
            session_id: Session ID

        Returns:
            Cancel result
        """
        return self._client.put(
            f"/appform/ws/api/apps/sessions/{session_id}/share_cancel"
        )

    def transfer_operation(self, session_id: str, username: str) -> Dict[str, Any]:
        """
        Transfer session operation to another user.

        Args:
            session_id: Session ID
            username: Username to transfer operation to

        Returns:
            Transfer result
        """
        return self._client.put(
            f"/appform/ws/api/apps/sessions/{session_id}/operation_transfer",
            json={"username": username},
        )

    def connect(self, session_id: str) -> Dict[str, Any]:
        """
        Connect to a session.

        Args:
            session_id: Session ID

        Returns:
            Connection information
        """
        return self._client.get(f"/appform/ws/api/apps/sessions/{session_id}/connect")

    def disconnect(self, session_id: str) -> Dict[str, Any]:
        """
        Disconnect from a session.

        Args:
            session_id: Session ID

        Returns:
            Disconnect result
        """
        return self._client.put(
            f"/appform/ws/api/apps/sessions/{session_id}/disconnect"
        )

    def batch_disconnect(self, session_ids: List[str]) -> Dict[str, Any]:
        """
        Disconnect from multiple sessions.

        Args:
            session_ids: List of session IDs

        Returns:
            Disconnect result
        """
        return self._client.put(
            "/appform/ws/api/apps/sessions/disconnect",
            json={"sessionIds": session_ids},
        )

    def close(self, session_id: str) -> Dict[str, Any]:
        """
        Close (destroy) a session.

        Args:
            session_id: Session ID

        Returns:
            Close result
        """
        return self._client.put(f"/appform/ws/api/apps/sessions/{session_id}/close")

    def batch_close(self, session_ids: List[str]) -> Dict[str, Any]:
        """
        Close multiple sessions.

        Args:
            session_ids: List of session IDs

        Returns:
            Close result
        """
        return self._client.put(
            "/appform/ws/api/apps/sessions/close",
            json={"sessionIds": session_ids},
        )

    def webclient_connect(self, session_id: str) -> Dict[str, Any]:
        """
        Connect to a session via web browser.

        Args:
            session_id: Session ID

        Returns:
            Connection URL
        """
        return self._client.get(f"/appform/ws/api/apps/webclient/{session_id}/connect")

    # ==================== V2 APIs (6.6+) ====================

    def start_v2(
        self,
        app_id: str,
        start_new: Optional[bool] = None,
        cwd: Optional[str] = None,
        work_file: Optional[str] = None,
        param: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Start a new session using v2 API (6.6+).

        Returns both client and web connection info (clientUrl, webUrl, desktopId).

        Args:
            app_id: Application ID (from apps.list_v2())
            start_new: Whether to start a new session (default: false)
            cwd: Working directory path
            work_file: File path to open when starting the application
            param: Launch parameters (need to be URL-encoded)

        Returns:
            Session information with desktopId, clientUrl, and webUrl

        Example:
            result = client.sessions.start_v2(
                app_id="common_sub",
                start_new=True,
                cwd="${HOME}",
            )
        """
        data = {"appId": app_id}

        if start_new is not None:
            data["startNew"] = start_new
        if cwd:
            data["cwd"] = cwd
        if work_file:
            data["workFile"] = work_file
        if param:
            data["param"] = param

        return self._client.post("/appform/ws/api/v2/app_session", json=data)

    def get_by_session_ids(self, session_ids: List[str]) -> Dict[str, Any]:
        """
        Get session info by multiple session IDs (deprecated).

        Args:
            session_ids: List of session IDs

        Returns:
            Session information
        """
        return self._client.get(
            "/appform/ws/api/apps/listBySessionIds",
            params={"sessionIds": ",".join(session_ids)},
        )

    def get_by_session_name(self, session_name: str) -> Dict[str, Any]:
        """
        Get session info by application name (deprecated).

        Args:
            session_name: Application/session name

        Returns:
            Session information
        """
        return self._client.get(
            "/appform/ws/api/apps/listBySessionName",
            params={"sessionName": session_name},
        )
