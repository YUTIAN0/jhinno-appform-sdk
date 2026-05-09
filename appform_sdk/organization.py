"""
Organization API module for Appform SDK
"""

from typing import Any, Dict, Optional


class OrganizationAPI:
    """
    Organization API for Appform.

    Provides methods for managing departments and users.
    """

    def __init__(self, client):
        """
        Initialize the Organization API.

        Args:
            client: AppformClient instance
        """
        self._client = client

    # ==================== Department APIs ====================

    def get_departments(self) -> Dict[str, Any]:
        """
        Get department tree structure.

        Returns:
            Department tree structure
        """
        return self._client.get("/appform/ws/api/deps")

    def create_department(
        self,
        dep_name: str,
        dep_chname: str,
        parent_dep: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a department.

        Args:
            dep_name: Department name (English)
            dep_chname: Department display name (Chinese)
            parent_dep: Parent department name
            description: Department description

        Returns:
            Creation result
        """
        data = {
            "depName": dep_name,
            "depNameCN": dep_chname,
        }

        if parent_dep:
            data["parentDepName"] = parent_dep
        if description:
            data["depNote"] = description

        return self._client.post("/appform/ws/api/deps", json=data)

    def update_department(
        self,
        dep_name: str,
        dep_chname: Optional[str] = None,
        parent_dep: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update a department.

        Args:
            dep_name: Department name
            dep_chname: New display name
            parent_dep: New parent department
            description: New description

        Returns:
            Update result
        """
        data = {}

        if dep_chname:
            data["depNameCN"] = dep_chname
        if parent_dep:
            data["parentDepName"] = parent_dep
        if description:
            data["depNote"] = description

        return self._client.put(f"/appform/ws/api/deps/{dep_name}", json=data)

    def delete_department(self, dep_name: str) -> Dict[str, Any]:
        """
        Delete a department.

        Args:
            dep_name: Department name

        Returns:
            Deletion result
        """
        return self._client.delete(f"/appform/ws/api/deps/{dep_name}")

    # ==================== User APIs ====================

    def get_users(
        self,
        page: int = 1,
        page_size: int = 20,
        dep: Optional[str] = None,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get user list.

        Args:
            page: Page number
            page_size: Number of items per page
            dep: Filter by department
            username: Filter by username

        Returns:
            User list
        """
        params = {
            "currentPage": page,
            "pageSize": page_size,
        }

        if dep:
            params["depName"] = dep
        if username:
            params["keyWord"] = username

        return self._client.get("/appform/ws/api/users", params=params)

    def create_user(
        self,
        username: str,
        chusername: str,
        password: str,
        dep: Optional[str] = None,
        phone: Optional[str] = None,
        mail: Optional[str] = None,
        card: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a user.

        Args:
            username: User account name (English)
            chusername: User display name (Chinese)
            password: User password
            dep: Department name
            phone: Phone number
            mail: Email address
            card: ID card number

        Returns:
            Creation result
        """
        data = {
            "userName": username,
            "userNameCn": chusername,
            "userPassword": password,
        }

        if dep:
            data["depName"] = dep
        if phone:
            data["userTel"] = phone
        if mail:
            data["userMail"] = mail
        if card:
            data["userCard"] = card

        return self._client.post("/appform/ws/api/users", json=data)

    def update_user(
        self,
        username: str,
        chusername: Optional[str] = None,
        dep: Optional[str] = None,
        phone: Optional[str] = None,
        mail: Optional[str] = None,
        card: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update a user.

        Args:
            username: User account name
            chusername: New display name
            dep: New department
            phone: New phone number
            mail: New email address
            card: New ID card number

        Returns:
            Update result
        """
        data = {}

        if chusername:
            data["userNameCn"] = chusername
        if dep:
            data["depName"] = dep
        if phone:
            data["userTel"] = phone
        if mail:
            data["userMail"] = mail
        if card:
            data["userCard"] = card

        return self._client.put(f"/appform/ws/api/users/{username}", json=data)

    def delete_user(self, username: str) -> Dict[str, Any]:
        """
        Delete a user.

        Args:
            username: User account name

        Returns:
            Deletion result
        """
        return self._client.delete(f"/appform/ws/api/users/{username}")

    def reset_password(
        self,
        username: str,
        new_password: str,
    ) -> Dict[str, Any]:
        """
        Reset user password.

        Args:
            username: User account name
            new_password: New password

        Returns:
            Reset result
        """
        return self._client.put(
            f"/appform/ws/api/users/{username}/password/password_reset",
            json={"password": new_password},
        )
