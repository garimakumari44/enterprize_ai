"""
Worker health checker.
"""


from datetime import datetime



class WorkerHealth:


    workers = {}



    @classmethod
    def register(
        cls,
        worker_name
    ):

        cls.workers[worker_name] = {

            "status":"running",
            "started_at":
                datetime.utcnow()

        }



    @classmethod
    def mark_failed(
        cls,
        worker_name,
        error
    ):

        cls.workers[worker_name] = {

            "status":"failed",
            "error":error,
            "time":
                datetime.utcnow()

        }



    @classmethod
    def status(cls):

        return cls.workers