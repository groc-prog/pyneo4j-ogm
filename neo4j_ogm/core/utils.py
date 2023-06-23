"""
This module hold helper functions and utilities.
"""

from typing import Callable

from neo4j_ogm.core.exceptions import InstanceDestroyed, InstanceNotHydrated


def ensure_alive(func: Callable):
    """
    Decorator which ensures that a instance has not been destroyed and has been hydrated before running any queries.

    Raises:
        InstanceDestroyed: Raised if the method is called on a instance which has been destroyed
    """

    async def decorator(self, *args, **kwargs):
        if getattr(self, "_destroyed", True):
            raise InstanceDestroyed()

        if getattr(self, "_element_id", None) is None:
            raise InstanceNotHydrated()

        result = await func(self, *args, **kwargs)
        return result

    return decorator


def validate_instance(func: Callable):
    """
    Decorator which validates the model fields before calling the method

    Raises:
        ValidationError: Raised if the model validation fails
    """

    async def decorator(self, *args, **kwargs):
        # Validate model and update current instance with validated fields
        validated_instance = self.validate(self.dict())
        self.__dict__.update(validated_instance)

        result = await func(self, *args, **kwargs)
        return result

    return decorator
