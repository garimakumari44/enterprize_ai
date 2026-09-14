"""
Tests for workflow node operations.
"""

import uuid

from fastapi.testclient import TestClient


class TestWorkflowNodes:
    """
    Workflow node test suite.
    """

    def test_create_node(
        self,
        client: TestClient,
        auth_headers: dict,
        created_workflow: dict,
    ):
        """
        Test creating a workflow node.
        """

        payload = {
            "name": "Start",
            "type": "start",
            "position_x": 100,
            "position_y": 200,
            "config": {},
        }

        response = client.post(
            f"/api/v1/workflows/{created_workflow['id']}/nodes",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 201

        data = response.json()

        assert data["name"] == payload["name"]
        assert data["type"] == payload["type"]
        assert data["position_x"] == payload["position_x"]
        assert data["position_y"] == payload["position_y"]


    def test_list_nodes(
        self,
        client: TestClient,
        auth_headers: dict,
        created_workflow: dict,
    ):
        """
        Test listing workflow nodes.
        """

        response = client.get(
            f"/api/v1/workflows/{created_workflow['id']}/nodes",
            headers=auth_headers,
        )

        assert response.status_code == 200

        assert isinstance(response.json(), list)


    def test_get_node(
        self,
        client: TestClient,
        auth_headers: dict,
        created_node: dict,
        created_workflow: dict,
    ):
        """
        Test retrieving a node.
        """

        response = client.get(
            f"/api/v1/workflows/{created_workflow['id']}/nodes/{created_node['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == created_node["id"]


    def test_update_node(
        self,
        client: TestClient,
        auth_headers: dict,
        created_node: dict,
        created_workflow: dict,
    ):
        """
        Test updating node.
        """

        payload = {
            "name": "Updated Start",
            "position_x": 400,
            "position_y": 500,
        }

        response = client.put(
            f"/api/v1/workflows/{created_workflow['id']}/nodes/{created_node['id']}",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["name"] == payload["name"]
        assert data["position_x"] == payload["position_x"]
        assert data["position_y"] == payload["position_y"]


    def test_delete_node(
        self,
        client: TestClient,
        auth_headers: dict,
        created_node: dict,
        created_workflow: dict,
    ):
        """
        Test deleting node.
        """

        response = client.delete(
            f"/api/v1/workflows/{created_workflow['id']}/nodes/{created_node['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 204


    def test_create_node_invalid_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Cannot create node for unknown workflow.
        """

        payload = {
            "name": "Start",
            "type": "start",
            "position_x": 0,
            "position_y": 0,
            "config": {},
        }

        response = client.post(
            f"/api/v1/workflows/{uuid.uuid4()}/nodes",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 404


    def test_create_node_missing_type(
        self,
        client: TestClient,
        auth_headers: dict,
        created_workflow: dict,
    ):
        """
        Node type is required.
        """

        payload = {
            "name": "Start",
            "position_x": 0,
            "position_y": 0,
        }

        response = client.post(
            f"/api/v1/workflows/{created_workflow['id']}/nodes",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 422