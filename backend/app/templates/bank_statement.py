from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(slots=True)
class BankStatementTemplate:
    """
    Bank statement extraction template.
    """

    document_type: str = "bank_statement"

    required_fields: List[str] = field(default_factory=lambda: [
        "account_number",
        "account_holder",
        "statement_period",
    ])

    optional_fields: List[str] = field(default_factory=lambda: [
        "bank_name",
        "opening_balance",
        "closing_balance",
        "currency",
    ])

    transaction_fields: List[str] = field(default_factory=lambda: [
        "date",
        "description",
        "debit",
        "credit",
        "balance",
    ])

    confidence_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "account_number": 0.95,
        "account_holder": 0.90,
        "statement_period": 0.90,
    })