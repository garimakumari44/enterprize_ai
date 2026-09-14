"""
Webhook Service

Business layer for workflow webhook operations.
"""


from typing import Dict, Any, Optional


from .webhook_client import WebhookClient



class WebhookService:
    """
    High-level webhook service.
    """



    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None
    ):

        self.config = config or {}

        self.client = WebhookClient(
            timeout=self.config.get(
                "timeout",
                30
            )
        )



    async def send(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Send webhook event.
        """

        return await self.client.post(
            url=url,
            payload=payload,
            headers=headers
        )



    async def trigger_event(
        self,
        event: str,
        data: Dict[str, Any],
    ):
        """
        Trigger external workflow event.
        """


        webhook_url = self.config.get(
            "webhook_url"
        )


        payload = {
            "event": event,
            "data": data
        }


        return await self.send(
            url=webhook_url,
            payload=payload
        )



    async def call_api(
        self,
        method: str,
        url: str,
        payload=None,
        headers=None
    ):
        """
        Generic API caller.
        """

        return await self.client.request(
            method=method,
            url=url,
            payload=payload,
            headers=headers
        )



    async def notify_workflow_completion(
        self,
        url: str,
        workflow_id: str,
        status: str,
        result: Any
    ):
        """
        Send workflow completion callback.
        """


        payload = {
            "workflow_id": workflow_id,
            "status": status,
            "result": result
        }


        return await self.send(
            url=url,
            payload=payload
        )



    async def health_check(
        self,
        url: str
    ):
        """
        Check webhook endpoint availability.
        """

        response = await self.client.get(
            url
        )


        return {
            "available": response["success"],
            "status_code": response.get(
                "status_code"
            )
        }