# adaptation/decision_engine.py

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DecisionType(str, Enum):
    CONTINUE = "continue"
    REPLAN = "replan"
    RETRY = "retry"
    RECOVER = "recover"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    SWITCH_PATH = "switch_path"
    ABORT = "abort"


@dataclass
class Decision:
    type: DecisionType
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class DecisionEngine:
    """
    Converts context signals into adaptation decisions.

    Input:
        Context Analysis

    Output:
        Adaptation Decision
    """

    def evaluate(
        self,
        context: Dict[str, Any]
    ) -> List[Decision]:

        decisions: List[Decision] = []

        # ----------------------------------
        # Failure handling
        # ----------------------------------

        failure_rate = context.get("failure_rate", 0)

        if failure_rate > 0.4:
            decisions.append(
                Decision(
                    type=DecisionType.RECOVER,
                    reason="High workflow failure rate detected",
                    metadata={
                        "failure_rate": failure_rate
                    }
                )
            )

        # ----------------------------------
        # Latency handling
        # ----------------------------------

        latency_ms = context.get("avg_latency_ms", 0)

        if latency_ms > 5000:
            decisions.append(
                Decision(
                    type=DecisionType.SCALE_UP,
                    reason="Workflow latency too high",
                    metadata={
                        "latency_ms": latency_ms
                    }
                )
            )

        # ----------------------------------
        # Resource utilization
        # ----------------------------------

        cpu_util = context.get("cpu_utilization", 0)

        if cpu_util > 85:
            decisions.append(
                Decision(
                    type=DecisionType.SCALE_UP,
                    reason="CPU utilization high",
                    metadata={
                        "cpu_utilization": cpu_util
                    }
                )
            )

        elif cpu_util < 20:
            decisions.append(
                Decision(
                    type=DecisionType.SCALE_DOWN,
                    reason="CPU underutilized",
                    metadata={
                        "cpu_utilization": cpu_util
                    }
                )
            )

        # ----------------------------------
        # Retry recommendation
        # ----------------------------------

        transient_errors = context.get(
            "transient_errors",
            0
        )

        if transient_errors > 0:
            decisions.append(
                Decision(
                    type=DecisionType.RETRY,
                    reason="Transient execution errors detected",
                    metadata={
                        "count": transient_errors
                    }
                )
            )

        # ----------------------------------
        # Dynamic replanning
        # ----------------------------------

        bottleneck_nodes = context.get(
            "bottleneck_nodes",
            []
        )

        if bottleneck_nodes:
            decisions.append(
                Decision(
                    type=DecisionType.REPLAN,
                    reason="Workflow bottlenecks detected",
                    metadata={
                        "nodes": bottleneck_nodes
                    }
                )
            )

        # ----------------------------------
        # Workflow healthy
        # ----------------------------------

        if not decisions:
            decisions.append(
                Decision(
                    type=DecisionType.CONTINUE,
                    reason="Workflow operating normally"
                )
            )

        return decisions