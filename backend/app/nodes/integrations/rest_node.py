"""
REST API Node

A generic REST client node for workflow execution.

Features
--------
- GET, POST, PUT, PATCH, DELETE
- Query parameters
- JSON / Form / Raw body
- Custom headers
- Bearer / Basic / API Key authentication
- Configurable timeout
- Retry support
- SSL verification
- Automatic JSON parsing
"""

from __future__ import annotations

import base64
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult


class RestNode(BaseNode):
    """
    Generic REST API request node.
    """

    NODE_TYPE = "rest"

    DEFAULT_TIMEOUT = 30
    DEFAULT_RETRIES = 3

    def execute(self, context: NodeContext) -> NodeResult:
        url = self.get_property("url")
        method = self.get_property("method", "GET").upper()

        headers = self.get_property("headers", {}) or {}
        params = self.get_property("params", {}) or {}

        json_body = self.get_property("json")
        form_body = self.get_property("form")
        raw_body = self.get_property("body")

        timeout = self.get_property("timeout", self.DEFAULT_TIMEOUT)
        verify_ssl = self.get_property("verify_ssl", True)
        retries = self.get_property("retries", self.DEFAULT_RETRIES)

        auth_type = self.get_property("auth_type", "none")

        if not url:
            return NodeResult.failure("REST endpoint URL is required.")

        self._apply_authentication(headers, auth_type)

        session = self._create_session(retries)

        request_kwargs = {
            "method": method,
            "url": url,
            "headers": headers,
            "params": params,
            "timeout": timeout,
            "verify": verify_ssl,
        }

        if json_body is not None:
            request_kwargs["json"] = json_body

        elif form_body is not None:
            request_kwargs["data"] = form_body

        elif raw_body is not None:
            request_kwargs["data"] = raw_body

        start = time.perf_counter()

        try:
            response = session.request(**request_kwargs)

            elapsed_ms = int((time.perf_counter() - start) * 1000)

            try:
                body: Any = response.json()
            except Exception:
                body = response.text

            return NodeResult.success(
                data={
                    "status_code": response.status_code,
                    "success": response.ok,
                    "headers": dict(response.headers),
                    "body": body,
                    "elapsed_ms": elapsed_ms,
                }
            )

        except requests.Timeout:
            return NodeResult.failure("REST request timed out.")

        except requests.RequestException as exc:
            return NodeResult.failure(str(exc))

    def _create_session(self, retries: int) -> requests.Session:
        session = requests.Session()

        retry = Retry(
            total=retries,
            backoff_factor=1.0,
            status_forcelist=[
                429,
                500,
                502,
                503,
                504,
            ],
            allowed_methods=[
                "GET",
                "POST",
                "PUT",
                "PATCH",
                "DELETE",
            ],
        )

        adapter = HTTPAdapter(max_retries=retry)

        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _apply_authentication(
        self,
        headers: dict,
        auth_type: str,
    ) -> None:
        auth_type = auth_type.lower()

        if auth_type == "bearer":
            token = self.get_property("token")

            if token:
                headers["Authorization"] = f"Bearer {token}"

        elif auth_type == "basic":
            username = self.get_property("username", "")
            password = self.get_property("password", "")

            encoded = base64.b64encode(
                f"{username}:{password}".encode()
            ).decode()

            headers["Authorization"] = f"Basic {encoded}"

        elif auth_type == "api_key":
            key_name = self.get_property("api_key_name")
            key_value = self.get_property("api_key_value")

            if key_name and key_value:
                headers[key_name] = key_value

    @classmethod
    def metadata(cls) -> dict:
        return {
            "type": cls.NODE_TYPE,
            "name": "REST API",
            "category": "Integration",
            "description": "Send REST API requests.",
            "icon": "server",
            "properties": [
                "url",
                "method",
                "headers",
                "params",
                "json",
                "form",
                "body",
                "timeout",
                "verify_ssl",
                "retries",
                "auth_type",
                "token",
                "username",
                "password",
                "api_key_name",
                "api_key_value",
            ],
        }