from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


class PricingCalculator:
    """
    Central pricing calculator for the Costs module.

    Supports:
    - LLM token pricing
    - Workflow execution pricing
    - Storage pricing
    - Generic unit pricing
    """

    PRECISION = Decimal("0.000001")

    @classmethod
    def _round(cls, value: Decimal) -> Decimal:
        return value.quantize(cls.PRECISION, rounding=ROUND_HALF_UP)

    # ------------------------------------------------------------------
    # Token Pricing
    # ------------------------------------------------------------------

    @classmethod
    def token_cost(
        cls,
        prompt_tokens: int,
        completion_tokens: int,
        input_price_per_1k: Decimal,
        output_price_per_1k: Decimal,
    ) -> Decimal:
        """
        Calculate LLM token cost.

        Formula:
            (prompt_tokens / 1000) * input_price
          + (completion_tokens / 1000) * output_price
        """

        prompt_cost = (
            Decimal(prompt_tokens) / Decimal("1000")
        ) * input_price_per_1k

        completion_cost = (
            Decimal(completion_tokens) / Decimal("1000")
        ) * output_price_per_1k

        return cls._round(prompt_cost + completion_cost)

    # ------------------------------------------------------------------
    # Execution Pricing
    # ------------------------------------------------------------------

    @classmethod
    def execution_cost(
        cls,
        duration_seconds: float,
        hourly_rate: Decimal,
    ) -> Decimal:
        """
        Formula:

            (duration_seconds / 3600) * hourly_rate
        """

        hours = Decimal(str(duration_seconds)) / Decimal("3600")

        return cls._round(hours * hourly_rate)

    # ------------------------------------------------------------------
    # Storage Pricing
    # ------------------------------------------------------------------

    @classmethod
    def storage_cost(
        cls,
        storage_gb: Decimal,
        price_per_gb: Decimal,
    ) -> Decimal:
        """
        Formula:

            storage_gb * price_per_gb
        """

        return cls._round(storage_gb * price_per_gb)

    # ------------------------------------------------------------------
    # Generic Pricing
    # ------------------------------------------------------------------

    @classmethod
    def unit_cost(
        cls,
        quantity: Decimal,
        unit_price: Decimal,
    ) -> Decimal:
        """
        Generic pricing.

        Formula:

            quantity × unit_price
        """

        return cls._round(quantity * unit_price)

    # ------------------------------------------------------------------
    # Aggregate Costs
    # ------------------------------------------------------------------

    @classmethod
    def total_cost(cls, *costs: Decimal) -> Decimal:
        """
        Sum multiple cost values.

        Example:
            token + execution + storage
        """

        total = sum(costs, Decimal("0"))

        return cls._round(total)