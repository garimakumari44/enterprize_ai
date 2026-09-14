from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentAction:
    """
    A single atomic action an agent decides to take.
    This is NOT execution yet—just intent.
    """

    action_type: str  # e.g. CALL_TOOL, READ_STATE, WRITE_STATE
    target: Optional[str] = None  # tool name / node / resource
    input: Dict[str, Any] = field(default_factory=dict)
    reasoning: Optional[str] = None


@dataclass
class AgentObservation:
    """
    What the agent receives from environment execution.
    """

    source: str  # tool/node/system
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentStep:
    """
    One reasoning-execution cycle.
    """

    step_id: str

    observation: Optional[AgentObservation] = None

    thought: Optional[str] = None  # future reasoning trace

    action: Optional[AgentAction] = None

    result: Optional[Any] = None


@dataclass
class AgentState:
    """
    Persistent agent-level state (NOT workflow state).
    """

    agent_id: str
    role: str  # planner | executor | researcher | analyzer

    goal: str

    memory: Dict[str, Any] = field(default_factory=dict)

    context: Dict[str, Any] = field(default_factory=dict)

    steps: List[AgentStep] = field(default_factory=list)

    status: str = "IDLE"  # IDLE | RUNNING | COMPLETED | FAILED

    def add_step(self, step: AgentStep) -> None:
        self.steps.append(step)

    def update_memory(self, key: str, value: Any) -> None:
        self.memory[key] = value

    def get_memory(self, key: str, default=None) -> Any:
        return self.memory.get(key, default)