"""
Slack Client

Low-level wrapper around Slack API.

Responsibilities:
- Initialize Slack connection
- Send API requests
- Handle Slack errors
"""

from typing import Dict, Any, Optional

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError



class SlackClient:
    """
    Slack API client wrapper.
    """


    def __init__(
        self,
        token: str
    ):
        self.token = token

        self.client = AsyncWebClient(
            token=self.token
        )



    async def test_connection(self) -> Dict[str, Any]:
        """
        Verify Slack authentication.
        """

        try:

            response = await self.client.auth_test()

            return {
                "success": True,
                "team": response.get("team"),
                "user": response.get("user")
            }


        except SlackApiError as e:

            return {
                "success": False,
                "error": e.response["error"]
            }



    async def send_message(
        self,
        channel: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send message to Slack channel.
        """

        try:

            response = await self.client.chat_postMessage(
                channel=channel,
                text=message
            )


            return {
                "success": True,
                "channel": response["channel"],
                "timestamp": response["ts"]
            }


        except SlackApiError as e:

            raise Exception(
                f"Slack error: {e.response['error']}"
            )



    async def send_blocks(
        self,
        channel: str,
        blocks: list
    ) -> Dict[str, Any]:
        """
        Send Slack Block Kit message.
        """

        try:

            response = await self.client.chat_postMessage(
                channel=channel,
                blocks=blocks
            )


            return {
                "success": True,
                "timestamp": response["ts"]
            }


        except SlackApiError as e:

            raise Exception(
                f"Slack error: {e.response['error']}"
            )



    async def get_channels(self):

        """
        Fetch available Slack channels.
        """

        try:

            response = await self.client.conversations_list()


            return response["channels"]


        except SlackApiError as e:

            raise Exception(
                f"Slack error: {e.response['error']}"
            )



    async def get_users(self):

        """
        Fetch Slack users.
        """

        try:

            response = await self.client.users_list()

            return response["members"]


        except SlackApiError as e:

            raise Exception(
                f"Slack error: {e.response['error']}"
            )