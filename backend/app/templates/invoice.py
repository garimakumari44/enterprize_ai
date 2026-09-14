from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(slots=True)
class InvoiceTemplate:
    """
    Extraction template for invoices.
    """

    document_type: str = "invoice"

    required_fields: List[str] = field(default_factory=lambda: [
        "invoice_number",
        "invoice_date",
        "vendor_name",
        "total_amount",
    ])

    optional_fields: List[str] = field(default_factory=lambda: [
        "purchase_order",
        "currency",
        "tax",
        "subtotal",
        "due_date",
        "payment_terms",
        "vendor_address",
        "customer_name",
    ])

    line_item_fields: List[str] = field(default_factory=lambda: [
        "description",
        "quantity",
        "unit_price",
        "amount",
    ])

    confidence_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "invoice_number": 0.95,
        "vendor_name": 0.90,
        "total_amount": 0.95,
        "invoice_date": 0.90,
    })