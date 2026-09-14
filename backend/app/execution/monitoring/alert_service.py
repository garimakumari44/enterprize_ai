"""
Alert Service.

Handles monitoring alerts.

Responsibilities:
- Create alerts
- Track active alerts
- Resolve alerts
- Alert history
"""


from datetime import datetime
from typing import Dict, List
from uuid import uuid4


from app.execution.monitoring.logger import (
    execution_logger
)



class AlertService:
    """
    Central alert management service.
    """


    def __init__(self):

        # Active alerts

        self.alerts: Dict[str, dict] = {}



    # ==================================================
    # Create Alert
    # ==================================================

    def create_alert(
        self,
        title: str,
        message: str,
        severity: str = "WARNING",
        source: str = "system"
    ):
        """
        Create new alert.
        """


        alert_id = str(
            uuid4()
        )


        alert = {

            "id": alert_id,

            "title": title,

            "message": message,

            "severity": severity,

            "source": source,

            "status": "ACTIVE",

            "created_at":
                datetime.utcnow()
                .isoformat(),

            "resolved_at": None
        }



        self.alerts[
            alert_id
        ] = alert



        execution_logger.warning(
            "Alert created",
            {
                "alert_id": alert_id,

                "title": title,

                "severity": severity,

                "source": source
            }
        )



        return alert



    # ==================================================
    # Resolve Alert
    # ==================================================

    def resolve_alert(
        self,
        alert_id: str
    ):
        """
        Resolve existing alert.
        """


        alert = self.alerts.get(
            alert_id
        )


        if not alert:
            return False



        alert["status"] = "RESOLVED"


        alert["resolved_at"] = (
            datetime.utcnow()
            .isoformat()
        )


        execution_logger.info(
            "Alert resolved",
            {
                "alert_id": alert_id
            }
        )


        return True



    # ==================================================
    # Get Active Alerts
    # ==================================================

    def get_active_alerts(
        self
    ) -> List[dict]:
        """
        Return unresolved alerts.
        """


        return [

            alert

            for alert in self.alerts.values()

            if alert["status"]
            ==
            "ACTIVE"

        ]



    # ==================================================
    # Get Alert History
    # ==================================================

    def get_history(
        self
    ) -> List[dict]:
        """
        Return all alerts.
        """


        return list(
            self.alerts.values()
        )



    # ==================================================
    # Duplicate Check
    # ==================================================

    def alert_exists(
        self,
        title: str,
        source: str
    ):
        """
        Prevent duplicate alerts.
        """


        for alert in self.alerts.values():

            if (

                alert["title"]
                ==
                title

                and

                alert["source"]
                ==
                source

                and

                alert["status"]
                ==
                "ACTIVE"

            ):

                return True



        return False



    # ==================================================
    # Convenience Methods
    # ==================================================

    def worker_failure_alert(
        self,
        worker_id: str
    ):

        if self.alert_exists(
            "Worker failure",
            worker_id
        ):
            return


        return self.create_alert(

            title="Worker failure",

            message=(
                f"Worker {worker_id} "
                "is not responding"
            ),

            severity="CRITICAL",

            source=worker_id
        )



    def queue_backlog_alert(
        self,
        queue_name: str,
        size: int
    ):

        if self.alert_exists(
            "Queue backlog",
            queue_name
        ):
            return


        return self.create_alert(

            title="Queue backlog",

            message=(
                f"Queue {queue_name} "
                f"has {size} pending jobs"
            ),

            severity="WARNING",

            source=queue_name
        )



    def execution_failure_alert(
        self,
        execution_id: str,
        error: str
    ):


        return self.create_alert(

            title="Execution failed",

            message=error,

            severity="ERROR",

            source=execution_id
        )



# --------------------------------------------------
# Global Instance
# --------------------------------------------------

alert_service = AlertService()