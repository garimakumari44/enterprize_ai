"""
Tests for workflow CRUD operations.
"""

import uuid

from fastapi.testclient import TestClient


class TestWorkflowCRUD:
    """
    Workflow CRUD test suite.
    """

    def test_create_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test creating a workflow.
        """

        payload = {
            "name": "Invoice Processing",
            "description": "Process incoming invoices",
        }

        response = client.post(
            "/api/v1/workflows",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 201

        data = response.json()

        assert data["name"] == payload["name"]
        assert data["description"] == payload["description"]
        assert "id" in data


    def test_get_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        created_workflow: dict,
    ):
        """
        Test retrieving a workflow.
        """

        response = client.get(
            f"/api/v1/workflows/{created_workflow['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == created_workflow["id"]


    def test_list_workflows(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test listing workflows.
        """

        response = client.get(
            "/api/v1/workflows",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert isinstance(data, list)


    def test_update_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        created_workflow: dict,
    ):
        """
        Test updating workflow.
        """

        payload = {
            "name": "Updated Workflow",
            "description": "Updated description",
        }

        response = client.put(
            f"/api/v1/workflows/{created_workflow['id']}",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["name"] == payload["name"]
        assert data["description"] == payload["description"]


    def test_delete_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        created_workflow: dict,
    ):
        """
        Test deleting workflow.
        """

        response = client.delete(
            f"/api/v1/workflows/{created_workflow['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        response = client.get(
            f"/api/v1/workflows/{created_workflow['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 404


    def test_get_nonexistent_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test fetching unknown workflow.
        """

        response = client.get(
            f"/api/v1/workflows/{uuid.uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == 404


    def test_create_workflow_without_name(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Name is required.
        """

        payload = {
            "description": "No name",
        }

        response = client.post(
            "/api/v1/workflows",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 422