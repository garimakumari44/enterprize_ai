"""
Execution-related exceptions.

Custom exceptions raised by the workflow execution engine.
"""


class ExecutionException(Exception):
    """
    Base exception for all execution-related errors.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ExecutionNotFoundException(ExecutionException):
    """
    Raised when an execution cannot be found.
    """


class ExecutionAlreadyRunningException(ExecutionException):
    """
    Raised when attempting to start an execution that is already running.
    """


class ExecutionCancelledException(ExecutionException):
    """
    Raised when an execution has been cancelled.
    """


class ExecutionTimeoutException(ExecutionException):
    """
    Raised when an execution exceeds its configured timeout.
    """


class ExecutionFailedException(ExecutionException):
    """
    Raised when workflow execution fails.
    """


class InvalidExecutionStateException(ExecutionException):
    """
    Raised when an operation is not allowed for the current execution state.
    """


class WorkflowExecutionException(ExecutionException):
    """
    Raised when a workflow cannot be executed due to an invalid workflow
    definition or execution context.
    """


class ContextVariableException(ExecutionException):
    """
    Raised when a required execution context variable is missing or invalid.
    """


class ExpressionEvaluationException(ExecutionException):
    """
    Raised when an expression cannot be evaluated.
    """


class RuntimeNotFoundException(ExecutionException):
    """
    Raised when no runtime implementation exists for a node type.
    """

    def __init__(self, node_type: str):
        super().__init__(f"No runtime registered for node type '{node_type}'")
        self.node_type = node_type