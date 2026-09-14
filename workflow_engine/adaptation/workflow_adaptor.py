

from typing import List

from contracts.adaptation import (
    AdaptationAction,
    AdaptationType
)

from contracts.workflow import Workflow
from contracts.state import WorkflowState


class WorkflowAdaptor:
    """
    Runtime workflow adaptation engine.

    Responsible for modifying
    workflow execution plans based
    on execution state.
    """

    def analyze(
        self,
        workflow: Workflow,
        state: WorkflowState
    ) -> List[AdaptationAction]:

        actions = []

        for node_id, node_state in state.node_states.items():

            if node_state.status == "failed":

                actions.append(
                    AdaptationAction(
                        type=AdaptationType.RETRY,
                        target_node_id=node_id,
                        metadata={
                            "attempt": node_state.retry_count + 1
                        }
                    )
                )

        return actions

    def apply(
        self,
        workflow: Workflow,
        actions: List[AdaptationAction]
    ) -> Workflow:

        for action in actions:

            if action.type == AdaptationType.RETRY:
                self._apply_retry(
                    workflow,
                    action
                )

            elif action.type == AdaptationType.INSERT_NODE:
                self._apply_insert(
                    workflow,
                    action
                )

            elif action.type == AdaptationType.REMOVE_NODE:
                self._apply_remove(
                    workflow,
                    action
                )

        return workflow

    def adapt(
        self,
        workflow: Workflow,
        state: WorkflowState
    ) -> Workflow:

        actions = self.analyze(
            workflow,
            state
        )

        if not actions:
            return workflow

        return self.apply(
            workflow,
            actions
        )

    def _apply_retry(
        self,
        workflow: Workflow,
        action: AdaptationAction
    ) -> None:

        node = workflow.nodes.get(
            action.target_node_id
        )

        if node:
            node.retry_required = True

    def _apply_insert(
        self,
        workflow: Workflow,
        action: AdaptationAction
    ) -> None:

        pass

    def _apply_remove(
        self,
        workflow: Workflow,
        action: AdaptationAction
    ) -> None:

        pass