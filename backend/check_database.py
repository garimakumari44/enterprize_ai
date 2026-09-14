import asyncio
import uuid

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.models.workflow import Workflow


async def main():
    print("=" * 60)
    print("WORKFLOW PERSISTENCE TEST")
    print("=" * 60)

    workflow = Workflow(
        name=f"Persistence Test {uuid.uuid4().hex[:8]}",
        description="Testing workflow database persistence",
        workflow_type="document_processing",
        version=1,
        is_active=True,
        config={
            "nodes": []
        },
    )

    async with AsyncSessionLocal() as db:
        try:
            db.add(workflow)

            print()
            print("BEFORE FLUSH")
            print("Workflow ID:", workflow.id)

            await db.flush()

            print()
            print("AFTER FLUSH")
            print("Workflow ID:", workflow.id)

            await db.commit()

            print()
            print("AFTER COMMIT")
            print("Workflow ID:", workflow.id)

        except Exception as exc:
            await db.rollback()
            print()
            print("ERROR:", repr(exc))
            raise

    # Verify using a completely new database session.
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Workflow).where(
                Workflow.id == workflow.id
            )
        )

        saved = result.scalar_one_or_none()

        print()
        print("NEW SESSION VERIFICATION")

        if saved:
            print("PERSISTED: YES")
            print("ID:", saved.id)
            print("NAME:", saved.name)
        else:
            print("PERSISTED: NO")

    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())