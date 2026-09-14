from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowMetadata:
    name: str
    description: str = ""
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)


@dataclass
class Workflow:
    workflow_id: str

    metadata: WorkflowMetadata

    dag_id: str

    status: WorkflowStatus = WorkflowStatus.DRAFT

    input_data: Dict = field(default_factory=dict)

    output_data: Dict = field(default_factory=dict)

    context: Dict = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.utcnow)

    started_at: Optional[datetime] = None

    completed_at: Optional[datetime] = None

    owner: Optional[str] = None