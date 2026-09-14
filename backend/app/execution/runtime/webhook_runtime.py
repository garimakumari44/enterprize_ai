"""
Webhook Runtime

Sends workflow events to external webhook endpoints.
"""

from __future__ import annotations

from typing import Any

import requests
from requests.exceptions import RequestException

from app.execution.exceptions.execution_exception import ExecutionException
from app.execution.runtime.base_runtime import BaseRuntime


class WebhookRuntime(BaseRuntime):
    """
    Runtime for Webhook nodes.

    Expected config:

    {
        "url": "https://example.com/webhook",
        "method": "POST",
        "headers": {
            "Authorization": "Bearer {{token}}"
        },
        "payload": {
            "workflow": "{{workflow.name}}",
            "status": "completed"
        },
        "timeout": 30
    }
    """

    @property
    def node_type(self) -> str:
        return "webhook"

    def execute(
        self,
        node: Any,
        execution: Any,
    ) -> dict[str, Any]:

        config = self.resolve_config(node.config)

        url = config.get("url")

        if not url:
            raise ExecutionException(
                "Webhook node requires a URL."
            )

        method = config.get("method", "POST").upper()
        headers = config.get("headers", {})
        payload = config.get("payload", {})
        timeout = config.get("timeout", 30)

        self.log(f"Sending webhook to {url}")

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=payload,
                timeout=timeout,
            )

            response.raise_for_status()

        except RequestException as exc:
            raise ExecutionException(
                f"Webhook delivery failed: {exc}"
            ) from exc

        try:
            response_body = response.json()
        except ValueError:
            response_body = response.text

        output = {
            "status": response.status_code,
            "headers": dict(response.headers),
            "body": response_body,
            "delivered": True,
        }

        self.save_output(
            node_id=str(node.id),
            output=output,
        )

        self.log(
            f"Webhook delivered ({response.status_code})"
        )

        return output