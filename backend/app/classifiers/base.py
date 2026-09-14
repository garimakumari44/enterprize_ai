"""
Base interfaces for document classification.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseClassifier(ABC):
    """
    Abstract classifier.

    Every classifier in the system should inherit from this class.
    """

    @abstractmethod
    async def classify(self, *args: Any, **kwargs: Any) -> Any:
        """
        Perform classification.

        Returns:
            Classification result.
        """
        raise NotImplementedError