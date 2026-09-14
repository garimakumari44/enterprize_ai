from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import time
import math


# ----------------------------
# Optimization Models
# ----------------------------

@dataclass
class OptimizationMetrics:
    latency_ms: float
    cost: float
    success_rate: float
    retry_count: int
    resource_usage: float  # CPU/memory proxy


@dataclass
class OptimizationDecision:
    node_id: str
    action: str  # "scale_up", "scale_down", "retry", "skip", "reroute"
    reason: str
    confidence: float


# ----------------------------
# Workflow Optimizer Core
# ----------------------------

class WorkflowOptimizer:
    """
    Responsible for optimizing workflow execution paths in real-time
    based on performance signals and execution history.
    """

    def __init__(
        self,
        latency_threshold: float = 2000.0,
        cost_threshold: float = 1.0,
        success_threshold: float = 0.85,
    ):
        self.latency_threshold = latency_threshold
        self.cost_threshold = cost_threshold
        self.success_threshold = success_threshold

        # history store (in-memory for now)
        self.metrics_history: Dict[str, List[OptimizationMetrics]] = {}

    # ----------------------------
    # Public API
    # ----------------------------

    def record_metrics(self, node_id: str, metrics: OptimizationMetrics):
        if node_id not in self.metrics_history:
            self.metrics_history[node_id] = []
        self.metrics_history[node_id].append(metrics)

    def optimize_node(self, node_id: str) -> Optional[OptimizationDecision]:
        history = self.metrics_history.get(node_id, [])
        if not history:
            return None

        aggregated = self._aggregate(history)
        return self._decide(node_id, aggregated)

    def optimize_workflow(self, node_ids: List[str]) -> List[OptimizationDecision]:
        decisions = []
        for node_id in node_ids:
            decision = self.optimize_node(node_id)
            if decision:
                decisions.append(decision)
        return decisions

    # ----------------------------
    # Aggregation Layer
    # ----------------------------

    def _aggregate(self, history: List[OptimizationMetrics]) -> OptimizationMetrics:
        n = len(history)

        return OptimizationMetrics(
            latency_ms=sum(m.latency_ms for m in history) / n,
            cost=sum(m.cost for m in history) / n,
            success_rate=sum(m.success_rate for m in history) / n,
            retry_count=sum(m.retry_count for m in history) / n,
            resource_usage=sum(m.resource_usage for m in history) / n,
        )

    # ----------------------------
    # Decision Engine
    # ----------------------------

    def _decide(self, node_id: str, m: OptimizationMetrics) -> OptimizationDecision:
        # High latency → scale or reroute
        if m.latency_ms > self.latency_threshold:
            return OptimizationDecision(
                node_id=node_id,
                action="scale_up",
                reason=f"High latency detected: {m.latency_ms:.2f}ms",
                confidence=self._confidence(m.latency_ms, self.latency_threshold),
            )

        # High cost → optimize or downgrade model/tool
        if m.cost > self.cost_threshold:
            return OptimizationDecision(
                node_id=node_id,
                action="scale_down",
                reason=f"High cost detected: {m.cost:.4f}",
                confidence=self._confidence(m.cost, self.cost_threshold),
            )

        # Low success rate → retry or reroute
        if m.success_rate < self.success_threshold:
            action = "retry" if m.retry_count < 3 else "reroute"
            return OptimizationDecision(
                node_id=node_id,
                action=action,
                reason=f"Low success rate: {m.success_rate:.2f}",
                confidence=1.0 - m.success_rate,
            )

        # High resource usage → optimize execution
        if m.resource_usage > 0.8:
            return OptimizationDecision(
                node_id=node_id,
                action="optimize_execution",
                reason=f"High resource usage: {m.resource_usage:.2f}",
                confidence=0.7,
            )

        return OptimizationDecision(
            node_id=node_id,
            action="no_change",
            reason="System within optimal thresholds",
            confidence=0.9,
        )

    # ----------------------------
    # Utility
    # ----------------------------

    def _confidence(self, value: float, threshold: float) -> float:
        if threshold == 0:
            return 0.5
        return min(1.0, abs(value - threshold) / threshold)

    def clear_history(self, node_id: Optional[str] = None):
        if node_id:
            self.metrics_history.pop(node_id, None)
        else:
            self.metrics_history.clear()


# ----------------------------
# Example usage (for debugging)
# ----------------------------

if __name__ == "__main__":
    optimizer = WorkflowOptimizer()

    optimizer.record_metrics(
        "node_1",
        OptimizationMetrics(
            latency_ms=2500,
            cost=0.8,
            success_rate=0.9,
            retry_count=0,
            resource_usage=0.6,
        ),
    )

    optimizer.record_metrics(
        "node_1",
        OptimizationMetrics(
            latency_ms=3000,
            cost=1.2,
            success_rate=0.7,
            retry_count=1,
            resource_usage=0.9,
        ),
    )

    decision = optimizer.optimize_node("node_1")
    print(decision)