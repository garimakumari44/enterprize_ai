from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(slots=True)
class ReceiptTemplate:
    """
    Receipt extraction template.
    """

    document_type: str = "receipt"

    required_fields: List[str] = field(default_factory=lambda: [
        "merchant_name",
        "transaction_date",
        "total_amount",
    ])

    optional_fields: List[str] = field(default_factory=lambda: [
        "tax",
        "subtotal",
        "payment_method",
        "currency",
        "receipt_number",
    ])

    confidence_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "merchant_name": 0.90,
        "transaction_date": 0.90,
        "total_amount": 0.95,
    })