"""
Workflow validation logic.

Responsible for validating workflow definitions
before saving or publishing.
"""


from typing import Dict, List, Any


class WorkflowValidator:
    """
    Validator for workflow graphs.

    A workflow consists of:
    - nodes
    - edges
    - metadata
    """

    @staticmethod
    def validate_workflow(workflow_data: Dict[str, Any]) -> Dict:
        """
        Validate complete workflow.

        Returns:
            {
                "valid": True/False,
                "errors": []
            }
        """

        errors = []

        nodes = workflow_data.get("nodes", [])
        edges = workflow_data.get("edges", [])

        # Validate nodes
        node_errors = WorkflowValidator.validate_nodes(nodes)
        errors.extend(node_errors)

        # Validate edges
        edge_errors = WorkflowValidator.validate_edges(
            nodes,
            edges
        )
        errors.extend(edge_errors)

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }


    @staticmethod
    def validate_nodes(
        nodes: List[Dict]
    ) -> List[str]:
        """
        Validate workflow nodes.
        """

        errors = []

        if not nodes:
            errors.append(
                "Workflow must contain at least one node"
            )

            return errors


        node_ids = set()


        for node in nodes:

            node_id = node.get("id")
            node_type = node.get("type")


            # Check node id
            if not node_id:
                errors.append(
                    "Node id is required"
                )


            # Duplicate node IDs
            if node_id in node_ids:
                errors.append(
                    f"Duplicate node id: {node_id}"
                )


            node_ids.add(node_id)


            # Check node type
            if not node_type:
                errors.append(
                    f"Node {node_id} missing type"
                )


        return errors



    @staticmethod
    def validate_edges(
        nodes: List[Dict],
        edges: List[Dict]
    ) -> List[str]:
        """
        Validate workflow edges.
        """

        errors = []


        node_ids = {
            node.get("id")
            for node in nodes
        }


        for edge in edges:

            source = edge.get(
                "source"
            )

            target = edge.get(
                "target"
            )


            if not source:
                errors.append(
                    "Edge source missing"
                )


            if not target:
                errors.append(
                    "Edge target missing"
                )


            # Check source node exists
            if source not in node_ids:
                errors.append(
                    f"Source node {source} does not exist"
                )


            # Check target node exists
            if target not in node_ids:
                errors.append(
                    f"Target node {target} does not exist"
                )


            # Prevent self connection
            if source == target:
                errors.append(
                    f"Node {source} cannot connect to itself"
                )


        return errors