"""
History filtering models.

These filters are used by the execution history repository
to build dynamic SQL queries.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class HistoryFilter(BaseModel):
    """
    Filter options for execution history.
    """

    workflow_id: Optional[UUID] = None
    execution_id: Optional[UUID] = None
    project_id: Optional[UUID] = None

    status: Optional[str] = None

    started_after: Optional[datetime] = None
    started_before: Optional[datetime] = None

    finished_after: Optional[datetime] = None
    finished_before: Optional[datetime] = None

    page: int = Field(default=1, ge=1)

    page_size: int = Field(
        default=20,
        ge=1,
        le=100
    )

    sort_by: str = "started_at"

    descending: bool = True


class SearchFilter(BaseModel):
    """
    Full-text search filters.
    """

    query: str

    page: int = 1
    page_size: int = 20

    include_logs: bool = True
    include_workflow_name: bool = True