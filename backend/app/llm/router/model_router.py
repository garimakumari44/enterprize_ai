"""
app/llm/router/model_router.py

Deterministic model selection and fallback ordering.
"""

from __future__ import annotations


class ModelRouter:
    """
    Selects the primary model and fallback models.

    It does not call providers.
    """

    def __init__(
        self,
        *,
        default_model: str,
        fallback_models: list[str] | None = None,
    ) -> None:
        if not default_model:
            raise ValueError(
                "default_model is required."
            )

        self.default_model = (
            str(default_model).strip()
        )

        self.fallback_models = self._normalize(
            fallback_models or []
        )

    # ========================================================================
    # MODEL SELECTION
    # ========================================================================

    def select_model(
        self,
        requested_model: str | None = None,
    ) -> str:
        """
        Select requested model or default model.
        """

        if requested_model:
            requested = str(
                requested_model
            ).strip()

            if requested:
                return requested

        return self.default_model

    # ========================================================================
    # FALLBACKS
    # ========================================================================

    def get_fallback_models(
        self,
        failed_model: str | None = None,
    ) -> list[str]:
        """
        Return fallback models excluding the failed model.
        """

        failed = (
            str(failed_model).strip()
            if failed_model
            else None
        )

        return [
            model
            for model in self.fallback_models
            if model != failed
        ]

    # ========================================================================
    # SEQUENCE
    # ========================================================================

    def get_model_sequence(
        self,
        requested_model: str | None = None,
    ) -> list[str]:
        """
        Return primary + fallback models without duplicates.
        """

        primary = self.select_model(
            requested_model
        )

        sequence = [
            primary,
            *self.get_fallback_models(
                primary
            ),
        ]

        result: list[str] = []

        for model in sequence:
            if (
                model
                and model not in result
            ):
                result.append(
                    model
                )

        return result

    # ========================================================================
    # NORMALIZATION
    # ========================================================================

    @staticmethod
    def _normalize(
        models: list[str],
    ) -> list[str]:
        result: list[str] = []

        for model in models:
            normalized = str(
                model
            ).strip()

            if (
                normalized
                and normalized not in result
            ):
                result.append(
                    normalized
                )

        return result


__all__ = [
    "ModelRouter",
]