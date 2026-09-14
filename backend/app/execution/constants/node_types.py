"""
Workflow node type constants.

Defines all supported node types that can be executed
by the workflow execution engine.
"""

from enum import StrEnum


class NodeType(StrEnum):
    """
    Supported workflow node types.
    """

    # Flow Control
    START = "START"
    END = "END"
    CONDITION = "CONDITION"
    DELAY = "DELAY"

    # Communication
    HTTP = "HTTP"
    WEBHOOK = "WEBHOOK"

    # Data
    DATABASE = "DATABASE"

    # AI (Future)
    LLM = "LLM"
    PROMPT = "PROMPT"
    EMBEDDING = "EMBEDDING"

    # Logic
    CODE = "CODE"
    SCRIPT = "SCRIPT"

    # Integration
    EMAIL = "EMAIL"
    SLACK = "SLACK"
    DISCORD = "DISCORD"

    # File
    FILE_UPLOAD = "FILE_UPLOAD"
    FILE_DOWNLOAD = "FILE_DOWNLOAD"