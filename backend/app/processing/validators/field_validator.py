from __future__ import annotations

import re
from typing import Any

from .base import BaseValidator


class FieldValidator(BaseValidator):
    """
    Generic field validation.
    """

    def __init__(
        self,
        *,
        required: bool = False,
        min_length: int | None = None,
        max_length: int | None = None,
        regex: str | None = None,
    ) -> None:
        self.required = required
        self.min_length = min_length
        self.max_length = max_length
        self.regex = regex

        self._message = ""

    def validate(self, value: Any) -> bool:
        if value is None:
            if self.required:
                self._message = "Field is required."
                return False
            return True

        value = str(value).strip()

        if self.required and not value:
            self._message = "Field cannot be empty."
            return False

        if self.min_length is not None:
            if len(value) < self.min_length:
                self._message = (
                    f"Minimum length is {self.min_length}."
                )
                return False

        if self.max_length is not None:
            if len(value) > self.max_length:
                self._message = (
                    f"Maximum length is {self.max_length}."
                )
                return False

        if self.regex:
            if not re.fullmatch(self.regex, value):
                self._message = "Invalid format."
                return False

        return True

    def error_message(self) -> str:
        return self._message