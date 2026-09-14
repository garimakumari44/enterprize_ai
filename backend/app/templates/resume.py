from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(slots=True)
class ResumeTemplate:
    """
    Resume extraction template.
    """

    document_type: str = "resume"

    required_fields: List[str] = field(default_factory=lambda: [
        "candidate_name",
        "email",
    ])

    optional_fields: List[str] = field(default_factory=lambda: [
        "phone",
        "skills",
        "education",
        "experience",
        "certifications",
        "linkedin",
        "github",
    ])

    confidence_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "candidate_name": 0.90,
        "email": 0.95,
    })