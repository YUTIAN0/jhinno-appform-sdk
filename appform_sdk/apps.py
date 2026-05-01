"""
Apps API module for Appform SDK
"""

from typing import Any, Dict, Optional


class AppsAPI:
    """
    Apps API for Appform.

    Provides methods for querying application information.
    """

    def __init__(self, client):
        """
        Initialize the Apps API.

        Args:
            client: AppformClient instance
        """
        self._client = client

    def list_all(self) -> Dict[str, Any]:
        """
        Get all application menus.

        Returns:
            List of all applications
        """
        return self._client.get("/appform/ws/api/apps")

    def get_url(self, app_name: str) -> Dict[str, Any]:
        """
        Get URL for a specific application.

        Args:
            app_name: Application name

        Returns:
            Application URL information
        """
        return self._client.get(f"/appform/ws/api/apps/{app_name}/url")

    def get_form_params(self, app_id: str) -> Dict[str, Any]:
        """
        Get form parameters for a compute application.

        Args:
            app_id: Application ID

        Returns:
            Form parameters
        """
        return self._client.get(
            "/appform/appstore/app-info/v1/form_params",
            params={"appId": app_id},
        )

    def get_file_extensions(self) -> Dict[str, Any]:
        """
        Get file extension associations for graphical applications.

        Returns:
            File extension associations
        """
        return self._client.get("/appform/appstore/app-info/v1/user/findChooseBaseList")

    def list_v2(self) -> Dict[str, Any]:
        """
        Get available compute, interactive, and web applications (6.6+).

        Returns:
            List of available applications with detailed information
        """
        return self._client.get("/appform/ws/api/v2/apps")
