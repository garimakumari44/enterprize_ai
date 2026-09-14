from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import time
import math


# -----------------------------
# Cost Models
# -----------------------------

@dataclass
class ModelCost:
    model_name: str
    cost_per_1k_tokens: float
    latency_ms: float
    quality_score: float  # normalized 0–1


@dataclass
class NodeCostProfile:
    node_id: str
    estimated_tokens: int
    model: str
    tool_calls: int
    priority: int  # 1 (low) → 5 (critical)


@dataclass
class ExecutionCostResult:
    node_id: str
    estimated_cost: float
    estimated_latency: float
    recommended_model: str
    savings_potential: float


# -----------------------------
# Cost Optimizer Core
# -----------------------------

class CostOptimizer:
    """
    Optimizes workflow execution cost by:
    - selecting cheaper models when possible
    - reducing unnecessary tool calls
    - estimating execution cost before runtime
    """

    def __init__(self, model_registry: Dict[str, ModelCost]):
        self.model_registry = model_registry

    # -------------------------
    # Cost estimation
    # -------------------------

    def estimate_node_cost(self, profile: NodeCostProfile) -> ExecutionCostResult:
        model = self.model_registry[profile.model]

        base_cost = self._calculate_token_cost(profile.estimated_tokens, model)

        tool_cost = profile.tool_calls * 0.002  # assume fixed tool overhead

        total_cost = base_cost + tool_cost
        latency = model.latency_ms + (profile.tool_calls * 50)

        recommended_model = self._find_cheaper_model(profile, model)
        savings = self._estimate_savings(profile, model, recommended_model)

        return ExecutionCostResult(
            node_id=profile.node_id,
            estimated_cost=round(total_cost, 6),
            estimated_latency=round(latency, 2),
            recommended_model=recommended_model,
            savings_potential=round(savings, 6),
        )

    # -------------------------
    # Model selection
    # -------------------------

    def _find_cheaper_model(
        self, profile: NodeCostProfile, current_model: ModelCost
    ) -> str:
        best_model = profile.model
        best_score = self._score_model(current_model, profile)

        for model_name, model in self.model_registry.items():
            if model_name == profile.model:
                continue

            score = self._score_model(model, profile)

            # prefer lower cost but respect quality threshold
            if score < best_score and model.quality_score >= 0.7:
                best_model = model_name
                best_score = score

        return best_model

    def _score_model(self, model: ModelCost, profile: NodeCostProfile) -> float:
        cost = self._calculate_token_cost(profile.estimated_tokens, model)
        latency = model.latency_ms
        quality_penalty = (1 - model.quality_score) * 10

        return cost + (latency / 1000.0) + quality_penalty

    # -------------------------
    # Cost calculations
    # -------------------------

    def _calculate_token_cost(self, tokens: int, model: ModelCost) -> float:
        return (tokens / 1000.0) * model.cost_per_1k_tokens

    def _estimate_savings(
        self,
        profile: NodeCostProfile,
        current_model: ModelCost,
        recommended_model_name: str,
    ) -> float:
        if recommended_model_name == profile.model:
            return 0.0

        recommended = self.model_registry[recommended_model_name]

        current_cost = self._calculate_token_cost(profile.estimated_tokens, current_model)
        new_cost = self._calculate_token_cost(profile.estimated_tokens, recommended)

        return max(0.0, current_cost - new_cost)

    # -------------------------
    # Workflow-level optimization
    # -------------------------

    def optimize_workflow(
        self, profiles: List[NodeCostProfile]
    ) -> List[ExecutionCostResult]:

        results = []

        for profile in profiles:
            result = self.estimate_node_cost(profile)
            results.append(result)

        return sorted(results, key=lambda x: x.estimated_cost, reverse=True)

    # -------------------------
    # Real-time adaptation hooks
    # -------------------------

    def should_throttle_node(self, result: ExecutionCostResult, budget: float) -> bool:
        return result.estimated_cost > budget

    def adaptive_model_switch(self, profile: NodeCostProfile, budget: float) -> str:
        result = self.estimate_node_cost(profile)

        if result.estimated_cost <= budget:
            return profile.model

        return result.recommended_model