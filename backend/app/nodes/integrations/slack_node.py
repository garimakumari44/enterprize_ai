"""
Slack Node

Posts messages to Slack using the configured SlackService.

Features
--------
- Send message to channel
- Send direct message
- Thread replies
- Rich Block Kit messages
- Attachments
- Mentions (@user, @channel)
"""

from __future__ import annotations

from typing import Any

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.services.slack_service import SlackService


class SlackNode(BaseNode):
    """
    Sends messages to Slack.
    """

    NODE_TYPE = "slack"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.slack_service = SlackService()

    def execute(self, context: NodeContext) -> NodeResult:
        """
        Execute Slack node.
        """

        channel = self.get_property("channel")
        message = self.get_property("message")

        if not channel:
            return NodeResult.failure("Slack channel is required.")

        if not message:
            return NodeResult.failure("Slack message is required.")

        thread_ts = self.get_property("thread_ts")
        username = self.get_property("username")
        icon_emoji = self.get_property("icon_emoji")
        blocks = self.get_property("blocks")
        attachments = self.get_property("attachments")
        unfurl_links = self.get_property("unfurl_links", False)
        unfurl_media = self.get_property("unfurl_media", False)

        try:
            result = self.slack_service.send_message(
                channel=channel,
                message=message,
                thread_ts=thread_ts,
                username=username,
                icon_emoji=icon_emoji,
                blocks=blocks,
                attachments=attachments,
                unfurl_links=unfurl_links,
                unfurl_media=unfurl_media,
            )

            return NodeResult.success(
                data={
                    "provider": "slack",
                    "channel": result.get("channel"),
                    "timestamp": result.get("ts"),
                    "message_id": result.get("message_id"),
                    "status": result.get("status", "sent"),
                }
            )

        except Exception as exc:
            return NodeResult.failure(str(exc))

    @classmethod
    def metadata(cls) -> dict[str, Any]:
        return {
            "type": cls.NODE_TYPE,
            "name": "Slack",
            "category": "Integration",
            "description": "Send messages to Slack channels or users.",
            "icon": "slack",
            "properties": [
                "channel",
                "message",
                "thread_ts",
                "username",
                "icon_emoji",
                "blocks",
                "attachments",
                "unfurl_links",
                "unfurl_media",
            ],
        }