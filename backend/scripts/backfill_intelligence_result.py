from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import UUID


# ============================================================
# Make backend/ available on Python's import path
# ============================================================

BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


# ============================================================
# Application imports
# ============================================================

from app.db.session import AsyncSessionLocal
from app.processing.job_runner import (
    ProcessingJobRunner,
)


# ============================================================
# Job to backfill
# ============================================================

JOB_ID = UUID(
    "e8c24a9d-b9c8-4cfc-a4cd-2f9d6bd70a06"
)


# ============================================================
# Main
# ============================================================

async def main() -> None:
    print("=" * 70)
    print("Document Intelligence Result Backfill")
    print("=" * 70)
    print(f"Processing Job ID: {JOB_ID}")
    print()

    async with AsyncSessionLocal() as db:
        runner = ProcessingJobRunner(db)

        print("Checking processing job...")

        result = await runner.ensure_intelligence_result(
            JOB_ID
        )

        if result is None:
            print()
            print("ERROR")
            print("-" * 70)
            print(
                "No DocumentIntelligenceResult was created."
            )
            print(
                "The processing job may not be completed, "
                "or its legacy result may be missing."
            )
            return

        print()
        print("SUCCESS")
        print("-" * 70)
        print(f"Result ID:                 {result.id}")
        print(f"Processing ID:             {result.processing_id}")
        print(f"Document ID:               {result.document_id}")
        print(
            f"Document Version ID:      "
            f"{result.document_version_id}"
        )
        print(f"Document Type:             {result.document_type}")
        print(
            f"Classification Confidence: "
            f"{result.classification_confidence}"
        )
        print("-" * 70)


if __name__ == "__main__":
    asyncio.run(main())