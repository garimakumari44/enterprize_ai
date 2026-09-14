"""
Webhook Node

Executes outbound HTTP webhook requests.

Supported:
- GET
- POST
- PUT
- PATCH
- DELETE

Authentication:
- None
- Bearer Token
- API Key Header

Outputs:
{
    "status_code": 200,
    "headers": {...},
    "body": {...},
    "success": True,
    "elapsed_ms": 124
}
"""

from __future__ import annotations

import json
import time
from typing import Any

import requests

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult


class WebhookNode(BaseNode):
    """
    Sends HTTP webhook requests.
    """

    NODE_TYPE = "webhook"

    DEFAULT_TIMEOUT = 30

    def execute(self, context: NodeContext) -> NodeResult:
        """
        Execute webhook request.
        """

        url = self.get_property("url")
        method = self.get_property("method", "POST").upper()

        headers = self.get_property("headers", {}) or {}

        query_params = self.get_property("query", {}) or {}

        payload = self.get_property("payload")

        timeout = self.get_property(
            "timeout",
            self.DEFAULT_TIMEOUT,
        )

        verify_ssl = self.get_property(
            "verify_ssl",
            True,
        )

        auth_type = self.get_property(
            "auth_type",
            "none",
        )

        token = self.get_property("token")

        api_key_name = self.get_property("api_key_name")
        api_key_value = self.get_property("api_key_value")

        if not url:
            return NodeResult.failure(
                "Webhook URL is required."
            )

        # Authentication

        if auth_type == "bearer" and token:
            headers["Authorization"] = f"Bearer {token}"

        elif (
            auth_type == "api_key"
            and api_key_name
            and api_key_value
        ):
            headers[api_key_name] = api_key_value

        start = time.perf_counter()

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=query_params,
                json=payload,
                timeout=timeout,
                verify=verify_ssl,
            )

            elapsed = int(
                (time.perf_counter() - start) * 1000
            )

            try:
                body: Any = response.json()
            except Exception:
                body = response.text

            return NodeResult.success(
                data={
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": body,
                    "success": response.ok,
                    "elapsed_ms": elapsed,
                }
            )

        except requests.Timeout:
            return NodeResult.failure(
                "Webhook request timed out."
            )

        except requests.RequestException as exc:
            return NodeResult.failure(str(exc))

    # ------------------------------------------------------------------

    @classmethod
    def metadata(cls) -> dict:
        return {
            "type": cls.NODE_TYPE,
            "name": "Webhook",
            "category": "Integration",
            "description": "Send HTTP requests to external services.",
            "icon": "webhook",
            "properties": [
                "url",
                "method",
                "headers",
                "query",
                "payload",
                "timeout",
                "verify_ssl",
                "auth_type",
                "token",
                "api_key_name",
                "api_key_value",
            ],
        }