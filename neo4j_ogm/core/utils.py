"""
This module hold helper functions and utilities.
"""
from enum import Enum
from typing import Callable

from neo4j.graph import Node

from neo4j_ogm.core.exceptions import InstanceDestroyed, InstanceNotHydrated, UnknownRelationshipDirection


class RelationshipDirection(str, Enum):
    """
    Definition for all possible relationship directions.
    """

    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"
    BOTH = "BOTH"


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


def validate_instance(func: Callable):
    """
    Decorator which validates the model fields before calling the method.

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


def build_relationship_match_clause(
    direction: RelationshipDirection,
    start_node: Node,
    end_node: Node,
    relationship_type: str,
    start_ref: str = "start",
    end_ref: str = "end",
    rel_ref: str = "rel",
) -> str:
    """
    Build a relationship MATCH query depending on the provided relationship direction.

    Args:
        start_ref (str, optional): Variable to use for the start node in the MATCH clause. Defaults to "start".
        end_ref (str, optional): Variable to use for the end node in the MATCH clause. Defaults to "end".
        rel_ref (str, optional): Variable to use for the relationship in the MATCH clause. Defaults to "rel".

    Raises:
        UnknownRelationshipDirection: Raised if a invalid relationship direction was provided.

    Returns:
        str: The created MATCH clause
    """
    start_match = f"({start_ref}:{':'.join(start_node.labels)})"
    end_match = f"({end_ref}:{':'.join(end_node.labels)})"
    rel_match = f"[{rel_ref}:{relationship_type}]"

    match direction:
        case RelationshipDirection.INCOMING:
            return f"MATCH {start_match}, {end_match}, {start_match}<-{rel_match}-{end_match}"
        case RelationshipDirection.OUTGOING:
            return f"MATCH {start_match}, {end_match}, {start_match}-{rel_match}->{end_match}"
        case RelationshipDirection.BOTH:
            return f"MATCH {start_match}, {end_match}, {start_match}-{rel_match}-{end_match}"
        case _:
            raise UnknownRelationshipDirection(
                expected_directions=[direction.value for direction in RelationshipDirection],
                actual_direction=direction,
            )
