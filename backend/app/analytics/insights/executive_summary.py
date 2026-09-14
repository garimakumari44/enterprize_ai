"""
Executive Summary Generator

Transforms analytics metrics into
business intelligence summaries.
"""

from datetime import datetime
from typing import Dict, Any, List



class ExecutiveSummary:


    def __init__(
        self,
        analytics_service
    ):

        self.analytics_service = analytics_service



    async def generate(
        self,
        organization_id: str
    ) -> Dict[str, Any]:

        metrics = await self.analytics_service.summary(
            organization_id
        )


        insights = []


        # Automation insight

        automation_rate = metrics.get(
            "automation_rate",
            0
        )


        if automation_rate > 80:

            insights.append(
                {
                    "type": "success",
                    "message":
                    f"Automation rate reached {automation_rate}%"
                }
            )


        else:

            insights.append(
                {
                    "type": "warning",
                    "message":
                    "Automation opportunities detected"
                }
            )



        # Failure insight

        failure_rate = metrics.get(
            "failure_rate",
            0
        )


        if failure_rate > 5:

            insights.append(
                {
                    "type":"risk",
                    "message":
                    f"Execution failures increased to {failure_rate}%"
                }
            )



        return {


            "organization_id":
                organization_id,


            "generated_at":
                datetime.utcnow(),


            "summary": {


                "total_executions":
                    metrics.get(
                        "executions",
                        0
                    ),


                "automation_rate":
                    automation_rate,


                "cost_saved":
                    metrics.get(
                        "cost_saved",
                        0
                    )

            },


            "insights":
                insights

        }