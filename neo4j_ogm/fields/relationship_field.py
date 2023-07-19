"""
This module holds the `RelationshipProperty` class which can be used to make relationship related methods available
on a `NodeSchema` models field.
"""
from typing import Type

from neo4j_ogm.core.node import NodeSchema
from neo4j_ogm.core.relationship import RelationshipDirection


class RelationshipProperty:
    """
    Class used to define relationships between the model this class is used on and a target node, which defines the
    other end of the relationship.
    """

    _source_model: Type[NodeSchema]
    _target_model: Type[NodeSchema]
    _direction: RelationshipDirection
