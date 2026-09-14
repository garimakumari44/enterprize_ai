# adaptation/context_analyzer.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from contracts.enums import NodeStatus


@dataclass
class ContextSignal:
    """
    A signal extracted from runtime context.
    """

    signal_type: str
    severity: str
    source: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextAnalysis:
    """
    Output of context analysis.
    """

    signals: List[ContextSignal] = field(default_factory=list)

    def has_signal(self, signal_type: str) -> bool:
        return any(s.signal_type == signal_type for s in self.signals)

    def get_signals(self, signal_type: str) -> List[ContextSignal]:
        return [
            s
            for s in self.signals
            if s.signal_type == signal_type
        ]


class ContextAnalyzer:
    """
    Analyzes workflow execution context and
    extracts adaptation signals.

    Examples:
    - task failures
    - repeated retries
    - SLA breaches
    - latency spikes
    - resource shortages
    - dependency bottlenecks
    """

    def analyze(
        self,
        workflow_state: Dict[str, Any],
    ) -> ContextAnalysis:

        analysis = ContextAnalysis()

        self._detect_failures(
            workflow_state,
            analysis,
        )

        self._detect_retry_storms(
            workflow_state,
            analysis,
        )

        self._detect_sla_breaches(
            workflow_state,
            analysis,
        )

        self._detect_resource_pressure(
            workflow_state,
            analysis,
        )

        return analysis

    # --------------------------------------------------
    # Failure Detection
    # --------------------------------------------------

    def _detect_failures(
        self,
        workflow_state: Dict[str, Any],
        analysis: ContextAnalysis,
    ) -> None:

        nodes = workflow_state.get("nodes", [])

        for node in nodes:

            status = node.get("status")

            if status == NodeStatus.FAILED.value:

                analysis.signals.append(
                    ContextSignal(
                        signal_type="TASK_FAILED",
                        severity="high",
                        source=node["id"],
                        details={
                            "node_name": node.get("name"),
                            "error": node.get("error"),
                        },
                    )
                )

    # --------------------------------------------------
    # Retry Detection
    # --------------------------------------------------

    def _detect_retry_storms(
        self,
        workflow_state: Dict[str, Any],
        analysis: ContextAnalysis,
    ) -> None:

        nodes = workflow_state.get("nodes", [])

        for node in nodes:

            retries = node.get("retry_count", 0)

            if retries >= 3:

                analysis.signals.append(
                    ContextSignal(
                        signal_type="EXCESSIVE_RETRIES",
                        severity="medium",
                        source=node["id"],
                        details={
                            "retry_count": retries,
                        },
                    )
                )

    # --------------------------------------------------
    # SLA Detection
    # --------------------------------------------------

    def _detect_sla_breaches(
        self,
        workflow_state: Dict[str, Any],
        analysis: ContextAnalysis,
    ) -> None:

        workflow_duration = workflow_state.get(
            "duration_seconds",
            0,
        )

        sla_limit = workflow_state.get(
            "sla_limit_seconds",
            None,
        )

        if (
            sla_limit is not None
            and workflow_duration > sla_limit
        ):
            analysis.signals.append(
                ContextSignal(
                    signal_type="SLA_BREACH",
                    severity="high",
                    source="workflow",
                    details={
                        "duration": workflow_duration,
                        "sla_limit": sla_limit,
                    },
                )
            )

    # --------------------------------------------------
    # Resource Analysis
    # --------------------------------------------------

    def _detect_resource_pressure(
        self,
        workflow_state: Dict[str, Any],
        analysis: ContextAnalysis,
    ) -> None:

        cpu = workflow_state.get("cpu_usage", 0)
        memory = workflow_state.get("memory_usage", 0)

        if cpu > 85:

            analysis.signals.append(
                ContextSignal(
                    signal_type="HIGH_CPU_USAGE",
                    severity="medium",
                    source="system",
                    details={
                        "cpu_usage": cpu,
                    },
                )
            )

        if memory > 90:

            analysis.signals.append(
                ContextSignal(
                    signal_type="HIGH_MEMORY_USAGE",
                    severity="high",
                    source="system",
                    details={
                        "memory_usage": memory,
                    },
                )
            )

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    def summarize(
        self,
        analysis: ContextAnalysis,
    ) -> Dict[str, Any]:

        return {
            "total_signals": len(analysis.signals),
            "high_severity": len(
                [
                    s
                    for s in analysis.signals
                    if s.severity == "high"
                ]
            ),
            "medium_severity": len(
                [
                    s
                    for s in analysis.signals
                    if s.severity == "medium"
                ]
            ),
            "signals": [
                {
                    "type": s.signal_type,
                    "severity": s.severity,
                    "source": s.source,
                }
                for s in analysis.signals
            ],
        }