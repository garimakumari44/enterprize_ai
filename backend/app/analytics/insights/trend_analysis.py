"""
Trend Analysis Engine

Detects patterns from historical analytics.
"""

from typing import Dict, Any, List
from datetime import datetime



class TrendAnalysis:


    def __init__(
        self,
        analytics_repository
    ):

        self.repository = analytics_repository



    async def analyze(
        self,
        organization_id: str,
        period: str = "30d"
    ) -> Dict[str, Any]:


        history = await self.repository.get_history(
            organization_id,
            period
        )


        trends = []



        executions = [
            item["executions"]
            for item in history
        ]


        if len(executions) > 1:


            growth = (
                executions[-1]
                -
                executions[0]
            )


            if growth > 0:

                trends.append(
                    {
                        "metric":
                        "workflow_growth",

                        "direction":
                        "up",

                        "change":
                        growth
                    }
                )


            else:

                trends.append(
                    {
                        "metric":
                        "workflow_growth",

                        "direction":
                        "down",

                        "change":
                        growth
                    }
                )



        return {


            "organization_id":
                organization_id,


            "period":
                period,


            "generated_at":
                datetime.utcnow(),


            "trends":
                trends

        }