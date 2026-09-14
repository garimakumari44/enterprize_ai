import asyncio

from sqlalchemy import select, func

from app.db.session import AsyncSessionLocal
from app.db.models.processing_job import ProcessingJob


async def main():
    async with AsyncSessionLocal() as db:
        total_result = await db.execute(
            select(func.count()).select_from(ProcessingJob)
        )

        total = total_result.scalar_one()

        print()
        print("=" * 80)
        print("TOTAL PROCESSING JOBS:", total)
        print("=" * 80)

        result = await db.execute(
            select(ProcessingJob)
            .order_by(
                ProcessingJob.created_at.desc()
            )
            .limit(20)
        )

        jobs = result.scalars().all()

        print("RECENT JOBS:", len(jobs))
        print()

        for job in jobs:
            print(
                "ID=", job.id,
                "STATUS=", repr(job.status),
                "CREATED=", job.created_at,
                "STARTED=", job.started_at,
                "COMPLETED=", job.completed_at,
                "VERSION=", job.document_version_id,
            )

        print()
        print("=" * 80)
        print("COMPLETED JOBS")
        print("=" * 80)

        completed_result = await db.execute(
            select(ProcessingJob)
            .where(
                ProcessingJob.status == "completed",
                ProcessingJob.completed_at.is_not(None),
            )
            .order_by(
                ProcessingJob.completed_at.desc(),
                ProcessingJob.created_at.desc(),
            )
            .limit(5)
        )

        completed_jobs = completed_result.scalars().all()

        print(
            "MATCHING COMPLETED JOBS:",
            len(completed_jobs),
        )
        print()

        for job in completed_jobs:
            print(
                "ID=", job.id,
                "STATUS=", repr(job.status),
                "COMPLETED=", job.completed_at,
                "VERSION=", job.document_version_id,
            )


if __name__ == "__main__":
    asyncio.run(main())
