"""
Email Node

Sends an email using the configured EmailService.

Features
--------
- Plain text or HTML
- Multiple recipients
- CC / BCC
- Reply-To
- Attachments
- Provider agnostic
"""

from __future__ import annotations

from typing import Any

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.services.email_service import EmailService


class EmailNode(BaseNode):
    """
    Send an email.
    """

    NODE_TYPE = "email"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.email_service = EmailService()

    def execute(self, context: NodeContext) -> NodeResult:
        """
        Execute email node.
        """

        to = self.get_property("to")
        subject = self.get_property("subject")

        if not to:
            return NodeResult.failure("Email recipient is required.")

        if not subject:
            return NodeResult.failure("Email subject is required.")

        body = self.get_property("body", "")

        html = self.get_property("html")

        cc = self.get_property("cc", [])

        bcc = self.get_property("bcc", [])

        reply_to = self.get_property("reply_to")

        attachments = self.get_property("attachments", [])

        try:
            result = self.email_service.send_email(
                to=to,
                subject=subject,
                body=body,
                html=html,
                cc=cc,
                bcc=bcc,
                reply_to=reply_to,
                attachments=attachments,
            )

            return NodeResult.success(
                data={
                    "provider": result.get("provider"),
                    "message_id": result.get("message_id"),
                    "status": result.get("status"),
                }
            )

        except Exception as exc:
            return NodeResult.failure(str(exc))

    @classmethod
    def metadata(cls) -> dict[str, Any]:
        return {
            "type": cls.NODE_TYPE,
            "name": "Email",
            "category": "Integration",
            "description": "Send emails through the configured email provider.",
            "icon": "mail",
            "properties": [
                "to",
                "subject",
                "body",
                "html",
                "cc",
                "bcc",
                "reply_to",
                "attachments",
            ],
        }