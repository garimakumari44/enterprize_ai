# app/integrations/postgres/postgres_client.py

from typing import Any, Dict, List, Optional

import asyncpg


class PostgresClient:
    """
    PostgreSQL connection client.

    Used by workflow integrations
    to communicate with external databases.
    """


    def __init__(
        self,
        database_url: str
    ):

        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None



    async def connect(self):
        """
        Create connection pool.
        """

        if not self.pool:

            self.pool = await asyncpg.create_pool(
                dsn=self.database_url,
                min_size=1,
                max_size=10
            )



    async def disconnect(self):
        """
        Close database pool.
        """

        if self.pool:

            await self.pool.close()

            self.pool = None



    async def execute(
        self,
        query: str,
        params: tuple = ()
    ) -> str:
        """
        Execute INSERT/UPDATE/DELETE queries.
        """

        if not self.pool:
            await self.connect()


        async with self.pool.acquire() as connection:

            result = await connection.execute(
                query,
                *params
            )

            return result



    async def fetch(
        self,
        query: str,
        params: tuple = ()
    ) -> List[Dict[str,Any]]:
        """
        Execute SELECT queries.
        """

        if not self.pool:
            await self.connect()


        async with self.pool.acquire() as connection:

            rows = await connection.fetch(
                query,
                *params
            )


            return [
                dict(row)
                for row in rows
            ]



    async def fetch_one(
        self,
        query: str,
        params: tuple = ()
    ) -> Optional[Dict[str,Any]]:
        """
        Fetch single row.
        """

        if not self.pool:
            await self.connect()


        async with self.pool.acquire() as connection:


            row = await connection.fetchrow(
                query,
                *params
            )


            if row:

                return dict(row)


            return None