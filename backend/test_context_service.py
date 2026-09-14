import asyncio

from app.db.session import AsyncSessionLocal
from app.assistant.context_service import ContextService


async def main():
    query = "What documents have been processed recently?"

    async with AsyncSessionLocal() as db:
        service = ContextService(db=db)

        print()
        print("=" * 80)
        print("TESTING CONTEXT SERVICE")
        print("=" * 80)
        print("QUERY:", query)
        print()

        route = "operational_processing"

        result = await service.build_context(
            query=query,
            route=route,
            context={
                "query_route": route,
            },
        )

        print("FULL CONTEXT:")
        print(result)

        print()
        print("=" * 80)
        print("PROCESSING CONTEXT")
        print("=" * 80)

        processing = result.get("processing")

        print("PROCESSING:", processing)

        print()
        print("AVAILABLE:")
        print(
            processing.get("available")
            if isinstance(processing, dict)
            else None
        )

        print()
        print("QUERY TYPE:")
        print(
            processing.get("query_type")
            if isinstance(processing, dict)
            else None
        )

        print()
        print("DOCUMENT COUNT:")
        print(
            len(processing.get("documents", []))
            if isinstance(processing, dict)
            else 0
        )

        print()
        print("DOCUMENTS:")

        if isinstance(processing, dict):
            for document in processing.get("documents", []):
                print(document)


if __name__ == "__main__":
    asyncio.run(main())
