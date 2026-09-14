

from __future__ import annotations

import heapq
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, List


class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


_PRIORITY_SCORE = {
    Priority.CRITICAL: 0,
    Priority.HIGH: 1,
    Priority.NORMAL: 2,
    Priority.LOW: 3,
}


@dataclass(order=True)
class ScheduledTask:
    sort_key: tuple = field(init=False)

    task_id: str
    workflow_id: str

    run_at: float
    priority: Priority = Priority.NORMAL

    payload: Optional[dict] = None

    def __post_init__(self):
        self.sort_key = (
            self.run_at,
            _PRIORITY_SCORE[self.priority],
        )


class SchedulingEngine:
    """
    Responsible for:
    - delayed execution
    - priority ordering
    - task queueing
    - dispatching ready tasks
    """

    def __init__(self):
        self._queue: List[ScheduledTask] = []
        self._lock = threading.Lock()

        self._running = False

    # --------------------------------------------------
    # Scheduling
    # --------------------------------------------------

    def schedule(
        self,
        task_id: str,
        workflow_id: str,
        delay_seconds: int = 0,
        priority: Priority = Priority.NORMAL,
        payload: Optional[dict] = None,
    ) -> ScheduledTask:

        task = ScheduledTask(
            task_id=task_id,
            workflow_id=workflow_id,
            run_at=time.time() + delay_seconds,
            priority=priority,
            payload=payload,
        )

        with self._lock:
            heapq.heappush(self._queue, task)

        return task

    # --------------------------------------------------
    # Queue Operations
    # --------------------------------------------------

    def next_ready_task(self) -> Optional[ScheduledTask]:

        with self._lock:

            if not self._queue:
                return None

            task = self._queue[0]

            if task.run_at > time.time():
                return None

            return heapq.heappop(self._queue)

    def pending_count(self) -> int:
        with self._lock:
            return len(self._queue)

    # --------------------------------------------------
    # Execution Loop
    # --------------------------------------------------

    def start(self, callback):

        self._running = True

        while self._running:

            task = self.next_ready_task()

            if task:
                callback(task)

            time.sleep(0.1)

    def stop(self):
        self._running = False

    # --------------------------------------------------
    # Inspection
    # --------------------------------------------------

    def list_tasks(self):

        with self._lock:
            return list(self._queue)

    def clear(self):

        with self._lock:
            self._queue.clear()