"""
Node-related exceptions.

Custom exceptions raised during node execution.
"""


class NodeException(Exception):
    """
    Base exception for all node-related errors.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NodeNotFoundException(NodeException):
    """
    Raised when a node cannot be found in the workflow.
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        super().__init__(f"Node '{node_id}' was not found.")


class InvalidNodeTypeException(NodeException):
    """
    Raised when a node type is not supported.
    """

    def __init__(self, node_type: str):
        self.node_type = node_type
        super().__init__(f"Unsupported node type '{node_type}'.")


class InvalidNodeConfigurationException(NodeException):
    """
    Raised when a node's configuration is invalid.
    """

    def __init__(self, node_id: str, reason: str):
        self.node_id = node_id
        self.reason = reason
        super().__init__(f"Invalid configuration for node '{node_id}': {reason}")


class NodeExecutionException(NodeException):
    """
    Raised when execution of a node fails.
    """

    def __init__(self, node_id: str, message: str):
        self.node_id = node_id
        super().__init__(f"Node '{node_id}' execution failed: {message}")


class NodeTimeoutException(NodeException):
    """
    Raised when a node execution exceeds its timeout.
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        super().__init__(f"Node '{node_id}' execution timed out.")


class NodeValidationException(NodeException):
    """
    Raised when a node fails validation before execution.
    """

    def __init__(self, node_id: str, reason: str):
        self.node_id = node_id
        self.reason = reason
        super().__init__(f"Node '{node_id}' validation failed: {reason}")


class MissingNodeInputException(NodeException):
    """
    Raised when a required node input is missing.
    """

    def __init__(self, node_id: str, input_name: str):
        self.node_id = node_id
        self.input_name = input_name
        super().__init__(
            f"Required input '{input_name}' is missing for node '{node_id}'."
        )


class NodeOutputException(NodeException):
    """
    Raised when a node produces an invalid output.
    """

    def __init__(self, node_id: str, message: str):
        self.node_id = node_id
        super().__init__(f"Invalid output from node '{node_id}': {message}")