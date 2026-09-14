"""
Tests for workflow validation.
"""

from fastapi.testclient import TestClient


class TestWorkflowValidation:
    """
    Workflow validation test suite.
    """

    def test_validate_valid_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        valid_workflow: dict,
    ):
        """
        A valid workflow should pass validation.
        """

        response = client.post(
            f"/api/v1/workflows/{valid_workflow['id']}/validate",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["valid"] is True
        assert data["errors"] == []


    def test_validate_empty_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        empty_workflow: dict,
    ):
        """
        Workflow without nodes should fail.
        """

        response = client.post(
            f"/api/v1/workflows/{empty_workflow['id']}/validate",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["valid"] is False
        assert len(data["errors"]) > 0


    def test_validate_missing_start_node(
        self,
        client: TestClient,
        auth_headers: dict,
        workflow_without_start: dict,
    ):
        """
        Workflow must contain exactly one start node.
        """

        response = client.post(
            f"/api/v1/workflows/{workflow_without_start['id']}/validate",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["valid"] is False


    def test_validate_multiple_start_nodes(
        self,
        client: TestClient,
        auth_headers: dict,
        workflow_multiple_starts: dict,
    ):
        """
        Multiple start nodes are not allowed.
        """

        response = client.post(
            f"/api/v1/workflows/{workflow_multiple_starts['id']}/validate",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["valid"] is False


    def test_validate_missing_end_node(
        self,
        client: TestClient,
        auth_headers: dict,
        workflow_without_end: dict,
    ):
        """
        Workflow should contain an end node.
        """

        response = client.post(
            f"/api/v1/workflows/{workflow_without_end['id']}/validate",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["valid"] is False


    def test_validate_disconnected_node(
        self,
        client: TestClient,
        auth_headers: dict,
        workflow_with_disconnected_node: dict,
    ):
        """
        Every node should be connected.
        """

        response = client.post(
            f"/api/v1/workflows/{workflow_with_disconnected_node['id']}/validate",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["valid"] is False


    def test_validate_cycle_detection(
        self,
        client: TestClient,
        auth_headers: dict,
        workflow_with_cycle: dict,
    ):
        """
        Cyclic workflows should fail validation.
        """

        response = client.post(
            f"/api/v1/workflows/{workflow_with_cycle['id']}/validate",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["valid"] is False


    def test_validate_unknown_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Unknown workflow returns 404.
        """

        response = client.post(
            "/api/v1/workflows/00000000-0000-0000-0000-000000000000/validate",
            headers=auth_headers,
        )

        assert response.status_code == 404