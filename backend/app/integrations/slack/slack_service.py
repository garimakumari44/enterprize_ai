"""
Slack Service

Business layer for Slack integration.

Used by:
- Workflow Nodes
- AI Agents
- Automation Engine
"""


from typing import Dict, Any


from .slack_client import SlackClient



class SlackService:
    """
    High-level Slack operations.
    """



    def __init__(
        self,
        token: str
    ):

        self.client = SlackClient(
            token
        )



    async def validate(
        self
    ) -> Dict[str, Any]:
        """
        Validate Slack credentials.
        """

        return await self.client.test_connection()



    async def notify(
        self,
        channel: str,
        message: str
    ):
        """
        Send workflow notification.
        """

        return await self.client.send_message(
            channel=channel,
            message=message
        )



    async def send_workflow_result(
        self,
        channel: str,
        workflow_name: str,
        status: str,
        output: Any
    ):
        """
        Send formatted workflow execution result.
        """

        message = f"""
Workflow Completed

Name:
{workflow_name}

Status:
{status}

Output:
{output}
"""


        return await self.client.send_message(
            channel,
            message
        )



    async def send_alert(
        self,
        channel: str,
        error: str
    ):
        """
        Send workflow failure alert.
        """

        message = f"""
🚨 Workflow Failed

Error:

{error}
"""


        return await self.client.send_message(
            channel,
            message
        )



    async def list_channels(self):

        return await self.client.get_channels()



    async def list_users(self):

        return await self.client.get_users()