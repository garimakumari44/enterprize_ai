"""
HTTP Runtime

Executes outbound HTTP requests.
"""

from __future__ import annotations

from typing import Any

import requests

from app.execution.runtime.base_runtime import BaseRuntime


class HTTPRuntime(BaseRuntime):
    """
    Runtime for HTTP nodes.

    Expected config:

    {
        "method": "POST",
        "url": "https://api.example.com/users",
        "headers": {},
        "params": {},
        "body": {},
        "timeout": 30
    }
    """

    @property
    def node_type(self) -> str:
        return "http"

    def execute(
        self,
        node: Any,
        execution: Any,
    ) -> dict[str, Any]:

        config = self.resolve_config(node.config)

        method = config.get("method", "GET").upper()
        url = config.get("url")

        if not url:
            raise ValueError("HTTP node requires a URL.")

        headers = config.get("headers", {})
        params = config.get("params", {})
        body = config.get("body")
        timeout = config.get("timeout", 30)

        self.log(f"{method} {url}")

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=body,
            timeout=timeout,
        )

        response.raise_for_status()

        try:
            response_body = response.json()
        except ValueError:
            response_body = response.text

        output = {
            "status": response.status_code,
            "headers": dict(response.headers),
            "body": response_body,
        }

        self.save_output(
            node_id=str(node.id),
            output=output,
        )

        self.log(
            f"HTTP {response.status_code}"
        )

        return output