"""
Processing Utilities

Shared helper functions for document processing pipeline.

Used by:
- OCR
- Classification
- Extraction
- Validation
- Confidence Engine
- Review Workflow
- Processing Workers
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4
import hashlib
import json
import time
from pathlib import Path


# =====================================================
# Processing ID Generator
# =====================================================

def generate_processing_id() -> str:
    """
    Generate unique processing execution id.
    """

    return str(uuid4())


# =====================================================
# Timestamp Utilities
# =====================================================

def utc_now() -> datetime:
    """
    Get current UTC timestamp.
    """

    return datetime.now(timezone.utc)



# =====================================================
# File Utilities
# =====================================================

def calculate_file_hash(
    file_path: str,
    algorithm: str = "sha256"
) -> str:
    """
    Generate file checksum.

    Used for:
    - duplicate detection
    - document versioning
    - integrity validation
    """

    hash_function = hashlib.new(algorithm)

    with open(file_path, "rb") as file:

        for chunk in iter(
            lambda: file.read(4096),
            b""
        ):
            hash_function.update(chunk)

    return hash_function.hexdigest()



def get_file_extension(
    filename: str
) -> str:
    """
    Extract file extension.
    """

    return Path(filename).suffix.lower()



def validate_file_type(
    filename: str,
    allowed_extensions: list[str]
) -> bool:
    """
    Validate uploaded document type.
    """

    extension = get_file_extension(filename)

    return extension in allowed_extensions



# =====================================================
# Processing Context
# =====================================================

def create_processing_context(
    document_id: str,
    user_id: Optional[str] = None,
    workflow_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create runtime context shared across pipeline stages.

    Example:

    OCR
      |
      v
    Extraction
      |
      v
    Validation

    All stages receive same context.
    """

    return {

        "processing_id": generate_processing_id(),

        "document_id": document_id,

        "user_id": user_id,

        "workflow_id": workflow_id,

        "started_at": utc_now(),

        "metadata": {}

    }



# =====================================================
# Processing Metadata
# =====================================================

def add_processing_metadata(
    context: Dict[str, Any],
    key: str,
    value: Any
):
    """
    Add metadata during processing.
    """

    if "metadata" not in context:
        context["metadata"] = {}

    context["metadata"][key] = value



# =====================================================
# Execution Timer
# =====================================================

class ProcessingTimer:
    """
    Measure processing stage execution time.

    Example:

    OCR took 4.2 seconds
    Extraction took 7 seconds

    """

    def __init__(self):

        self.start_time = None

        self.end_time = None



    def start(self):

        self.start_time = time.time()



    def stop(self):

        self.end_time = time.time()



    def duration(self) -> float:

        if not self.start_time:
            return 0

        end = (
            self.end_time
            if self.end_time
            else time.time()
        )

        return round(
            end - self.start_time,
            4
        )



# =====================================================
# JSON Utilities
# =====================================================

def serialize_processing_result(
    data: Dict[str, Any]
) -> str:
    """
    Convert processing output to JSON.

    Used before:
    - storing results
    - sending events
    - logging
    """

    return json.dumps(
        data,
        default=str,
        indent=2
    )



def safe_json_load(
    value: str
) -> Dict[str, Any]:
    """
    Safely parse JSON.
    """

    try:

        return json.loads(value)

    except Exception:

        return {}



# =====================================================
# Status Helpers
# =====================================================

PROCESSING_STATES = {

    "PENDING",
    "PROCESSING",
    "COMPLETED",
    "FAILED",
    "REVIEW_REQUIRED"

}



def is_valid_processing_state(
    state: str
) -> bool:
    """
    Validate processing state.
    """

    return state.upper() in PROCESSING_STATES



def calculate_progress(
    current_stage: int,
    total_stages: int
) -> float:
    """
    Calculate pipeline progress.

    Example:

    OCR
    Classification
    Extraction
    Validation

    2/4 = 50%
    """

    if total_stages == 0:
        return 0

    return round(
        (current_stage / total_stages) * 100,
        2
    )