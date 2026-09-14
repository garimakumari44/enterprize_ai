"""
app/nodes/metadata/node_categories.py

Defines all available workflow node categories.

These categories are used by:
- Node Registry
- Workflow Builder
- React Flow UI
- Node Search
- Validation
- Analytics
"""

from enum import Enum


class NodeCategory(str, Enum):
    """Available workflow node categories."""

    TRIGGER = "trigger"
    AI = "ai"
    LOGIC = "logic"
    DATA = "data"
    INPUT = "input"
    OUTPUT = "output"
    FILE = "file"
    API = "api"
    DATABASE = "database"
    MEMORY = "memory"
    VECTOR = "vector"
    EMBEDDING = "embedding"
    OCR = "ocr"
    VISION = "vision"
    DOCUMENT = "document"
    COMMUNICATION = "communication"
    AUTOMATION = "automation"
    SCHEDULER = "scheduler"
    HUMAN = "human"
    UTILITY = "utility"
    SECURITY = "security"
    CUSTOM = "custom"


CATEGORY_LABELS = {
    NodeCategory.TRIGGER: "Trigger",
    NodeCategory.AI: "AI",
    NodeCategory.LOGIC: "Logic",
    NodeCategory.DATA: "Data",
    NodeCategory.INPUT: "Input",
    NodeCategory.OUTPUT: "Output",
    NodeCategory.FILE: "File",
    NodeCategory.API: "API",
    NodeCategory.DATABASE: "Database",
    NodeCategory.MEMORY: "Memory",
    NodeCategory.VECTOR: "Vector Store",
    NodeCategory.EMBEDDING: "Embedding",
    NodeCategory.OCR: "OCR",
    NodeCategory.VISION: "Vision",
    NodeCategory.DOCUMENT: "Document",
    NodeCategory.COMMUNICATION: "Communication",
    NodeCategory.AUTOMATION: "Automation",
    NodeCategory.SCHEDULER: "Scheduler",
    NodeCategory.HUMAN: "Human Review",
    NodeCategory.UTILITY: "Utility",
    NodeCategory.SECURITY: "Security",
    NodeCategory.CUSTOM: "Custom",
}


CATEGORY_ICONS = {
    NodeCategory.TRIGGER: "Play",
    NodeCategory.AI: "Sparkles",
    NodeCategory.LOGIC: "GitBranch",
    NodeCategory.DATA: "Database",
    NodeCategory.INPUT: "ArrowDown",
    NodeCategory.OUTPUT: "ArrowUp",
    NodeCategory.FILE: "File",
    NodeCategory.API: "Globe",
    NodeCategory.DATABASE: "Database",
    NodeCategory.MEMORY: "Brain",
    NodeCategory.VECTOR: "Blocks",
    NodeCategory.EMBEDDING: "Fingerprint",
    NodeCategory.OCR: "ScanText",
    NodeCategory.VISION: "Eye",
    NodeCategory.DOCUMENT: "FileText",
    NodeCategory.COMMUNICATION: "MessageSquare",
    NodeCategory.AUTOMATION: "Workflow",
    NodeCategory.SCHEDULER: "Clock",
    NodeCategory.HUMAN: "UserCheck",
    NodeCategory.UTILITY: "Wrench",
    NodeCategory.SECURITY: "Shield",
    NodeCategory.CUSTOM: "Puzzle",
}


CATEGORY_COLORS = {
    NodeCategory.TRIGGER: "#22C55E",
    NodeCategory.AI: "#8B5CF6",
    NodeCategory.LOGIC: "#F97316",
    NodeCategory.DATA: "#0EA5E9",
    NodeCategory.INPUT: "#3B82F6",
    NodeCategory.OUTPUT: "#10B981",
    NodeCategory.FILE: "#F59E0B",
    NodeCategory.API: "#6366F1",
    NodeCategory.DATABASE: "#2563EB",
    NodeCategory.MEMORY: "#EC4899",
    NodeCategory.VECTOR: "#14B8A6",
    NodeCategory.EMBEDDING: "#A855F7",
    NodeCategory.OCR: "#EF4444",
    NodeCategory.VISION: "#F43F5E",
    NodeCategory.DOCUMENT: "#84CC16",
    NodeCategory.COMMUNICATION: "#06B6D4",
    NodeCategory.AUTOMATION: "#7C3AED",
    NodeCategory.SCHEDULER: "#64748B",
    NodeCategory.HUMAN: "#E11D48",
    NodeCategory.UTILITY: "#6B7280",
    NodeCategory.SECURITY: "#DC2626",
    NodeCategory.CUSTOM: "#9333EA",
}


def get_category_label(category: NodeCategory) -> str:
    """Return display label."""
    return CATEGORY_LABELS.get(category, category.value.title())


def get_category_icon(category: NodeCategory) -> str:
    """Return frontend icon name."""
    return CATEGORY_ICONS.get(category, "Box")


def get_category_color(category: NodeCategory) -> str:
    """Return UI color."""
    return CATEGORY_COLORS.get(category, "#64748B")


def list_categories() -> list[NodeCategory]:
    """Return all categories."""
    return list(NodeCategory)


def is_valid_category(value: str) -> bool:
    """Check if a category value is valid."""
    return value in NodeCategory._value2member_map_