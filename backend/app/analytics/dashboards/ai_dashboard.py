"""
AI Dashboard

Tracks AI system health,
LLM performance,
agent behavior,
and model metrics.
"""


from datetime import datetime
from typing import Dict, Any



class AIDashboard:
    """
    AI infrastructure monitoring dashboard.
    """


    def __init__(
        self,
        model_service,
        agent_service,
        evaluation_service,
        usage_service,
    ):

        self.model_service = model_service

        self.agent_service = agent_service

        self.evaluation_service = evaluation_service

        self.usage_service = usage_service



    async def generate(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Generate AI performance dashboard.
        """


        models = await self.model_service.metrics(
            organization_id
        )


        agents = await self.agent_service.metrics(
            organization_id
        )


        evaluations = await self.evaluation_service.summary(
            organization_id
        )


        usage = await self.usage_service.summary(
            organization_id
        )



        return {


            "dashboard": "ai",


            "generated_at":
                datetime.utcnow(),


            "organization_id":
                organization_id,



            "model_performance": {


                "models_used":
                    models.get(
                        "count",
                        0
                    ),


                "average_latency_ms":
                    models.get(
                        "latency",
                        0
                    ),


                "error_rate":
                    models.get(
                        "error_rate",
                        0
                    )

            },



            "agent_metrics": {


                "total_agents":
                    agents.get(
                        "total",
                        0
                    ),


                "successful_tasks":
                    agents.get(
                        "successful_tasks",
                        0
                    ),


                "average_confidence":
                    agents.get(
                        "confidence",
                        0
                    )

            },



            "llm_usage": {


                "tokens_used":
                    usage.get(
                        "tokens",
                        0
                    ),


                "estimated_cost":
                    usage.get(
                        "cost",
                        0
                    )

            },



            "ai_quality": {


                "evaluation_score":
                    evaluations.get(
                        "score",
                        0
                    ),


                "hallucination_rate":
                    evaluations.get(
                        "hallucination_rate",
                        0
                    )

            }

        }