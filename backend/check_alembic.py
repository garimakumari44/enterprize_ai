import asyncio

from sqlalchemy import text

from app.db.session import AsyncSessionLocal


async def main():
    async with AsyncSessionLocal() as session:

        print("\n=== DATABASE CHECK ===")

        result = await session.execute(
            text("SELECT current_database(), current_user")
        )

        print("Database:", result.fetchone())

        # ----------------------------------------------------------
        # ALEMBIC VERSION
        # ----------------------------------------------------------

        print("\n=== ALEMBIC VERSION ===")

        result = await session.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'alembic_version'
                )
            """)
        )

        alembic_exists = result.scalar()

        if not alembic_exists:
            print("alembic_version table DOES NOT EXIST")
        else:
            result = await session.execute(
                text("""
                    SELECT version_num
                    FROM alembic_version
                """)
            )

            rows = result.fetchall()

            if rows:
                for row in rows:
                    print("Current revision:", row[0])
            else:
                print("alembic_version is EMPTY")

        # ----------------------------------------------------------
        # TABLES
        # ----------------------------------------------------------

        print("\n=== TABLES ===")

        result = await session.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
        )

        tables = result.fetchall()

        if tables:
            for row in tables:
                print(row[0])
        else:
            print("NO PUBLIC TABLES FOUND")

        # ----------------------------------------------------------
        # DOCUMENT CHUNKS
        # ----------------------------------------------------------

        print("\n=== DOCUMENT CHUNKS ===")

        result = await session.execute(
            text("""
                SELECT
                    column_name,
                    data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'document_chunks'
                ORDER BY ordinal_position
            """)
        )

        rows = result.fetchall()

        if rows:
            print("document_chunks EXISTS")

            for row in rows:
                print(f"{row[0]} -> {row[1]}")
        else:
            print("document_chunks DOES NOT EXIST")

        # ----------------------------------------------------------
        # PGVECTOR
        # ----------------------------------------------------------

        print("\n=== PGVECTOR EXTENSION ===")

        result = await session.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM pg_extension
                    WHERE extname = 'vector'
                )
            """)
        )

        vector_exists = result.scalar()

        if vector_exists:
            print("pgvector extension EXISTS")
        else:
            print("pgvector extension DOES NOT EXIST")

        # ----------------------------------------------------------
        # DOCUMENT CHUNK VECTORS
        # ----------------------------------------------------------

        print("\n=== DOCUMENT CHUNK VECTORS ===")

        result = await session.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'document_chunk_vectors'
                )
            """)
        )

        vector_table_exists = result.scalar()

        if vector_table_exists:
            print("document_chunk_vectors EXISTS")
        else:
            print("document_chunk_vectors DOES NOT EXIST")


if __name__ == "__main__":
    asyncio.run(main())