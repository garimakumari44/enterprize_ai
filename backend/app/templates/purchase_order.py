from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(slots=True)
class PurchaseOrderTemplate:
    """
    Purchase Order extraction template.
    """

    document_type: str = "purchase_order"

    required_fields: List[str] = field(default_factory=lambda: [
        "po_number",
        "supplier",
        "order_date",
    ])

    optional_fields: List[str] = field(default_factory=lambda: [
        "delivery_date",
        "buyer",
        "currency",
        "total_amount",
    ])

    line_item_fields: List[str] = field(default_factory=lambda: [
        "item",
        "quantity",
        "unit_price",
        "amount",
    ])

    confidence_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "po_number": 0.95,
        "supplier": 0.90,
        "order_date": 0.90,
    })