# app/integrations/postgres/postgres_service.py


from typing import Any, Dict, List

from app.integrations.postgres.postgres_client import (
    PostgresClient
)



class PostgresService:
    """
    High-level PostgreSQL service.

    Used by workflow nodes.
    """



    def __init__(
        self,
        database_url: str
    ):

        self.client = PostgresClient(
            database_url
        )



    async def query(
        self,
        sql: str,
        params: tuple = ()
    ) -> Dict[str,Any]:

        """
        Execute SELECT query.
        """

        rows = await self.client.fetch(
            sql,
            params
        )


        return {

            "status": "success",

            "rows": rows,

            "count": len(rows)

        }



    async def query_one(
        self,
        sql: str,
        params: tuple = ()
    ):

        row = await self.client.fetch_one(
            sql,
            params
        )


        return {

            "status":"success",

            "data": row

        }



    async def execute(
        self,
        sql:str,
        params:tuple=()
    ):

        """
        Execute mutation query.
        """

        result = await self.client.execute(
            sql,
            params
        )


        return {

            "status":"success",

            "result":result

        }



    async def insert(
        self,
        table:str,
        data:Dict[str,Any]
    ):

        """
        Generic insert builder.
        """


        columns = ", ".join(
            data.keys()
        )


        values = list(
            data.values()
        )


        placeholders = ", ".join(
            [
                f"${i+1}"
                for i in range(len(values))
            ]
        )


        query = f"""
        INSERT INTO {table}
        ({columns})
        VALUES
        ({placeholders})
        RETURNING *
        """



        result = await self.client.fetch_one(
            query,
            tuple(values)
        )


        return {

            "status":"success",

            "data":result

        }



    async def delete(
        self,
        table:str,
        condition:str,
        params:tuple
    ):


        query = f"""
        DELETE FROM {table}
        WHERE {condition}
        """



        result = await self.client.execute(
            query,
            params
        )


        return {

            "status":"success",

            "result":result

        }