from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(slots=True)
class ContractTemplate:
    """
    Contract extraction template.
    """

    document_type: str = "contract"

    required_fields: List[str] = field(default_factory=lambda: [
        "party_a",
        "party_b",
        "effective_date",
    ])

    optional_fields: List[str] = field(default_factory=lambda: [
        "expiration_date",
        "contract_value",
        "governing_law",
        "renewal_clause",
        "termination_clause",
    ])

    confidence_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "party_a": 0.90,
        "party_b": 0.90,
        "effective_date": 0.90,
    })