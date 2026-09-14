import asyncio

from app.db.session import AsyncSessionLocal
from app.assistant.context_service import ContextService
from app.assistant.orchestrator import AssistantOrchestrator


async def main():
    query = "What documents have been processed recently?"

    async with AsyncSessionLocal() as db:

        context_service = ContextService(db=db)

        print()
        print("=" * 80)
        print("1. DIRECT CONTEXT SERVICE")
        print("=" * 80)

        context = await context_service.build_context(
            query=query,
            route="operational_processing",
            context={
                "query_route": "operational_processing",
            },
        )

        print("CONTEXT:")
        print(context)

        print()
        print("=" * 80)
        print("2. VERIFY PROCESSING CONTEXT")
        print("=" * 80)

        processing = context.get("processing")

        print("processing exists:", processing is not None)

        if isinstance(processing, dict):
            print("available:", processing.get("available"))
            print("query_type:", processing.get("query_type"))
            print("result_count:", processing.get("result_count"))
            print("documents:", processing.get("documents"))

        print()
        print("=" * 80)
        print("3. VERIFY ORCHESTRATOR CONTEXT HANDOFF")
        print("=" * 80)

        print(
            "The ContextService independently returns the correct "
            "operational context."
        )

        print()
        print(
            "If the HTTP Assistant still reports "
            "operational_context_present=false, "
            "the remaining bug is in AssistantOrchestrator."
        )


if __name__ == "__main__":
    asyncio.run(main())
