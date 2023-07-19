"""
This module holds the `RelationshipProperty` class which can be used to make relationship related methods available
on a `NodeModel` models field.
"""
from typing import Type

from neo4j_ogm.core.client import Neo4jClient
from neo4j_ogm.core.node import NodeModel
from neo4j_ogm.core.relationship import RelationshipDirection
from neo4j_ogm.exceptions import UnregisteredModel


class RelationshipProperty:
    """
    Class used to define relationships between the model this class is used on and a target node, which defines the
    other end of the relationship.
    """

    _client: Neo4jClient
    _source_model: Type[NodeModel]
    _target_model: Type[NodeModel]
    _direction: RelationshipDirection

    def __init__(self, target_model: Type[NodeModel] | str, direction: RelationshipDirection) -> None:
        """
        Verifies that the defined target model has been registered with the client. If not, a `UnregisteredModel`
        will be raised.

        Args:
            target_model (Type[NodeModel] | str): The model which is the target of the relationship. Can be a
                model class or a string which matches the name of the model class.
        """
        self._client = Neo4jClient()

        # Check if target model has been registered with client
        target_model_name = target_model if isinstance(target_model, str) else target_model.__name__

        registered_target_model = [model for model in self._client.models if model.__name__ == target_model_name]
        if len(registered_target_model) == 0:
            raise UnregisteredModel(unregistered_model=target_model_name)

        self._target_model = registered_target_model
        self._direction = direction

    def _build_property(self, source_model: Type[NodeModel])
