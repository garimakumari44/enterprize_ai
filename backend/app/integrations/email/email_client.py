"""
Email Client

Low-level email communication layer.
Supports SMTP based providers.
"""

import aiosmtplib

from email.message import EmailMessage
from typing import List, Optional



class EmailClient:
    """
    SMTP email client wrapper.
    """


    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        use_tls: bool = True,
    ):

        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls



    async def send_email(
        self,
        sender: str,
        recipient: str,
        subject: str,
        body: str,
        html: Optional[str] = None,
        attachments: Optional[List[str]] = None,
    ):
        """
        Send email message.
        """


        message = EmailMessage()

        message["From"] = sender
        message["To"] = recipient
        message["Subject"] = subject


        if html:

            message.set_content(body)

            message.add_alternative(
                html,
                subtype="html"
            )

        else:

            message.set_content(body)



        if attachments:

            for file_path in attachments:

                with open(
                    file_path,
                    "rb"
                ) as file:

                    file_data = file.read()


                filename = file_path.split("/")[-1]


                message.add_attachment(
                    file_data,
                    maintype="application",
                    subtype="octet-stream",
                    filename=filename
                )



        try:

            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
                start_tls=self.use_tls,
            )


            return {
                "success": True,
                "recipient": recipient,
                "subject": subject
            }


        except Exception as e:

            raise Exception(
                f"Email sending failed: {str(e)}"
            )



    async def test_connection(self):
        """
        Verify SMTP credentials.
        """

        try:

            smtp = aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                start_tls=self.use_tls
            )


            await smtp.connect()


            await smtp.login(
                self.username,
                self.password
            )


            await smtp.quit()


            return {
                "success": True,
                "message": "SMTP connection successful"
            }


        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }