# app/integrations/rest/http_client.py

from typing import Dict, Any, Optional

import httpx

from app.core.config import settings


class HTTPClient:
    """
    Generic HTTP client wrapper.

    Used by REST integrations to communicate
    with external APIs.
    """

    def __init__(
        self,
        timeout: int = 30
    ):
        self.timeout = timeout

        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True
        )


    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Execute HTTP request.
        """

        try:

            response = await self.client.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=json,
                data=data
            )


            return {
                "success": True,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "data": self._parse_response(response)
            }


        except httpx.TimeoutException as e:

            return {
                "success": False,
                "error": "Request timeout",
                "details": str(e)
            }


        except httpx.RequestError as e:

            return {
                "success": False,
                "error": "HTTP request failed",
                "details": str(e)
            }



    def _parse_response(
        self,
        response: httpx.Response
    ):

        """
        Normalize API responses.
        """

        content_type = response.headers.get(
            "content-type",
            ""
        )


        if "application/json" in content_type:

            try:
                return response.json()

            except Exception:
                return response.text


        return response.text



    async def close(self):

        await self.client.aclose()