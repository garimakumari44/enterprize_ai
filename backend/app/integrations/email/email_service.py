"""
Email Service

Business layer for workflow email operations.
"""

from typing import Dict, Any, List, Optional


from .email_client import EmailClient



class EmailService:
    """
    High-level email service.
    """



    def __init__(
        self,
        config: Dict[str, Any]
    ):

        self.default_sender = config.get(
            "sender"
        )


        self.client = EmailClient(
            smtp_host=config["smtp_host"],
            smtp_port=config.get(
                "smtp_port",
                587
            ),
            username=config["username"],
            password=config["password"],
            use_tls=config.get(
                "tls",
                True
            )
        )



    async def validate(self):
        """
        Validate email provider.
        """

        return await self.client.test_connection()



    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        html: Optional[str] = None,
        attachments: Optional[List[str]] = None,
    ):
        """
        Generic email sender.
        """

        return await self.client.send_email(
            sender=self.default_sender,
            recipient=recipient,
            subject=subject,
            body=body,
            html=html,
            attachments=attachments
        )



    async def send_notification(
        self,
        recipient: str,
        title: str,
        message: str,
    ):
        """
        Workflow notification email.
        """


        return await self.send(
            recipient=recipient,
            subject=title,
            body=message
        )



    async def send_workflow_success(
        self,
        recipient: str,
        workflow_name: str,
        result: Any
    ):
        """
        Send successful workflow execution email.
        """


        body = f"""
Workflow Completed Successfully

Workflow:
{workflow_name}


Result:

{result}
"""


        return await self.send(
            recipient,
            f"Workflow Completed: {workflow_name}",
            body
        )



    async def send_workflow_failure(
        self,
        recipient: str,
        workflow_name: str,
        error: str
    ):
        """
        Send workflow failure alert.
        """


        body = f"""
Workflow Failed

Workflow:
{workflow_name}


Error:

{error}
"""


        return await self.send(
            recipient,
            f"Workflow Failed: {workflow_name}",
            body
        )



    async def send_approval_request(
        self,
        recipient: str,
        document_name: str,
        approval_url: str
    ):
        """
        Human-in-the-loop approval request.
        """


        html = f"""
        <h2>Approval Required</h2>

        <p>
        Document:
        {document_name}
        </p>

        <a href="{approval_url}">
        Review Document
        </a>
        """


        return await self.send(
            recipient=recipient,
            subject="Document Approval Required",
            body=html,
            html=html
        )