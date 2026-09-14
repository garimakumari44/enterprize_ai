from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from statistics import mean
from typing import Dict, List, Optional


@dataclass
class NodeExecutionMetric:
    node_id: str
    execution_time: float
    success: bool
    retries: int = 0
    timestamp: float = field(default_factory=time.time)


@dataclass
class WorkflowExecutionMetric:
    workflow_id: str
    execution_time: float
    success: bool
    timestamp: float = field(default_factory=time.time)


class ExecutionProfiler:
    """
    Collects runtime execution metrics and provides
    optimization insights.
    """

    def __init__(self):
        self.node_metrics: List[NodeExecutionMetric] = []
        self.workflow_metrics: List[WorkflowExecutionMetric] = []

    # --------------------------------------------------
    # Recording Metrics
    # --------------------------------------------------

    def record_node_execution(
        self,
        node_id: str,
        execution_time: float,
        success: bool,
        retries: int = 0,
    ) -> None:

        metric = NodeExecutionMetric(
            node_id=node_id,
            execution_time=execution_time,
            success=success,
            retries=retries,
        )

        self.node_metrics.append(metric)

    def record_workflow_execution(
        self,
        workflow_id: str,
        execution_time: float,
        success: bool,
    ) -> None:

        metric = WorkflowExecutionMetric(
            workflow_id=workflow_id,
            execution_time=execution_time,
            success=success,
        )

        self.workflow_metrics.append(metric)

    # --------------------------------------------------
    # Analytics
    # --------------------------------------------------

    def average_node_time(self, node_id: str) -> float:

        executions = [
            m.execution_time
            for m in self.node_metrics
            if m.node_id == node_id
        ]

        return mean(executions) if executions else 0.0

    def average_workflow_time(self, workflow_id: str) -> float:

        executions = [
            m.execution_time
            for m in self.workflow_metrics
            if m.workflow_id == workflow_id
        ]

        return mean(executions) if executions else 0.0

    def node_failure_rate(self, node_id: str) -> float:

        executions = [
            m
            for m in self.node_metrics
            if m.node_id == node_id
        ]

        if not executions:
            return 0.0

        failures = sum(1 for m in executions if not m.success)

        return failures / len(executions)

    def workflow_failure_rate(self, workflow_id: str) -> float:

        executions = [
            m
            for m in self.workflow_metrics
            if m.workflow_id == workflow_id
        ]

        if not executions:
            return 0.0

        failures = sum(1 for m in executions if not m.success)

        return failures / len(executions)

    # --------------------------------------------------
    # Bottleneck Detection
    # --------------------------------------------------

    def find_slowest_nodes(
        self,
        top_k: int = 5,
    ) -> List[Dict]:

        grouped = defaultdict(list)

        for metric in self.node_metrics:
            grouped[metric.node_id].append(metric.execution_time)

        results = []

        for node_id, timings in grouped.items():
            results.append(
                {
                    "node_id": node_id,
                    "avg_execution_time": mean(timings),
                }
            )

        results.sort(
            key=lambda x: x["avg_execution_time"],
            reverse=True,
        )

        return results[:top_k]

    # --------------------------------------------------
    # Optimization Suggestions
    # --------------------------------------------------

    def generate_recommendations(self) -> List[str]:

        recommendations = []

        for node in self.find_slowest_nodes():

            if node["avg_execution_time"] > 5:
                recommendations.append(
                    f"Node {node['node_id']} is slow "
                    f"({node['avg_execution_time']:.2f}s avg). "
                    f"Consider caching, batching, or parallel execution."
                )

        node_ids = {m.node_id for m in self.node_metrics}

        for node_id in node_ids:

            failure_rate = self.node_failure_rate(node_id)

            if failure_rate > 0.30:
                recommendations.append(
                    f"Node {node_id} has high failure rate "
                    f"({failure_rate:.0%}). "
                    f"Investigate reliability issues."
                )

        return recommendations

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    def get_summary(self) -> Dict:

        return {
            "total_node_executions": len(self.node_metrics),
            "total_workflow_executions": len(
                self.workflow_metrics
            ),
            "slowest_nodes": self.find_slowest_nodes(),
            "recommendations": self.generate_recommendations(),
        }