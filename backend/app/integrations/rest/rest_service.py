# app/integrations/rest/rest_service.py


from typing import Dict, Any, Optional

from app.integrations.rest.http_client import HTTPClient



class RESTService:
    """
    High level REST API service.

    Used by workflow nodes.
    """


    def __init__(self):

        self.client = HTTPClient()



    async def execute(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str,str]] = None,
        params: Optional[Dict[str,Any]] = None,
        body: Optional[Dict[str,Any]] = None
    ) -> Dict[str,Any]:


        response = await self.client.request(

            method=method,

            url=url,

            headers=headers,

            params=params,

            json=body
        )


        return self._format_response(response)



    def _format_response(
        self,
        response: Dict[str,Any]
    ):

        """
        Convert external API response
        into workflow output format.
        """


        if not response.get("success"):

            return {

                "status": "failed",

                "error": response.get(
                    "error"
                ),

                "details": response.get(
                    "details"
                )

            }



        return {

            "status": "success",

            "status_code": response.get(
                "status_code"
            ),

            "result": response.get(
                "data"
            )

        }



    async def get(
        self,
        url: str,
        headers=None,
        params=None
    ):

        return await self.execute(

            method="GET",

            url=url,

            headers=headers,

            params=params
        )



    async def post(
        self,
        url:str,
        body:Dict[str,Any],
        headers=None
    ):


        return await self.execute(

            method="POST",

            url=url,

            headers=headers,

            body=body
        )



    async def put(
        self,
        url:str,
        body:Dict[str,Any],
        headers=None
    ):


        return await self.execute(

            method="PUT",

            url=url,

            headers=headers,

            body=body
        )



    async def delete(
        self,
        url:str,
        headers=None
    ):


        return await self.execute(

            method="DELETE",

            url=url,

            headers=headers

        )