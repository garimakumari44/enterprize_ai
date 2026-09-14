from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseValidator(ABC):
    """
    Base interface for all validators.
    """

    @abstractmethod
    def validate(self, value: Any) -> bool:
        """
        Validate a value.

        Returns
        -------
        bool
            True if valid.
        """
        raise NotImplementedError

    @abstractmethod
    def error_message(self) -> str:
        """
        Validation failure message.
        """
        raise NotImplementedError