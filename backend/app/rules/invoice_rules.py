from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from .base import BusinessRule, RuleResult


class InvoiceRuleEngine(BusinessRule):
    """
    Business-rule validation for invoice documents.

    Validates core invoice fields:

    - Invoice number
    - Vendor name
    - Total amount

    The rule engine is intentionally independent of the extraction
    implementation. It accepts the normalized extracted data dictionary
    produced by the document-processing pipeline.
    """

    name = "Invoice Rules"

    def evaluate(self, data: dict[str, Any]) -> RuleResult:
        """
        Evaluate invoice business rules.

        Parameters
        ----------
        data:
            Extracted invoice data.

        Returns
        -------
        RuleResult
            Collection of business-rule violations.
        """

        result = RuleResult()

        if not isinstance(data, dict):
            result.add_violation(
                "invoice_data",
                "Invoice data must be a dictionary.",
            )
            return result

        invoice_number = data.get("invoice_number")
        total = data.get("total_amount")
        vendor = data.get("vendor_name")

        self._validate_invoice_number(
            result=result,
            invoice_number=invoice_number,
        )

        self._validate_vendor(
            result=result,
            vendor=vendor,
        )

        self._validate_total(
            result=result,
            total=total,
        )

        return result

    @staticmethod
    def _validate_invoice_number(
        result: RuleResult,
        invoice_number: Any,
    ) -> None:
        """
        Validate that an invoice number exists and is not blank.
        """

        if invoice_number is None:
            result.add_violation(
                "invoice_number",
                "Invoice number is missing.",
                field="invoice_number",
            )
            return

        if isinstance(invoice_number, str):
            if not invoice_number.strip():
                result.add_violation(
                    "invoice_number",
                    "Invoice number is missing.",
                    field="invoice_number",
                )
            return

        if not str(invoice_number).strip():
            result.add_violation(
                "invoice_number",
                "Invoice number is missing.",
                field="invoice_number",
            )

    @staticmethod
    def _validate_vendor(
        result: RuleResult,
        vendor: Any,
    ) -> None:
        """
        Validate that a vendor name exists and is not blank.
        """

        if vendor is None:
            result.add_violation(
                "vendor",
                "Vendor name is required.",
                field="vendor_name",
            )
            return

        if isinstance(vendor, str) and not vendor.strip():
            result.add_violation(
                "vendor",
                "Vendor name is required.",
                field="vendor_name",
            )
            return

        if not str(vendor).strip():
            result.add_violation(
                "vendor",
                "Vendor name is required.",
                field="vendor_name",
            )

    @staticmethod
    def _validate_total(
        result: RuleResult,
        total: Any,
    ) -> None:
        """
        Validate the invoice total.

        Supported numeric representations include:

        - int
        - float
        - Decimal
        - numeric strings such as "1250.50"

        Invalid, non-numeric, NaN, infinite, missing, and non-positive
        amounts are reported as rule violations.
        """

        if total is None:
            result.add_violation(
                "amount",
                "Invoice amount missing.",
                field="total_amount",
            )
            return

        try:
            amount = Decimal(str(total).strip())
        except (InvalidOperation, ValueError, TypeError):
            result.add_violation(
                "amount",
                "Invoice amount must be a valid number.",
                field="total_amount",
            )
            return

        if not amount.is_finite():
            result.add_violation(
                "amount",
                "Invoice amount must be a finite number.",
                field="total_amount",
            )
            return

        if amount <= Decimal("0"):
            result.add_violation(
                "amount",
                "Invoice amount must be greater than zero.",
                field="total_amount",
            )