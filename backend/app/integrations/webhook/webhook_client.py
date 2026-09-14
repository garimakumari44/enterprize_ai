"""
Webhook Client

Low-level HTTP communication layer.
"""

from typing import Dict, Any, Optional

import httpx



class WebhookClient:
    """
    Async HTTP client for webhook calls.
    """


    def __init__(
        self,
        timeout: int = 30
    ):

        self.timeout = timeout



    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        """
        Execute HTTP request.
        """


        async with httpx.AsyncClient(
            timeout=self.timeout
        ) as client:


            try:

                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=payload,
                    params=params
                )


                return {
                    "success": True,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "data": self._parse_response(
                        response
                    )
                }


            except httpx.TimeoutException:

                raise Exception(
                    "Webhook request timeout"
                )


            except httpx.HTTPError as e:

                raise Exception(
                    f"Webhook HTTP error: {str(e)}"
                )



    def _parse_response(
        self,
        response
    ):
        """
        Parse response safely.
        """

        try:

            return response.json()

        except Exception:

            return response.text



    async def get(
        self,
        url: str,
        headers=None,
        params=None
    ):

        return await self.request(
            method="GET",
            url=url,
            headers=headers,
            params=params
        )



    async def post(
        self,
        url: str,
        payload=None,
        headers=None
    ):

        return await self.request(
            method="POST",
            url=url,
            headers=headers,
            payload=payload
        )



    async def put(
        self,
        url: str,
        payload=None,
        headers=None
    ):

        return await self.request(
            method="PUT",
            url=url,
            headers=headers,
            payload=payload
        )



    async def patch(
        self,
        url: str,
        payload=None,
        headers=None
    ):

        return await self.request(
            method="PATCH",
            url=url,
            headers=headers,
            payload=payload
        )



    async def delete(
        self,
        url: str,
        headers=None
    ):

        return await self.request(
            method="DELETE",
            url=url,
            headers=headers
        )