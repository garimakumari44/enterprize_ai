"""
Integration Factory

Responsible for creating integration instances dynamically.
"""


from typing import Dict, Type

from .integration import Integration



class IntegrationFactory:
    """
    Creates integrations dynamically.
    """

    _registry: Dict[str, Type[Integration]] = {}


    @classmethod
    def register(
        cls,
        name: str,
        integration_class: Type[Integration]
    ):
        """
        Register integration.

        Example:

        IntegrationFactory.register(
            "slack",
            SlackIntegration
        )
        """

        cls._registry[name.lower()] = integration_class



    @classmethod
    def create(
        cls,
        name: str,
        config: dict
    ) -> Integration:
        """
        Create integration instance.
        """

        integration_name = name.lower()


        if integration_name not in cls._registry:
            raise ValueError(
                f"Integration '{name}' is not registered"
            )


        integration_class = cls._registry[
            integration_name
        ]


        return integration_class(
            name=integration_name,
            config=config
        )



    @classmethod
    def available_integrations(cls):
        """
        List available integrations.
        """

        return list(
            cls._registry.keys()
        )
