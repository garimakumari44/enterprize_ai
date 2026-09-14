"""
Tests for workflow version operations.
"""

import uuid

from fastapi.testclient import TestClient


class TestWorkflowVersions:
    """
    Workflow version test suite.
    """

    def test_create_version(
        self,
        client: TestClient,
        auth_headers: dict,
        created_workflow: dict,
    ):
        """
        Test creating a new workflow version.
        """

        payload = {
            "description": "Initial version",
        }

        response = client.post(
            f"/api/v1/workflows/{created_workflow['id']}/versions",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 201

        data = response.json()

        assert "id" in data
        assert "version" in data
        assert data["description"] == payload["description"]


    def test_list_versions(
        self,
        client: TestClient,
        auth_headers: dict,
        created_workflow: dict,
    ):
        """
        Test listing workflow versions.
        """

        response = client.get(
            f"/api/v1/workflows/{created_workflow['id']}/versions",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert isinstance(data, list)


    def test_get_version(
        self,
        client: TestClient,
        auth_headers: dict,
        created_workflow: dict,
        created_version: dict,
    ):
        """
        Test retrieving a workflow version.
        """

        response = client.get(
            f"/api/v1/workflows/{created_workflow['id']}/versions/{created_version['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == created_version["id"]


    def test_publish_version(
        self,
        client: TestClient,
        auth_headers: dict,
        created_workflow: dict,
        created_version: dict,
    ):
        """
        Test publishing a workflow version.
        """

        response = client.post(
            f"/api/v1/workflows/{created_workflow['id']}/versions/{created_version['id']}/publish",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["is_published"] is True


    def test_latest_version(
        self,
        client: TestClient,
        auth_headers: dict,
        created_workflow: dict,
    ):
        """
        Test retrieving the latest workflow version.
        """

        response = client.get(
            f"/api/v1/workflows/{created_workflow['id']}/versions/latest",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert "version" in data


    def test_create_version_unknown_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Creating a version for an unknown workflow should fail.
        """

        payload = {
            "description": "Invalid",
        }

        response = client.post(
            f"/api/v1/workflows/{uuid.uuid4()}/versions",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 404


    def test_get_unknown_version(
        self,
        client: TestClient,
        auth_headers: dict,
        created_workflow: dict,
    ):
        """
        Retrieving an unknown version should return 404.
        """

        response = client.get(
            f"/api/v1/workflows/{created_workflow['id']}/versions/{uuid.uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == 404


    def test_publish_unknown_version(
        self,
        client: TestClient,
        auth_headers: dict,
        created_workflow: dict,
    ):
        """
        Publishing an unknown version should return 404.
        """

        response = client.post(
            f"/api/v1/workflows/{created_workflow['id']}/versions/{uuid.uuid4()}/publish",
            headers=auth_headers,
        )

        assert response.status_code == 404