"""
Enums shared between multiple modules.
"""
from enum import Enum


class RelationshipPropertyDirection(str, Enum):
    """
    Available relationship directions for relationship properties.
    """

    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"


class RelationshipPropertyCardinality(str, Enum):
    """
    Available cardinality types.
    """

    ZERO_OR_ONE = "ZERO_OR_ONE"
    ZERO_OR_MORE = "ZERO_OR_MORE"
