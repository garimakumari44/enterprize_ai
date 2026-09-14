"""
Job serializer.

Converts execution jobs between
Python dictionaries and JSON payloads.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


class JobSerializer:
    """
    Handles workflow execution job serialization.
    """


    VERSION = "1.0"


    def serialize(
        self,
        job: dict[str, Any],
    ) -> str:
        """
        Convert job dictionary into JSON payload.

        Args:
            job:
                Execution job data.

        Returns:
            JSON string.
        """

        payload = {
            "version": self.VERSION,
            "created_at": self._timestamp(),
            "job": job,
        }


        return json.dumps(
            payload,
            default=str,
        )


    def deserialize(
        self,
        payload: str,
    ) -> dict[str, Any]:
        """
        Convert JSON payload back into job data.
        """

        data = json.loads(payload)


        self._validate(data)


        return data["job"]



    def _validate(
        self,
        payload: dict[str, Any],
    ) -> None:
        """
        Validate serialized job structure.
        """

        required_fields = [
            "version",
            "created_at",
            "job",
        ]


        for field in required_fields:

            if field not in payload:
                raise ValueError(
                    f"Invalid job payload. Missing: {field}"
                )



    def _timestamp(self) -> str:
        """
        Generate UTC timestamp.
        """

        return datetime.now(
            timezone.utc
        ).isoformat()