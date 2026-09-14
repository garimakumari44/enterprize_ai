import asyncio

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.models.workflow import Workflow


async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Workflow))
        workflows = result.scalars().all()

        print(f"COUNT: {len(workflows)}")

        for workflow in workflows:
            print(
                workflow.id,
                workflow.name,
                workflow.workflow_type,
                workflow.is_active,
                workflow.config,
            )


if __name__ == "__main__":
    asyncio.run(main())
