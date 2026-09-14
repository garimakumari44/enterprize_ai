"""
Base Integration Interface

All external integrations must implement this contract.

Examples:
- SlackIntegration
- EmailIntegration
- S3Integration
- GoogleDriveIntegration
- PostgresIntegration
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Integration(ABC):
    """
    Abstract base class for all integrations.
    """

    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
    ):
        self.name = name
        self.config = config
        self.connected = False


    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection with external service.

        Example:
        - Authenticate API client
        - Create SDK client
        - Validate credentials
        """

        pass


    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close connection / cleanup resources.
        """

        pass


    @abstractmethod
    async def execute(
        self,
        action: str,
        payload: Dict[str, Any],
    ) -> Any:
        """
        Execute integration operation.

        Example:

        Slack:
            send_message

        S3:
            upload_file

        Database:
            query
        """

        pass


    async def health_check(self) -> Dict[str, Any]:
        """
        Check integration availability.
        """

        return {
            "integration": self.name,
            "status": "connected" if self.connected else "disconnected"
        }


    def get_config(self) -> Dict[str, Any]:
        """
        Return integration configuration.
        """

        return self.config


    def is_connected(self) -> bool:
        """
        Connection status.
        """

        return self.connected


    def set_connected(
        self,
        value: bool
    ):
        """
        Update connection state.
        """

        self.connected = value