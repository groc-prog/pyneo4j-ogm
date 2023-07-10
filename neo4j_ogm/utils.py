"""
This module hold helper functions and utilities.
"""
from typing import Callable

from neo4j_ogm.exceptions import InstanceDestroyed, InstanceNotHydrated


def ensure_alive(func: Callable):
    """
    Decorator which ensures that a instance has not been destroyed and has been hydrated before running any queries.

    Raises:
        InstanceDestroyed: Raised if the method is called on a instance which has been destroyed
        InstanceNotHydrated: Raised if the method is called on a instance which has been saved to the database
    """

    async def decorator(self, *args, **kwargs):
        if getattr(self, "_destroyed", True):
            raise InstanceDestroyed()

        if getattr(self, "_element_id", None) is None:
            raise InstanceNotHydrated()

        result = await func(self, *args, **kwargs)
        return result

    return decorator
